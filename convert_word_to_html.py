from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "source_word"
OUT_DIR = ROOT / "out_html"
PAGES_DIR = OUT_DIR / "pages"
ASSETS_DIR = OUT_DIR / "assets"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def slugify(name: str) -> str:
    stem = Path(name).stem
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem).strip(" .")
    safe = re.sub(r"_+", "_", safe)
    return safe or "document"


def unique_slug(base: str, used: set[str]) -> str:
    slug = base
    counter = 2
    while slug.lower() in used:
        slug = f"{base}-{counter}"
        counter += 1
    used.add(slug.lower())
    return slug


def clean_output() -> None:
    resolved_out = OUT_DIR.resolve()
    resolved_root = ROOT.resolve()
    if resolved_out == resolved_root or resolved_root not in resolved_out.parents:
        raise RuntimeError(f"Refusing to remove unsafe output directory: {resolved_out}")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def run_pandoc(source: Path, page_dir: Path, title: str) -> str:
    content_path = page_dir / "_content.html"
    command = [
        "pandoc",
        str(source),
        "--from=docx",
        "--to=html5",
        "--mathml",
        "--wrap=none",
        f"--extract-media={page_dir}",
        "--metadata",
        f"title={title}",
        "-o",
        str(content_path),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    content = content_path.read_text(encoding="utf-8")
    content_path.unlink()
    return content


def extract_text(markup: str) -> str:
    parser = TextExtractor()
    parser.feed(markup)
    return parser.text()


def make_summary(text: str, limit: int = 180) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def page_html(title: str, source_name: str, body: str) -> str:
    escaped_title = html.escape(title)
    escaped_source = html.escape(source_name)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <link rel="stylesheet" href="../../assets/site.css">
</head>
<body>
  <header class="page-header">
    <a class="back-link" href="../../index.html">回到索引</a>
    <h1>{escaped_title}</h1>
    <p>{escaped_source}</p>
  </header>
  <main class="document">
{body}
  </main>
</body>
</html>
"""


def index_html() -> str:
    return """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Word 文件索引</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
  <main class="index-shell">
    <header class="index-header">
      <h1>Word 文件索引</h1>
      <p id="doc-count">載入中...</p>
    </header>
    <section class="search-panel" aria-label="文件搜尋">
      <input id="search" type="search" placeholder="搜尋標題或內容" autocomplete="off" autofocus>
      <p id="result-count"></p>
    </section>
    <section id="results" class="results" aria-live="polite"></section>
  </main>
  <script src="assets/search-data.js"></script>
  <script src="assets/search.js"></script>
</body>
</html>
"""


def stylesheet() -> str:
    return """* {
  box-sizing: border-box;
}

body {
  margin: 0;
  color: #1f2933;
  background: #f7f8fa;
  font-family: "Microsoft JhengHei", "PingFang TC", "Noto Sans TC", Arial, sans-serif;
  line-height: 1.7;
}

a {
  color: #0f5f8c;
}

.index-shell {
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 56px;
}

.index-header {
  margin-bottom: 24px;
}

.index-header h1 {
  margin: 0 0 8px;
  font-size: clamp(2rem, 4vw, 3.25rem);
  line-height: 1.15;
}

.index-header p,
.page-header p,
#result-count {
  margin: 0;
  color: #5b6776;
}

.search-panel {
  position: sticky;
  top: 0;
  z-index: 2;
  margin: 0 0 20px;
  padding: 16px 0;
  background: #f7f8fa;
}

#search {
  width: 100%;
  height: 48px;
  border: 1px solid #c9d2dc;
  border-radius: 6px;
  padding: 0 14px;
  font: inherit;
  background: white;
}

#search:focus {
  border-color: #0f5f8c;
  outline: 3px solid rgba(15, 95, 140, 0.16);
}

#result-count {
  margin-top: 8px;
}

.results {
  display: grid;
  gap: 12px;
}

.result {
  display: block;
  padding: 18px;
  border: 1px solid #d9e0e8;
  border-radius: 8px;
  color: inherit;
  text-decoration: none;
  background: white;
}

.result:hover,
.result:focus {
  border-color: #0f5f8c;
  outline: none;
}

.result h2 {
  margin: 0 0 6px;
  font-size: 1.1rem;
  line-height: 1.4;
}

.result .source {
  margin: 0 0 8px;
  color: #697586;
  font-size: 0.92rem;
}

.result .summary {
  margin: 0;
}

.empty {
  padding: 28px;
  border: 1px dashed #b9c4cf;
  border-radius: 8px;
  color: #5b6776;
  background: white;
}

.page-header {
  width: min(980px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 16px;
}

.page-header h1 {
  margin: 10px 0 6px;
  font-size: clamp(1.7rem, 3vw, 2.5rem);
  line-height: 1.25;
}

.back-link {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  font-weight: 700;
  text-decoration: none;
}

.document {
  width: min(980px, calc(100% - 32px));
  margin: 0 auto 56px;
  padding: 28px;
  border: 1px solid #d9e0e8;
  border-radius: 8px;
  background: white;
}

.document img {
  max-width: 100%;
  height: auto;
}

.document math {
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  vertical-align: middle;
}

.document math[display="block"] {
  display: block;
  margin: 1em 0;
}

.document table {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
}

.document th,
.document td {
  border: 1px solid #c9d2dc;
  padding: 6px 8px;
  vertical-align: top;
}

.document pre {
  overflow-x: auto;
  padding: 12px;
  background: #f1f4f7;
}

@media (max-width: 640px) {
  .document {
    padding: 18px;
  }
}
"""


def search_script() -> str:
    return """const resultsEl = document.querySelector("#results");
const searchEl = document.querySelector("#search");
const resultCountEl = document.querySelector("#result-count");
const docCountEl = document.querySelector("#doc-count");

let documents = Array.isArray(window.SEARCH_INDEX) ? window.SEARCH_INDEX : [];

function normalize(value) {
  return value.toLocaleLowerCase();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function render(items, query = "") {
  resultCountEl.textContent = query
    ? `${items.length} 筆符合「${query}」`
    : `${items.length} 筆文件`;

  if (!items.length) {
    resultsEl.innerHTML = '<p class="empty">沒有符合的文件。</p>';
    return;
  }

  resultsEl.innerHTML = items.map((item) => `
    <a class="result" href="${escapeHtml(item.href)}">
      <h2>${escapeHtml(item.title)}</h2>
      <p class="source">${escapeHtml(item.source)}</p>
      <p class="summary">${escapeHtml(item.summary)}</p>
    </a>
  `).join("");
}

function runSearch() {
  const query = searchEl.value.trim();
  const normalized = normalize(query);
  if (!normalized) {
    render(documents);
    return;
  }

  const terms = normalized.split(/\\s+/).filter(Boolean);
  const matches = documents.filter((item) => {
    const haystack = normalize(`${item.title} ${item.source} ${item.text}`);
    return terms.every((term) => haystack.includes(term));
  });
  render(matches, query);
}

if (documents.length) {
  docCountEl.textContent = `${documents.length} 份文件`;
  render(documents);
  searchEl.addEventListener("input", runSearch);
} else {
  docCountEl.textContent = "索引載入失敗";
  resultsEl.innerHTML = '<p class="empty">無法載入搜尋索引。</p>';
}
"""


def convert_all() -> None:
    sources = sorted(SOURCE_DIR.glob("*.docx"), key=lambda path: path.name.lower())
    if not sources:
        raise RuntimeError(f"No .docx files found in {SOURCE_DIR}")

    clean_output()
    (ASSETS_DIR / "site.css").write_text(stylesheet(), encoding="utf-8")
    (ASSETS_DIR / "search.js").write_text(search_script(), encoding="utf-8")

    used_slugs: set[str] = set()
    index: list[dict[str, str]] = []

    for source in sources:
        title = source.stem
        slug = unique_slug(slugify(source.name), used_slugs)
        page_dir = PAGES_DIR / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        print(f"Converting {source.name}")
        body = run_pandoc(source, page_dir, title)
        text = extract_text(body)
        (page_dir / "index.html").write_text(page_html(title, source.name, body), encoding="utf-8")
        index.append(
            {
                "title": title,
                "source": source.name,
                "href": f"pages/{slug}/index.html",
                "summary": make_summary(text),
                "text": text,
            }
        )

    (OUT_DIR / "index.html").write_text(index_html(), encoding="utf-8")
    (ASSETS_DIR / "search-data.js").write_text(
        "window.SEARCH_INDEX = "
        + json.dumps(index, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    (OUT_DIR / "search-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Done. Converted {len(index)} documents into {OUT_DIR}")


if __name__ == "__main__":
    convert_all()
