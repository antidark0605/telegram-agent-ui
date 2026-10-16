# 顯示核心完善與驗證

Revision: 1 — 2026-10-15

## 範圍與修正

依 [整合計畫第一階段](integration-plan.md#第一階段固定顯示契約) 完善現有核心；本次不包含消費應用接入或發布。

原本 `_label` 只攔截 ASCII 控制字元。以 U+0085、U+2028、U+2029 放入身份標籤，可重現跨行內容通過驗證。現在這三種換行字元也會引發 `ValueError`，共用驗證涵蓋 agent、model、活動與流程標籤，維持既有公開簽章。

來源：[標籤驗證與呼叫端](../src/telegram_ui/rendering.py)、[回歸測試](../tests/test_rendering.py) 的 `test_unicode_line_separators_rejected_in_all_labels`。

## 走讀、邊界與副作用

- 驗證仍先檢查字串、非空白與 300 字元上限，再檢查控制／換行字元，最後 escape；增加的判斷只擴充非法標籤字元集合。
- 合法多語、emoji 與恰好 300 字元標籤仍可用；空白、空標籤與 301 字元被拒絕。
- 正文不經 `_label`；空正文、長正文與含 Unicode 換行的正文仍逐字保留。
- Context 的零占用與滿額、quota 的零與百分之百、未知用量分別呈現；非 UTC reset 保留原時間及 offset。
- 每次產生的按鈕資料互相獨立；既有終態清除按鈕、正文媒體標記與 UTF-16 分段測試仍通過。

以上均由 [測試](../tests/test_rendering.py) 驗證；核心無新增外部 I/O，改動限於 `_label` 判斷式。

## 本次執行結果

- Python 3.10：24 項單元測試 PASS，包含原有 300 組固定亂數分段。
- `python3 -m compileall -q src tests`、`git diff --check` PASS。
- `python3 -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .` PASS。
- wheel 安裝到專案外臨時目錄，切換 cwd 後確認 import 來源位於安裝目錄、metadata 與套件版本均為 0.1.0；對已安裝套件執行完整 24 項測試，全部 PASS。
- 臨時安裝使用 Python `TemporaryDirectory` 清理。其他 Python 版本的 CI 本輪未執行。

可重現步驟見 [開發與驗證](development-guide.md)；測試定義見 [合成測試](../tests/test_rendering.py)。

## 後續整合手動驗收

尚未驗證真實 Telegram 解析、client 畫面及消費應用中斷授權。套件測試不能判定這三項通過。

1. 在整合應用送出短任務；執行中應顯示進度、經過秒數與中斷按鈕，終態應移除按鈕。
2. 使用合法操作者中斷目前任務，僅該任務停止；其他操作者、錯誤 topic、舊訊息或過期 task 不得中斷新任務。
3. 顯示含 Usage 的回覆，確認正文留白與四列引用段落各自保留；缺行、折疊或正文被改寫即失敗。
4. 將 `agent` 設為含 U+2028 的合成標籤，應於送出前得到 `ValueError`；將同一字元放在正文，`render_reply` 應原樣保留。

來源：[README Integration contract](../README.md#integration-contract)、[整合通過條件](integration-plan.md#接入通過條件)。
