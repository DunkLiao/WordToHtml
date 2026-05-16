# WordToHtml 使用手冊

WordToHtml 可以把 `source_word` 資料夾中的 Word 文件（`.docx`）轉成可用瀏覽器開啟的靜態網頁。轉換完成後，會在 `out_html` 產生一個文件索引頁，使用者可以直接瀏覽所有文件，也可以搜尋標題與內文。

## 適合用來做什麼

- 把多份 Word 教育訓練手冊整理成網頁版。
- 產生一個可以搜尋所有文件內容的入口頁。
- 將轉換後的 `out_html` 資料夾提供給其他人離線瀏覽，或放到內部網站上。

## 資料夾說明

| 位置 | 用途 |
| --- | --- |
| `source_word` | 放入要轉換的 Word 文件。只會處理副檔名為 `.docx` 的檔案。 |
| `out_html` | 轉換完成後的網頁輸出位置。每次轉換時會重新產生內容。 |
| `run_convert.bat` | Windows 使用者建議直接執行這個檔案來轉換。 |
| `convert_word_to_html.py` | 實際執行轉換的程式，一般使用者通常不需要修改。 |

## 第一次使用前準備

本工具需要先安裝兩個程式：

1. Python 3.10 或更新版本
2. Pandoc 3.6 或更新版本

安裝完成後，可以用下面方式確認電腦是否已經可以執行：

1. 在此資料夾空白處按住 `Shift`，按滑鼠右鍵，選擇「在終端機中開啟」或「在 PowerShell 中開啟」。
2. 輸入以下指令：

```powershell
python --version
pandoc --version
```

如果兩個指令都有顯示版本號，代表環境已準備完成。

如果出現「找不到 python」或「找不到 pandoc」，請先安裝對應程式，或請資訊人員協助確認安裝路徑是否已加入系統環境變數。

## 安裝 Python 套件

第一次使用，或換到新電腦使用時，請在此資料夾中執行：

```powershell
pip install -r requirements.txt
```

這個步驟只需要做一次。之後如果只是新增 Word 文件並重新轉換，通常不需要再執行。

## 轉換 Word 文件

1. 將要轉換的 Word 文件放進 `source_word` 資料夾。
2. 確認檔案副檔名是 `.docx`。
3. 雙擊 `run_convert.bat`。
4. 等待視窗顯示轉換進度。
5. 看到 `Conversion completed. Open out_html\index.html to browse the result.` 代表轉換完成。
6. 開啟 `out_html\index.html` 即可瀏覽結果。

轉換時會自動處理 `source_word` 裡所有 `.docx` 文件。文件名稱會成為網頁標題，因此建議先把 Word 檔名整理成容易辨識的名稱。

## 瀏覽與搜尋結果

轉換完成後，請開啟：

```text
out_html\index.html
```

索引頁會列出所有已轉換文件。上方搜尋框可以搜尋：

- 文件標題
- 原始 Word 檔名
- 文件內文

點選搜尋結果後會進入該文件的網頁版。文件頁面左上方有「回到索引」連結，可以回到總列表。

## 重新轉換

如果新增、刪除或修改了 `source_word` 裡的 Word 文件，只要再次雙擊 `run_convert.bat` 即可。

注意：每次重新轉換時，`out_html` 會被重新產生。請不要把手動修改的重要檔案放在 `out_html` 裡，避免下次轉換時被覆蓋。

## 可以分享哪些檔案

如果只是要讓別人瀏覽轉換後的文件，通常只需要分享整個 `out_html` 資料夾。

請保留 `out_html` 裡的完整資料夾結構，不要只複製單一 HTML 檔，否則圖片、樣式或搜尋功能可能無法正常顯示。

## 常見問題

### 雙擊 `run_convert.bat` 後顯示 Python was not found in PATH

代表電腦找不到 Python。請確認 Python 已安裝，並且安裝時有勾選加入 PATH，或請資訊人員協助設定。

### 雙擊 `run_convert.bat` 後顯示 Pandoc was not found in PATH

代表電腦找不到 Pandoc。請確認 Pandoc 已安裝，並且可以在 PowerShell 中執行 `pandoc --version`。

### 顯示 No .docx files found

代表 `source_word` 資料夾中沒有可轉換的 `.docx` 檔案。請確認 Word 文件已放入 `source_word`，且副檔名不是 `.doc`、`.pdf` 或其他格式。

### 開啟網頁後沒有看到最新內容

請重新雙擊 `run_convert.bat` 產生一次新的 `out_html`，再重新開啟 `out_html\index.html`。如果瀏覽器仍顯示舊內容，可以按 `Ctrl + F5` 強制重新整理。

### Word 裡的版面和網頁看起來不完全一樣

這是正常情況。此工具會盡量保留文字、標題、表格、圖片與公式，但 Word 的頁首頁尾、頁碼、部分複雜排版或特殊樣式，轉成網頁後可能會和原始 Word 不完全相同。

## 進階執行方式

熟悉命令列的使用者，也可以不透過 `run_convert.bat`，直接在此資料夾執行：

```powershell
python .\convert_word_to_html.py
```

成功後會產生：

- `out_html/index.html`：文件索引與搜尋頁
- `out_html/search-index.json`：搜尋索引資料
- `out_html/pages/.../index.html`：每份 Word 文件轉換後的網頁
