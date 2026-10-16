# 身份與顯示設定

Revision: 1 — 2026-10-16

## 通用需求與邊界

完整回覆需保留 agent、模型、reasoning effort、帳號別名及速度標籤，並依 agent 選圖示。不同應用只調整顯示資料與 profile，不在核心依專案名稱分支。設定只影響畫面，不能啟用 fast、切換帳號或模型。

舊 `ReplyView(agent, model, body, usage)` 與無 profile 的輸出保持相容。新增可選 `identity`，提供 effort/account/speed/display_name；agent 與 model 仍以 ReplyView 為唯一來源，避免重複資料矛盾。缺少身份欄位省略，不從正文猜測。

`DisplayProfile` 控制圖示、身份欄位順序、帳號 replace/append/hide、哪些 agent 隱藏 effort、quota 小數位與時區偏移顯示。設定為不可變資料；`from_dict()` 接受已解析 JSON 的 mapping，拒絕未知鍵與錯誤型別。核心不讀設定檔、不管理優先序；應用在任務開始前解析設定並保留本次 snapshot。

Quota 可提供獨立 used 百分比，未提供時維持舊有 100−remaining 行為。`UsageView.quota_rows=None` 保留 5h/Weekly；空 tuple 表示不適用、不輸出 quota 列；自訂 `QuotaRow(label, window)` tuple 可加入 daily/monthly，window=None 明示 unavailable。禁止同時指定自訂列與非空舊欄位，避免靜默丟資料。Usage 每列維持獨立引用段落。

## 接入範例

```python
from telegram_ui import DisplayProfile, ReplyIdentity, ReplyView, render_reply

# 應用可將 json.load() 結果交給 from_dict；此處全為合成資料。
profile = DisplayProfile.from_dict({
    "icons": {"writer": "🧠", "builder": "🛠️"},
    "fallback_icon": "🤖",
    "account_mode": "replace",
    "fields": ["model", "effort", "speed"],
    "hide_effort_for": ["builder"],
    "quota_precision": 2,
})
view = ReplyView("writer", "example-model", "Result", identity=ReplyIdentity(
    display_name="WRITER", effort="high", account="personal", speed="fast",
))
text = render_reply(view, profile=profile)
# 🧠 **[personal]** · example\-model · high · fast
```

`account_mode=append` 需在 fields 中包含 account（預設包含）；replace 將別名取代標頭名稱，hide 完全隱藏帳號。別名等於 agent id 時，應用可傳 None 保留顯示名稱。圖示對應使用精確 agent id，不自動大小寫轉換。其他應用可省略 identity 或使用較少 fields。擴充欄位先新增明確型別，不提供可執行模板。

## 驗收

離線：既有呼叫輸出不變、完整身份可呈現、設定隔離、無效設定拒絕、缺值不造假、正文與附件標記原樣保留。安裝 wheel 後從 checkout 外執行同樣的消費流程。

應用端手動：輸入一般任務及 fast 任務，標頭應符合該任務已核實的模型／effort／帳號／速度；切換較簡 profile 後，只影響指定 scope 的新任務。缺欄位、跨 scope 汙染或畫面與實際執行不符均為失敗。另確認每列 Usage 在 Telegram 分段。此套件離線測試不代表實際 Telegram 或三個應用已接入。

來源：`src/telegram_ui/rendering.py`、`tests/test_profiles.py`。
