# 開發與驗證

Revision: 1 — 2026-10-15

## 工作目錄

在本 checkout 根目錄工作，`git remote get-url origin` 應為公開的 `antidark0605/telegram-agent-ui`。程式位於 `src/telegram_ui/`，測試位於 `tests/`；不是在父目錄或其他應用內開發。

```sh
git status --short
git remote get-url origin
python3 --version
```

要求Python>=3.10。已有未提交變更時先讀diff，不自動pull/reset；只有乾淨且沒有不同意保留的工作時才依任務更新來源。

## 原始碼測試

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
git diff --check
```

初始0.1.0來源有17項測試，其中一項涵蓋300組固定亂數Unicode／換行分段。新增或修改功能時以實際輸出為準，不把此數量當永久要求。

## 建置與安裝消費驗證

建議在獨立virtual environment內準備建置工具，不改全域Python：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'setuptools>=61' wheel
.venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

在專案外臨時目錄安裝wheel，離開checkout驗證，避免誤用src而掩蓋封裝缺檔。以下只安裝到臨時目錄，結束後清除：

```sh
ui_checkout="$PWD"
ui_probe_dir="$(mktemp -d)"
trap 'rm -rf "$ui_probe_dir"' EXIT
.venv/bin/python -m pip install --no-deps --target "$ui_probe_dir/site" "$ui_checkout"/dist/telegram_agent_ui-*.whl
cd "$ui_probe_dir"
PYTHONPATH="$ui_probe_dir/site" "$ui_checkout/.venv/bin/python" - <<'PY'
from importlib.metadata import version
from telegram_ui import UsageView, render_usage, render_progress
assert version('telegram-agent-ui')
assert len(render_usage(UsageView()).split('\n>\n')) == 4
view = render_progress(state='completed', elapsed_seconds=1, task_id='synthetic')
assert view.reply_markup == {'inline_keyboard': []}
print('Installed consumer PASS')
PY
cd "$ui_checkout"
```

dist含多版wheel時只選本次精確檔名，不一次安裝多版。建置出的metadata必須是telegram-agent-ui與預期版本；UNKNOWN或只在src能import都算失敗。

## Review重點

- state、非負秒數、callback長度與終態按鈕清除。
- Context必須是已核實占用量；quota為有限的0..100百分比，reset帶時區。
- Usage四列獨立段落，未知顯示unavailable，正文及媒體標記不被改寫。
- Plain-text分段保留換行與Unicode字元；不宣稱可任意分割Markdown。
- 不引入網路／程序／憑證存取，不改其他應用。
- 公開diff和Git metadata不含任何私人環境資訊。

來源：[套件README](../README.md)、[程式](../src/telegram_ui/rendering.py)、[測試](../tests/test_rendering.py)、[Python官方封裝指南](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。
