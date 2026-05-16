# WordToHtml

Convert `.docx` files in `source_word` into searchable static HTML pages in `out_html`.

## Prerequisites

- Python 3.10+
- Pandoc 3.6+

## Verify Environment

```powershell
python --version
pandoc --version
```

## Install Python Dependencies

```powershell
pip install -r requirements.txt
```

## Run Conversion

```powershell
python .\convert_word_to_html.py
```

Output:

- `out_html/index.html` (entry index page with search)
- `out_html/search-index.json` (search index data)
- `out_html/pages/.../index.html` (converted pages)
