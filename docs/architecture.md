# 共用顯示核心架構

Revision: 2 — 2026-10-16

## 資料流

```text
應用取得並驗證任務／模型／用量資料
                  ↓
telegram_ui：ReplyView／UsageView／render_progress
                  ↓
Markdown文字與reply_markup字典
                  ↓
應用的Telegram client傳送／編輯、確認送達
```

## 目前公開介面

- `ContextUsage(used_tokens, window_tokens)`：已驗證的Context占用，不接受任務累積token冒充。
- `QuotaWindow(remaining_percent, resets_at=None, used_percent=None)`：0..100百分比；可保留 provider 的獨立 used 值，省略才以 100−remaining 計算。reset 若存在必須帶時區。
- `UsageView(context=None, five_hour=None, weekly=None, cached=False, quota_rows=None)`：未知使用 None；quota_rows=None 保留舊 5h/Weekly，空 tuple 不輸出 quota 列，自訂 QuotaRow 可增加週期，不能與非空舊 quota 欄位混用。
- `ReplyView(agent, model, body, usage=None, identity=None)` 與 `render_reply(view, *, profile=DisplayProfile())`：身份／模型、正文與可選 Usage。ReplyIdentity 提供 display_name／effort／account／speed；DisplayProfile 控制圖示、欄位順序、帳號顯示及數值格式。標籤單行並 escape，正文原樣保留。見 [設定契約](display-profiles.md)。
- `render_usage(view, *, profile=DisplayProfile())`：預設四列，每列獨立引用段落；自訂 quota_rows 可調整列數。用 `\n>\n` 隔開，不顯示查詢時間。
- `render_progress(state, elapsed_seconds, task_id, activity=None, flow=...)`：關鍵字參數；回傳ProgressView.text與.reply_markup。合法state為running、waiting、completed、cancelled、failed；後三者移除中斷按鈕。
- `split_text(text, limit=4096)`與`utf16_length(text)`：只處理純文字分段，不保證Markdown跨段語法完整。
- `telegram_ui.service_lifecycle.ServiceLifecycleView` 與 `render_service_lifecycle(view)`：驗證後的服務就緒通知，與任務進度分開；原因未知明示，啟動時間須帶時區。沒有偵測、投遞或模型載入行為，見 [通知契約](service-lifecycle.md)。

版本與精確簽章以[src/telegram_ui/rendering.py](../src/telegram_ui/rendering.py)、[exports](../src/telegram_ui/__init__.py)為準。

## 中斷操作界線

按鈕callback為`task:cancel:<task_id>`；task_id限制1..48個ASCII字母／數字／底線／連字號，整體小於Telegram64-byte上限。這只是顯示契約，不是授權憑證。

應用必須檢查按鈕來自允許的使用者、正確chat/topic、原status message與仍在執行的task，才執行取消。終態／過期按鈕不能取消新的任務。核心不儲存chat/user ID、不建立timer、不呼叫kill、不推進任何task state。

## 進度與排版語義

elapsed由應用使用單調時鐘計算後傳入，核心不能從零開始假裝真實已執行時間。預設流程是分析→修改→測試→完成的checklist，不是百分比或真實階段探測；不適用時flow=None或提供自己的tuple。

正文前後的NBSP獨立段落保留可見留白。Usage的分段方式避免依賴Markdown soft line break；套件測試驗證輸出結構，真實Telegram解析／不同客戶端顯示仍須整合驗證。

來源：[Telegram鍵盤callback](https://core.telegram.org/bots/api#inlinekeyboardbutton)、[Rich訊息](https://core.telegram.org/bots/api#sendrichmessage)、[目前原始碼](../src/telegram_ui/rendering.py)。
