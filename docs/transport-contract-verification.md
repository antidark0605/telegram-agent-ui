# 文件傳送契約驗證

Revision: 1 — 2026-10-16

整理：Codex（gpt-6-astra）。

## 已完成範圍

獨立 distribution `telegram-agent-transport` 放於 `packages/telegram-agent-transport/`。
包含 Destination、Document、Receipt，同步及 async provider 呼叫；UI runtime 不引用傳輸套件。
這是 provider 契約與呼叫層，不是已接入的 HTTP client，也不包含 inbound download。

來源：`packages/telegram-agent-transport/pyproject.toml`、
`packages/telegram-agent-transport/src/telegram_transport/documents.py`。

## 驗證結果

- 8 項合成單元測試通過：三種文件 bytes、topic、caption、大小邊界、非法檔名、收據、timeout 與 async 取消。
- compile 通過；0.1.0 wheel 建置成功，checkout 外安裝、metadata/import 與送達收據 consumer 通過。
- 同 repo UI 24 項測試、compile、wheel、checkout 外安裝消費驗證通過。
- CI 新增獨立套件檢查；本機只驗證目前 Python，未宣稱 GitHub CI 多版本已執行。

來源：`packages/telegram-agent-transport/tests/test_documents.py`、`.github/workflows/python-tests.yml`。

## 程式走讀與邊界

1. 先檢查 metadata，再呼叫 provider；超限不進入 sender。
2. 只在 topic 不為 None 時傳遞原值，不移除 topic 後重送。
3. 同步與 async 都只呼叫一次；例外原樣傳遞。收到錯誤不表示未送達。
4. 呼叫端提供 stream 並管理開啟／關閉；套件不讀取、重開或刪除路徑。
5. size_bytes 是呼叫端契約，不能代替真實 bytes 或授權驗證；應用須完成不可變 staging。
6. Receipt 必須對應原 destination；收據驗證失敗也不重送。

來源：`packages/telegram-agent-transport/src/telegram_transport/documents.py`。

## 尚未完成與驗收方式

尚未接入消費應用、未上傳套件平台、未呼叫真實 Telegram。HTTP multipart／SDK adapter、
收檔、安全 staging、queue 重試及持久化仍由各應用負責，不能把本套件測試稱為三平台整合完成。

應用接入後以 HTML／MD／TXT 各傳一個已知檔案，下載並比對 SHA256；須檔名、bytes、
chat/topic 全部一致。測試超限時不發 API，模擬 timeout 時不得自動移除 topic 重送。
詳見套件 README 的消費範例與契約。

來源：[套件 README](../packages/telegram-agent-transport/README.md)、
[Telegram sendDocument](https://core.telegram.org/bots/api#senddocument)。
