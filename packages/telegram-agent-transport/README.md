# telegram-agent-transport

Revision: 1 — 2026-10-16

獨立 Python >=3.10 distribution；runtime 只需標準庫，與 `telegram-agent-ui` 無互相依賴。
0.1.0 是文件傳送介面的本地來源候選，尚未發佈或接入任何實際 bot。

## 契約

- `Destination(chat_id, message_thread_id=None)` 保留私聊及群組 topic。
- `Document(filename, stream, size_bytes, caption=None)` 接收應用已授權且固定的 binary stream；HTML、MD、TXT 都走文件，不轉成圖片或訊息正文。
- `send_document(sender, destination, document, max_bytes=50_000_000)` 與 async 版本只呼叫 provider 一次，回傳 `Receipt(destination, message_id)`。
- provider 收到 `chat_id`, `document`（stream）, `filename`，以及存在時的 `message_thread_id`, `caption`。它須完成傳送後回傳 Receipt；這是自訂 provider contract，不是宣稱任一 SDK 可直接回傳 Receipt。
- `filename` 是 SDK adapter 參數；HTTP adapter 必須把它放在 multipart 的檔名，不可當作 Bot API JSON 欄位。Bot API 檔案欄位為 `document`。
- 不自動重送、不刪 topic、不解析 caption、不選 token、不讀路徑、不擷取遠端 URL、不下載或刪檔。
- metadata 尺寸檢查不是檔案安全檢查。應用必須負責授權、允許路徑、不可變 staging、實際 byte count、stream 從開頭讀取、傳送期間保持開啟，以及錯誤後關閉／清理；不可把未驗證的 agent 路徑直接交給 provider。
- 預設 50,000,000 bytes 是此套件保守政策，可由應用調小。Caption 保守限制為 1024 UTF-16 units。大小在呼叫 provider 前驗證。
- timeout、取消與 receipt 驗證失敗都不能證明未送達；套件不據此重送，應用須另定不確定送達處理政策。

## 消費範例

```python
from telegram_transport import Destination, Document, Receipt, send_document_async

async def deliver(bot, authorized_path, destination):
    async def provider(**kwargs):
        message = await bot.send_document(**kwargs)
        # Verify actual chat/topic against destination in the application adapter.
        if str(message.chat.id) != str(destination.chat_id):
            raise ValueError('unexpected recipient')
        if message.message_thread_id != destination.message_thread_id:
            raise ValueError('unexpected topic')
        return Receipt(destination, message.message_id)

    with authorized_path.open('rb') as stream:
        import os
        document = Document(authorized_path.name, stream, os.fstat(stream.fileno()).st_size)
        return await send_document_async(provider, destination, document)
```

此範例要求應用預先完成路徑授權及 immutable staging；不代表已完成安全整合。
同步 stdlib client 可包成同一 provider contract；HTTP multipart、錯誤分類與 queue 收據由應用 adapter 維持。

## 驗證

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
python3 -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

合成 provider 驗證 bytes、檔名、caption、topic、超限不呼叫、錯誤不重送、async 取消及 stream lifetime。
另須在 checkout 外安裝 wheel 驗證 import；真實 Telegram API／手機下載與各應用整合尚未驗證。
正式接入後，逐一傳送已知 bytes 的 HTML／MD／TXT，下載後比對 SHA256，確認私聊 topic 不串線。

來源：[Telegram sendDocument](https://core.telegram.org/bots/api#senddocument)、[Python Binary I/O](https://docs.python.org/3/library/io.html#binary-i-o)。
