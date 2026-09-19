# WordToHtml 使用手冊

WordToHtml 會讀取 `source_word` 資料夾內的 Word 文件，將 `.docx` 轉成可瀏覽、可搜尋的 HTML 網站，輸出到 `out_html`。

本工具也支援舊版 Word `.doc` 檔。執行完整轉換時，系統會先把 `.doc` 另存為同資料夾、同檔名的 `.docx`，再進行 HTML 轉換。

## 系統需求

- Windows
- Python 3.10 或更新版本
- Microsoft Word，可用於將 `.doc` 轉成 `.docx`
- Pandoc 3.6 或更新版本

請先在 PowerShell 或命令提示字元確認：

```powershell
python --version
pandoc --version
```

第一次使用請安裝 Python 套件：

```powershell
pip install -r requirements.txt
```

## 資料夾用途

| 路徑 | 用途 |
| --- | --- |
| `source_word` | 放入要轉換的 `.doc` 或 `.docx` Word 文件。 |
| `out_html` | 轉換完成後產生 HTML 網站與搜尋索引。 |
| `convert_doc_to_docx.bat` | 只把 `.doc` 批次轉成 `.docx`。 |
| `run_convert.bat` | 先轉 `.doc` 為 `.docx`，再把 `.docx` 轉成 HTML。 |

## 完整轉換流程

1. 將 Word 文件放入 `source_word`。
2. 可同時放入 `.doc` 與 `.docx`。
3. 執行 `run_convert.bat`。
4. 等待畫面顯示完成訊息。
5. 開啟 `out_html\index.html` 瀏覽結果。

`run_convert.bat` 會先處理所有 `.doc` 檔：

- 若同名 `.docx` 尚未存在，會建立新的 `.docx`。
- 若同名 `.docx` 已存在，會略過，不覆蓋既有檔案。
- 原始 `.doc` 會保留，不會刪除。

接著系統會轉換 `source_word` 內所有 `.docx`，並產生：

- `out_html\index.html`
- `out_html\search-index.json`
- `out_html\pages\...\index.html`

## 只轉 `.doc` 成 `.docx`

如果只想先把舊格式升級成新格式，執行：

```text
convert_doc_to_docx.bat
```

或使用命令列：

```powershell
python .\convert_doc_to_docx.py
```

轉換結果會留在 `source_word`，檔名與原 `.doc` 相同，副檔名改為 `.docx`。

## 只重新產生 HTML

若已經確認 `source_word` 內都是 `.docx`，也可以直接執行：

```powershell
python .\convert_word_to_html.py
```

### 自訂首頁標題與副標

可在命令列輸入首頁標題與副標；未指定時會使用內建預設文字：

```powershell
python .\convert_word_to_html.py `
  --home-title "我的文件中心" `
  --home-subtitle "快速搜尋與閱讀文件"
```

執行 `run_convert.bat` 後，批次視窗會依序要求輸入首頁標題與副標；直接按 Enter 會使用預設文字：

```text
請輸入首頁標題 [Word 文件索引]: 我的文件中心
請輸入首頁副標 [快速搜尋與閱讀轉換完成的操作手冊。]: 快速搜尋與閱讀文件
```

`run_convert.bat` 仍會將額外命令列參數轉交給轉換流程。`convert_doc_to_docx.bat` 同樣會轉交所有命令列參數；這個批次檔只執行 DOC→DOCX，首頁參數會在之後執行 HTML 轉換時生效。

不過日常使用建議執行 `run_convert.bat`，避免漏掉新放入的 `.doc`。

## 常見問題

### 顯示 Python was not found in PATH

表示系統找不到 Python。請安裝 Python，並確認安裝時有勾選加入 PATH。

### 顯示 Pandoc was not found in PATH

表示系統找不到 Pandoc。請安裝 Pandoc，並確認 `pandoc --version` 可以在命令列執行。

### 顯示 pywin32 is not installed

請執行：

```powershell
pip install -r requirements.txt
```

### 顯示 Microsoft Word automation is not available

表示程式無法透過 Windows 自動化控制 Microsoft Word。請確認：

- Microsoft Word 已安裝。
- Word 可以正常手動開啟。
- Office 安裝沒有損毀。

### 同名 `.docx` 已存在但想重新轉檔

為了避免覆蓋人工整理過的檔案，工具預設會略過既有 `.docx`。如果要重轉，請先自行刪除同名 `.docx`，再重新執行批次檔。

### 轉換後看不到新內容

請重新執行 `run_convert.bat`，然後在瀏覽器使用 `Ctrl + F5` 強制重新整理 `out_html\index.html`。
