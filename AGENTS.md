# telegram-agent-ui 開發指引

Revision: 2 — 2026-10-15

## 專案目的與入口

- 本工作目錄是 `antidark0605/telegram-agent-ui` 的開發 checkout；公開儲存庫：https://github.com/antidark0605/telegram-agent-ui 。
- 開發 Python 共用顯示套件：distribution 為 `telegram-agent-ui`，import 為 `telegram_ui`。先讀 README.md，再依序讀 docs/development-guide.md、docs/architecture.md、docs/integration-plan.md、docs/handoff.md。
- 預設使用繁體中文報告；程式名稱與命令保留英文。新文件用 kebab-case，內文標明 revision／日期；AGENTS.md、README.md 是檔名例外。

## 公開資訊界線

- 只加入通用程式、通用文件與合成測試。禁止加入私有專案名稱或內容、公司名稱／email、內網主機／路徑、裝置與真實使用者／聊天識別碼、憑證、Token、連線設定、原始對話或執行紀錄。
- 不從其他私有專案直接複製程式或歷史。需要參照時，先把需求整理成不含私有資訊的規格，再實作共用邏輯。
- 提交與發布前檢查 staged diff、Git metadata、文件連結及建置檔。範例只用 synthetic 值，不把私人證據放進此 checkout。

## 程式邊界

- Python >=3.10，runtime 只依賴標準庫。建置工具由 pyproject.toml 管理。
- 核心只接收資料並產生 Markdown／button markup；不讀憑證、不開連線、不啟動或停止 Agent、不修改應用狀態。
- 以任務進度、經過時間與中斷按鈕為主要互動；終態清除按鈕。流程列是 checklist，不代表核心已觀察到實際執行階段。
- Usage 每一列用獨立引用段落，保留正文前後空白；不加入 Selected model 或 Quota checked。未知 Context／quota 顯示 unavailable，不把未知當0，不由模型文字猜數值或模型身份。
- 真正取消操作由消費應用核對 caller、chat/topic、status message、active task，再呼叫自己的取消方法。顯示按鈕不等於已中斷任務。
- 平台啟動、模型來源、投遞、重試、會話、權限與附件安全保留在應用；不得為共用UI順手改服務、連網或操作其他專案。

## 工作與驗證

- 修改前完整讀相關檔案；從原始碼／官方文件確認格式、單位與副作用，不猜命令選項。
- 優先最小變更；不擅自改既有公開函式契約。修改必須自驗，涵蓋邊界、未知值與副作用。
- 執行 docs/development-guide.md 的單元測試、compile、wheel建置，以及離開原始碼目錄後的安裝消費驗證。
- 只有離線測試時明確標示：未驗證真實Telegram解析、client畫面及應用的中斷授權；不能把套件測試當三個應用整合完成。
- 不執行本機Agent CLI或重啟任何現有Bot服務來測此套件；純合成測試足以驗證核心。

## Git與來源署名

- 不覆蓋其他人的未提交變更，不自動reset／force push。Git Author／Committer使用已核實的人類owner identity；公開提交不使用公司或私人email，可用owner的GitHub noreply地址。
- Conventional Commit格式：`<type>(<scope>): <summary>`。
- Agent實質參與時，message最後加 `Assisted-by: Codex (<verified-runtime-model>)`，或實際agent名稱。每次commit前查目前session本輪runtime紀錄，不沿用其他session或設定值，不輸出prompt／session UUID／effort到公開commit。
- 無法核實model時用 `Assisted-by: Codex` 並在私人交接說明，不能猜測；agent身份亦無法核實則停止commit。
- 多行message用真正換行的檔案或heredoc，不傳literal `\n`；不為補署名改寫已推送歷史。
- 推送、發布及接入應用依使用者當次授權範圍；維護文件不能被當成已批准三平台部署。
