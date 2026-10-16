# 0.2.0 開發交接

Revision: 3 — 2026-10-16

## 來源與範圍

公開儲存庫：antidark0605/telegram-agent-ui。distribution 為 telegram-agent-ui，import 為 telegram_ui，Python >=3.10，runtime 只使用標準庫。

本次 0.2.0 在已提交的 lifecycle renderer 基礎上整合 profiles、身份欄位與可擴充 Usage。未發布套件平台；固定完整審核 commit 或 wheel SHA-256 安裝，不能只用版本字串判斷來源。dist 中既有同名舊 wheel 已由本輪完整建置取代；對應 hash 以本輪產物交付為準。

本輪由 owner 完成 review／建置／驗證後，由具 Git index 寫入權限的協作者依精確清單完成正常提交。最終來源請使用此文件所在完整 commit；wheel 與來源已逐檔比對。原有 AGENTS 與歷史驗證文件不納入此功能提交。

## API 與相容性

- ReplyIdentity：display_name、effort、account、speed；ReplyView 仍是 agent/model 的唯一來源。DisplayProfile.from_dict 接受已解析設定，拒絕未知鍵與錯誤型別，建立不可變 snapshot。
- QuotaWindow 新增可選 used_percent；UsageView 新增可選 quota_rows。省略新參數時保留舊 positional constructor 與預設輸出；未知值明示 unavailable，不適用 quota 用空 tuple。數值與時區先驗證。
- render_reply/render_usage 接受 keyword-only profile。正文與附件標記保留，Usage 每列獨立引用段落。標籤拒絕 Unicode 換行。
- ServiceLifecycleView／render_service_lifecycle 由 telegram_ui.service_lifecycle 匯入；完整 0.2.0 wheel 已包含。通知只呈現 verified ready/restarted/recovered、帶時區啟動時間及可選公開版本；原因未知明示，不能當作模型已載入。
- render_progress 及 task:cancel callback 契約保留；取消授權、實際執行、傳輸、重試與附件安全均在應用。

來源：[profiles](display-profiles.md)、[lifecycle](service-lifecycle.md)、[架構](architecture.md)。

## 驗證與邊界

本輪完整來源 45 項單元測試、compileall、diff check 通過；最終 0.2.0 wheel 安裝至 checkout 外後，以安裝套件重跑相同 45 項測試並核對 module 來源與版本。建置成品的 package Python 檔案逐一與來源比對，metadata 不含 runtime 第三方依賴；公開變更與建置檔檢查不含私有部署資料。先前 35 項 profiles 及 27 項隔離 lifecycle 結果屬歷史記錄，不取代這次完整驗證。

本輪只驗 UI 套件，沒有操作消費應用、Bot、服務或真實 Telegram。應用部署、通知觸發／收件範圍／去重、真實客戶端排版及取消授權均須由接入端驗證；不以套件測試宣稱已完成整合。

## 接入檢查

1. 使用固定 commit/wheel；先核對版本、hash、匯入位置與兩組新增 API。
2. 將已核實模型／effort／帳號／fast 資料轉成 view，依 scope 保存任務 profile snapshot；避免在有舊投遞收據的任務中途改 renderer。
3. 在 Rich/classic/raw 檢查身份、Usage、留白與長文。raw 會看到 Markdown 和跳脫字元；套件不選傳輸模式。
4. 依 README 驗證進度與取消權限；依 lifecycle 文件驗證啟動事件、未知原因、已授權且曾使用的目的地及同 instance 去重。

來源：[開發驗證](development-guide.md)、[整合計畫](integration-plan.md)。
