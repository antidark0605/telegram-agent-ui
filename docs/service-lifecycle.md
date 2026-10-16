# 服務啟動通知

Revision: 1 — 2026-10-16

## API 與責任

```python
from datetime import datetime, timezone
from telegram_ui.service_lifecycle import ServiceLifecycleView, render_service_lifecycle

view = ServiceLifecycleView(
    agent_label="Example Gateway",
    state="ready",
    started_at=datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    release="v1.2.3",  # 可省略
    reason=None,
)
markdown = render_service_lifecycle(view)
```

新增 frozen dataclass 與純 Markdown renderer；只使用標準庫與既有 label helper。使用 submodule import，沒有修改頂層 exports、版本、reply／usage／progress。此變更可獨立安裝在既有 0.1.0 基準，無須其他尚未提交的 profile 修改。

`agent_label` 必須由應用核實，代表這次啟動的服務；多 agent 服務使用一個服務名稱。`state` 僅接受 ready／restarted／recovered，三者都表示服務已就緒，不代表模型載入、native task 重啟或任務恢復成功。

`started_at` 是已核實的服務 instance 啟動時間，必須是 timezone-aware datetime；輸出 ISO 8601，保留原時區偏移，精確至秒。不是通知寄出時間，renderer 不讀時鐘。

`reason=None` 顯示「原因未確認」。只有應用取得外部證據後才可傳 external_restart（外部重啟服務）或 host_reboot（主機重開）；renderer 不從 state、時間、版本或文字猜原因。其他值直接拒絕，避免自由格式原因洩漏內部資訊。

`agent_label`、可選 `release` 限非空單行且至多 300 字元，拒絕控制字元與 Unicode 換行符並跳脫 Markdown。只傳公開安全的服務別名與版本，不傳 path、PID、主機識別碼、token 或原始錯誤；文字驗證不是敏感資訊辨識器。API 沒有這些內部欄位。

## 消費應用契約

- 實際 ready 後觸發；事件與 reason 的證據由應用取得，套件不讀 systemd、檔案、程序或網路。
- 僅通知已授權且實際使用過的 chat/topic，保留 private topic；不能遍歷所有 allowlist 群發。
- 每啟動 instance 對每個目的 chat/topic 至多建立一份邏輯通知；多 agent 同 topic 不逐 agent 重複。去重、退避與投遞失敗處理由應用負責，失敗不阻止服務啟動；這不是 exactly-once 網路投遞保證。
- 使用既有訊息／格式傳輸。輸出是 Markdown，raw 會顯示 Markdown 與跳脫字元，套件不擅自選擇傳輸格式。此通知不需要 task 中斷按鈕。

## 驗證與接入狀態

專用合成測試覆蓋三狀態、未知與已核實原因、跳脫、單行／長度、錯誤型別、時區、不可變及重複渲染。既有回覆／Usage／進度測試用於回歸檢查。需另做 compile、wheel 建置與 checkout 外安裝消費驗證。

本變更尚未接入任何 gateway，未發送真實 Telegram，也未部署。離線驗證不代表通知去重、收件授權、restart/reboot 偵測或手機排版已通過。

本輪離線結果（2026-10-16）：目前工作樹 45 項測試全部通過，compileall 與 diff check 通過。另從 HEAD 匯出乾淨基準，只加入本文件、module 與專用測試，建置 wheel 並安裝到 checkout 外獨立目錄；以安裝套件執行 17 項基準測試與 10 項新測試，27 項全部通過，並核對 import 確實來自安裝目錄。此隔離 wheel 沿用基準 metadata 0.1.0，僅作驗證產物，不是新發布版本；接入應固定審核後的完整 commit，不能單憑 0.1.0 版本字串識別本功能。

走讀：state/reason 先檢查字串型別再查固定映射，未知值不被當成 ready；時間只接受帶時區 datetime；所有動態 label 先驗證再跳脫。缺 release 省略，缺 reason 明示未知；renderer 不讀目前時間，也沒有跨呼叫狀態。既有程式檔未修改，隔離基準測試同時檢查原回覆／進度／Usage 行為。

接入後手動驗收：以外部已核實重啟或主機重開觸發服務啟動；每個已使用且授權的 topic 應各有一則服務 ready 通知，時間／版本／原因符合證據，未使用或未授權 topic 不收到。多 agent topic 不重複；native task 重啟不觸發。投遞失敗時服務仍就緒且由既有退避策略處理。未知原因只顯示「原因未確認」。

來源：`src/telegram_ui/service_lifecycle.py`、`tests/test_service_lifecycle.py`；既有純顯示邊界見 README「Integration contract」。
