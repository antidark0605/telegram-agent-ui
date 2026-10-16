# 0.2.0 顯示設定驗證

Revision: 2 — 2026-10-16

本文件記錄早期 profiles 階段，下面的 35 項結果與 SHA-256 為歷史產物；最終包含 lifecycle 的完整 0.2.0 驗證見 [目前交接](handoff.md)。不得使用下列舊 hash 部署最終版本。

## 完成範圍

本地來源與 wheel 已完成；未推送、未發布套件平台、未接入或重啟消費應用。

## 程式碼走讀

- `rendering.py:69`：身份資料逐欄驗證單行文字；agent/model 仍在 ReplyView，避免兩份來源衝突。
- `rendering.py:82`：profile 使用 frozen dataclass 與 tuple；from_dict 複製 mapping/list，不保留可變設定參照。未知鍵與無效欄位順序直接拒絕。
- `rendering.py:222`：先選顯示名稱與圖示，再依 profile 選擇欄位，最後接回未修改的正文。沒有查詢或修改執行設定。
- `rendering.py:190`：獨立 used 值以 None 判斷，0 不被當缺值；未提供才用舊公式。自訂 quota 與舊欄位互斥，避免資訊被靜默覆蓋。

## 邊界與副作用

- 缺身份資料：省略欄位；未知 agent：使用 profile fallback，均不從正文猜值。
- 帳號三種顯示模式與欄位順序：測試精確比對標頭；特定 agent 可隱藏 effort。
- 設定原物件遭修改：已建立 profile 不變；另一 profile 與預設 renderer 不受影響。
- NaN、無限值、布林百分比、超界數字、無時區 reset：拒絕；未知 quota 顯示 unavailable，不適用用空 tuple。
- 舊 positional constructors、預設回覆、Usage 分段、空白與媒體標記、中斷按鈕、Unicode 分段：原測試通過。未修改傳輸、網路、權限或其他應用。

來源：`tests/test_profiles.py`、`tests/test_rendering.py`。

## 本輪執行結果

- 原始碼 unittest：35 項全部 PASS。
- compileall src/tests：PASS。
- git diff --check：PASS。
- wheel：`telegram_agent_ui-0.2.0-py3-none-any.whl` 建置成功。
- 將該 wheel 安裝至獨立臨時目錄，離開 checkout 後執行相同 35 項測試：全部 PASS；import 路徑確認來自安裝目錄，distribution 與 module 版本均為 0.2.0。
- SHA-256：`445a8402065f59711017f435ca11d099ffb8411121c92f5ba8e6fba737fdc85d`。

以上是本機離線結果，不宣稱本輪執行多版本 CI。真實 Telegram 解析、客戶端畫面、消費應用 scope 與中斷授權均未驗證。

## 應用接入後手動驗證

1. 提交一般任務及 fast 任務；核對 agent 圖示、模型、effort、帳號別名及 fast 是否符合實際任務資料。
2. 套用精簡 profile；只應隱藏指定欄位，不應改變執行模型或其他 scope 的顯示。
3. 提交有 Usage 與附件標記的回覆；確認 Usage 各列獨立、正文及附件流程正常。

任何欄位遺失、任務資料不符、跨 scope 汙染、Usage 折行錯誤均判為未通過。接入範例見 `display-profiles.md`。
