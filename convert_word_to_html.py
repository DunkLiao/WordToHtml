from __future__ import annotations

import argparse
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
DEFAULT_HOME_TITLE = "Word 文件索引"
DEFAULT_HOME_SUBTITLE = "快速搜尋與閱讀轉換完成的操作手冊。"


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
    (OUT_DIR / ".gitkeep").write_bytes(b"\n")


def normalize_media_paths(markup: str, page_dir: Path) -> str:
    page_prefix = page_dir.resolve().as_posix().rstrip("/") + "/"

    def replace_src(match: re.Match[str]) -> str:
        prefix, raw_src, suffix = match.groups()
        normalized_src = raw_src.replace("\\", "/")

        if normalized_src.startswith(page_prefix):
            relative_src = normalized_src[len(page_prefix) :]
        elif "/media/" in normalized_src:
            relative_src = "media/" + normalized_src.rsplit("/media/", 1)[1]
        else:
            return match.group(0)

        return f"{prefix}{html.escape(relative_src, quote=True)}{suffix}"

    return re.sub(r'(src=["\'])([^"\']+)(["\'])', replace_src, markup)


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
    return normalize_media_paths(content, page_dir)


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
<body class="document-page">
  <header class="page-header">
    <div class="page-header-inner">
      <a class="back-link" href="../../index.html" aria-label="回到文件索引">
        <span aria-hidden="true">←</span>
        回到文件索引
      </a>
      <p class="page-kicker">操作手冊</p>
      <h1>{escaped_title}</h1>
      <p class="source-name">來源檔案：{escaped_source}</p>
    </div>
  </header>
  <div class="reader-layout" id="reader-layout">
    <details class="page-outline" id="page-outline" hidden>
      <summary>本頁目錄</summary>
      <nav id="outline-links" aria-label="本頁目錄"></nav>
    </details>
    <main class="document" id="document-content">
{body}
    </main>
  </div>
  <button class="back-to-top" id="back-to-top" type="button" hidden aria-label="回到頁面頂端">
    <span aria-hidden="true">↑</span>
    <span>回到頂端</span>
  </button>
  <script src="../../assets/reader.js"></script>
</body>
</html>
"""


def index_html(
    title: str = DEFAULT_HOME_TITLE,
    subtitle: str = DEFAULT_HOME_SUBTITLE,
) -> str:
    title = title or DEFAULT_HOME_TITLE
    subtitle = subtitle or DEFAULT_HOME_SUBTITLE
    escaped_title = html.escape(title)
    escaped_subtitle = html.escape(subtitle)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body class="index-page">
  <main class="index-shell">
    <header class="index-header">
      <p class="eyebrow">文件知識庫</p>
      <h1>{escaped_title}</h1>
      <p class="index-intro">{escaped_subtitle}</p>
      <p class="doc-count" id="doc-count">載入中...</p>
    </header>
    <section class="search-panel" aria-label="文件搜尋">
      <label class="sr-only" for="search">搜尋文件標題或內容</label>
      <div class="search-box">
        <span class="search-icon" aria-hidden="true"></span>
        <input id="search" type="search" placeholder="搜尋標題、檔名或文件內容" autocomplete="off" autofocus>
        <kbd aria-hidden="true">/</kbd>
        <button id="clear-search" class="clear-search" type="button" hidden aria-label="清除搜尋">清除</button>
      </div>
      <p id="result-count" aria-live="polite"></p>
    </section>
    <section id="results" class="results" aria-live="polite"></section>
  </main>
  <script src="assets/search-data.js"></script>
  <script src="assets/search.js"></script>
</body>
</html>
"""


def stylesheet() -> str:
    return """:root {
  color-scheme: light;
  --page: #f4eee5;
  --surface: #fffdf8;
  --surface-soft: #f8f1e7;
  --ink: #2f2924;
  --muted: #73675e;
  --accent: #784832;
  --accent-strong: #5f3524;
  --accent-soft: #efe0d3;
  --border: #ded2c5;
  --mark: #f3d89f;
  --shadow: 0 18px 45px rgba(76, 53, 37, 0.09);
  --radius: 18px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  color: var(--ink);
  background: var(--page);
  font-family: "Microsoft JhengHei", "PingFang TC", "Noto Sans TC", Arial, sans-serif;
  line-height: 1.75;
  text-rendering: optimizeLegibility;
}

a {
  color: var(--accent);
  text-underline-offset: 0.18em;
}

button,
input {
  font: inherit;
}

:focus-visible {
  outline: 3px solid rgba(120, 72, 50, 0.28);
  outline-offset: 3px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.index-shell {
  width: min(1160px, calc(100% - 40px));
  margin: 0 auto;
  padding: 64px 0 72px;
}

.index-header {
  position: relative;
  margin-bottom: 30px;
  padding-right: 160px;
}

.index-header h1 {
  max-width: 760px;
  margin: 4px 0 10px;
  font-family: Georgia, "Times New Roman", "Noto Serif TC", serif;
  font-size: clamp(2.4rem, 5vw, 4.25rem);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.035em;
}

.eyebrow,
.page-kicker {
  margin: 0;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.index-intro,
.source-name,
#result-count {
  margin: 0;
  color: var(--muted);
}

.doc-count {
  position: absolute;
  top: 26px;
  right: 0;
  margin: 0;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--accent-strong);
  background: rgba(255, 253, 248, 0.72);
  font-weight: 700;
}

.search-panel {
  position: sticky;
  top: 12px;
  z-index: 5;
  margin: 0 0 24px;
  padding: 14px;
  border: 1px solid rgba(222, 210, 197, 0.88);
  border-radius: var(--radius);
  background: rgba(255, 253, 248, 0.9);
  box-shadow: 0 10px 30px rgba(76, 53, 37, 0.08);
  backdrop-filter: blur(14px);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 18px;
  width: 17px;
  height: 17px;
  border: 2px solid var(--accent);
  border-radius: 50%;
  pointer-events: none;
}

.search-icon::after {
  content: "";
  position: absolute;
  right: -5px;
  bottom: -4px;
  width: 7px;
  height: 2px;
  border-radius: 2px;
  background: var(--accent);
  transform: rotate(45deg);
}

#search {
  width: 100%;
  min-height: 58px;
  border: 1px solid var(--border);
  border-radius: 13px;
  padding: 0 124px 0 50px;
  color: var(--ink);
  background: var(--surface);
  box-shadow: inset 0 1px 2px rgba(76, 53, 37, 0.04);
}

#search:focus {
  border-color: var(--accent);
  outline: 3px solid rgba(120, 72, 50, 0.16);
}

.search-box kbd {
  position: absolute;
  right: 18px;
  min-width: 28px;
  padding: 2px 7px;
  border: 1px solid var(--border);
  border-bottom-width: 2px;
  border-radius: 6px;
  color: var(--muted);
  background: var(--surface-soft);
  text-align: center;
  font: 700 0.78rem/1.5 inherit;
}

.clear-search {
  position: absolute;
  right: 12px;
  min-height: 36px;
  border: 0;
  border-radius: 8px;
  padding: 0 12px;
  color: var(--accent-strong);
  background: var(--accent-soft);
  cursor: pointer;
  font-weight: 700;
}

.clear-search[hidden] {
  display: none;
}

.search-box:has(.clear-search:not([hidden])) kbd {
  display: none;
}

#result-count {
  margin-top: 10px;
  padding-left: 4px;
  font-size: 0.92rem;
}

.results {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.result {
  position: relative;
  display: block;
  min-height: 188px;
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: inherit;
  text-decoration: none;
  background: var(--surface);
  box-shadow: 0 6px 18px rgba(76, 53, 37, 0.045);
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.result:hover,
.result:focus-visible {
  border-color: var(--accent);
  box-shadow: var(--shadow);
  transform: translateY(-3px);
}

.result h2 {
  margin: 0 0 9px;
  color: var(--accent-strong);
  font-size: 1.18rem;
  line-height: 1.45;
}

.result .source {
  margin: 0 0 13px;
  color: var(--muted);
  font-size: 0.85rem;
  word-break: break-all;
}

.result .summary {
  margin: 0;
  color: #514941;
  font-size: 0.96rem;
}

mark {
  border-radius: 3px;
  padding: 0 0.08em;
  color: inherit;
  background: var(--mark);
}

.empty {
  grid-column: 1 / -1;
  padding: 46px 28px;
  border: 1px dashed #c9b9a8;
  border-radius: var(--radius);
  color: var(--muted);
  background: rgba(255, 253, 248, 0.72);
  text-align: center;
}

.page-header {
  border-bottom: 1px solid var(--border);
  background: rgba(255, 253, 248, 0.72);
}

.page-header-inner {
  width: min(1100px, calc(100% - 40px));
  margin: 0 auto;
  padding: 30px 0 26px;
}

.page-header h1 {
  max-width: 900px;
  margin: 8px 0 7px;
  font-family: Georgia, "Times New Roman", "Noto Serif TC", serif;
  font-size: clamp(1.9rem, 4vw, 3.2rem);
  line-height: 1.2;
  letter-spacing: -0.025em;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 32px;
  font-weight: 700;
  text-decoration: none;
}

.page-kicker {
  margin-top: 22px;
}

.reader-layout {
  display: grid;
  grid-template-columns: minmax(0, 820px);
  justify-content: center;
  width: min(1160px, calc(100% - 40px));
  margin: 32px auto 72px;
}

.reader-layout.has-outline {
  grid-template-columns: 230px minmax(0, 820px);
  gap: 30px;
  align-items: start;
}

.page-outline {
  position: sticky;
  top: 22px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: rgba(255, 253, 248, 0.76);
}

.page-outline summary {
  color: var(--accent-strong);
  cursor: pointer;
  font-weight: 800;
}

.outline-list {
  display: grid;
  gap: 8px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.outline-list a {
  display: block;
  border-left: 2px solid transparent;
  padding: 3px 0 3px 10px;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.45;
  text-decoration: none;
}

.outline-list .level-3 a {
  padding-left: 24px;
  font-size: 0.84rem;
}

.outline-list a:hover,
.outline-list a:focus-visible {
  border-left-color: var(--accent);
  color: var(--accent-strong);
}

.document {
  min-width: 0;
  width: 100%;
  padding: clamp(26px, 5vw, 56px);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
  font-size: 1.02rem;
}

.document h1,
.document h2,
.document h3 {
  scroll-margin-top: 24px;
  color: var(--accent-strong);
  font-family: Georgia, "Times New Roman", "Noto Serif TC", serif;
  line-height: 1.35;
}

.document h1 {
  font-size: 2rem;
}

.document h2 {
  margin-top: 2.2em;
  padding-bottom: 0.35em;
  border-bottom: 1px solid var(--border);
  font-size: 1.55rem;
}

.document h3 {
  margin-top: 1.8em;
  font-size: 1.25rem;
}

.document p,
.document li {
  max-width: 72ch;
}

.document img {
  display: inline-block;
  max-width: 100%;
  height: auto;
  border-radius: 6px;
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
  margin: 1.5em 0;
  overflow-x: auto;
  border-collapse: collapse;
  border-spacing: 0;
}

.document th,
.document td {
  border: 1px solid var(--border);
  padding: 9px 11px;
  vertical-align: top;
}

.document th {
  color: var(--accent-strong);
  background: var(--surface-soft);
}

.document blockquote {
  margin: 1.5em 0;
  border-left: 4px solid #b88768;
  padding: 0.7em 1.1em;
  color: #5c5148;
  background: var(--surface-soft);
}

.document pre {
  overflow-x: auto;
  padding: 16px;
  border-radius: 10px;
  background: #eee6dc;
}

.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 44px;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0 15px;
  color: var(--surface);
  background: var(--accent-strong);
  box-shadow: 0 10px 28px rgba(76, 53, 37, 0.2);
  cursor: pointer;
  font-weight: 700;
}

.back-to-top[hidden] {
  display: none;
}

@media (max-width: 900px) {
  .reader-layout.has-outline {
    grid-template-columns: minmax(0, 820px);
    gap: 16px;
  }

  .page-outline {
    position: static;
  }
}

@media (max-width: 700px) {
  .index-shell {
    width: min(100% - 28px, 1160px);
    padding: 36px 0 48px;
  }

  .index-header {
    padding-right: 0;
  }

  .doc-count {
    position: static;
    display: inline-block;
    margin-top: 16px;
  }

  .results {
    grid-template-columns: 1fr;
  }

  .result {
    min-height: 0;
  }

  .page-header-inner,
  .reader-layout {
    width: min(100% - 28px, 1160px);
  }

  .document {
    padding: 22px 18px;
    font-size: 1rem;
  }

  .back-to-top {
    right: 14px;
    bottom: 14px;
  }

  .back-to-top span:last-child {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}

@media print {
  body {
    background: white;
  }

  .page-header,
  .page-outline,
  .back-to-top {
    display: none !important;
  }

  .reader-layout,
  .reader-layout.has-outline {
    display: block;
    width: 100%;
    margin: 0;
  }

  .document {
    border: 0;
    padding: 0;
    box-shadow: none;
  }

  .document img,
  .document table,
  .document blockquote {
    break-inside: avoid;
  }
}
"""


def search_script() -> str:
    return """function normalize(value) {
  return String(value ?? "").toLocaleLowerCase();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function queryTerms(query) {
  return normalize(query).split(/\\s+/).filter(Boolean);
}

function filterDocuments(items, query) {
  const terms = queryTerms(query);
  if (!terms.length) return items;
  return items.filter((item) => {
    const haystack = normalize(`${item.title} ${item.source} ${item.text}`);
    return terms.every((term) => haystack.includes(term));
  });
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
}

function highlightText(value, terms) {
  const uniqueTerms = [...new Set(terms.filter(Boolean))]
    .sort((left, right) => right.length - left.length);
  if (!uniqueTerms.length) return escapeHtml(value);
  const pattern = new RegExp(`(${uniqueTerms.map(escapeRegExp).join("|")})`, "gi");
  return String(value ?? "").split(pattern).map((part, index) => (
    index % 2 ? `<mark>${escapeHtml(part)}</mark>` : escapeHtml(part)
  )).join("");
}

function makeExcerpt(value, terms, limit = 190) {
  const text = String(value ?? "").replace(/\\s+/g, " ").trim();
  if (!text || text.length <= limit) return text;

  const normalized = normalize(text);
  const positions = terms
    .map((term) => ({term, index: normalized.indexOf(normalize(term))}))
    .filter((entry) => entry.index >= 0)
    .sort((left, right) => left.index - right.index);
  const match = positions[0] ?? {term: "", index: 0};
  const matchLength = Math.min(match.term.length, limit);
  const initialContext = Math.max(0, Math.floor((limit - matchLength) / 2));
  let start = Math.max(0, match.index - initialContext);
  let end = Math.min(text.length, start + limit);
  if (end - start < limit) start = Math.max(0, end - limit);

  const prefix = start > 0 ? "..." : "";
  const suffix = end < text.length ? "..." : "";
  const available = Math.max(matchLength, limit - prefix.length - suffix.length);
  start = Math.max(0, match.index - Math.floor((available - matchLength) / 2));
  end = Math.min(text.length, start + available);
  if (end - start < available) start = Math.max(0, end - available);
  return `${start > 0 ? "..." : ""}${text.slice(start, end).trim()}${end < text.length ? "..." : ""}`;
}

function render(items, query, elements) {
  const {resultsEl, resultCountEl} = elements;
  const terms = queryTerms(query);
  resultCountEl.textContent = query
    ? `${items.length} 筆符合「${query}」`
    : `${items.length} 筆文件`;

  if (!items.length) {
    resultsEl.innerHTML = '<p class="empty">沒有符合的文件。</p>';
    return;
  }

  resultsEl.innerHTML = items.map((item) => `
    <a class="result" href="${escapeHtml(item.href)}">
      <h2>${highlightText(item.title, terms)}</h2>
      <p class="source">${escapeHtml(item.source)}</p>
      <p class="summary">${highlightText(
        query ? makeExcerpt(item.text, terms) : item.summary,
        terms,
      )}</p>
    </a>
  `).join("");
}

function initializeSearch() {
  if (typeof document === "undefined") return;
  const resultsEl = document.querySelector("#results");
  const searchEl = document.querySelector("#search");
  const clearEl = document.querySelector("#clear-search");
  const resultCountEl = document.querySelector("#result-count");
  const docCountEl = document.querySelector("#doc-count");
  if (!resultsEl || !searchEl || !clearEl || !resultCountEl || !docCountEl) return;

  const documents = typeof window !== "undefined" && Array.isArray(window.SEARCH_INDEX)
    ? window.SEARCH_INDEX
    : [];
  const elements = {resultsEl, resultCountEl};

  function runSearch() {
    const query = searchEl.value.trim();
    clearEl.hidden = !query;
    render(filterDocuments(documents, query), query, elements);
  }

  clearEl.addEventListener("click", () => {
    searchEl.value = "";
    runSearch();
    searchEl.focus();
  });

  searchEl.addEventListener("input", runSearch);
  document.addEventListener?.("keydown", (event) => {
    const target = event.target;
    const isEditing = target?.matches?.("input, textarea, [contenteditable='true']");
    if (event.key === "/" && !isEditing) {
      event.preventDefault();
      searchEl.focus();
    } else if (event.key === "Escape" && document.activeElement === searchEl) {
      searchEl.value = "";
      runSearch();
    }
  });

  if (documents.length) {
    docCountEl.textContent = `${documents.length} 份文件`;
    render(documents, "", elements);
  } else {
    docCountEl.textContent = "索引載入失敗";
    resultsEl.innerHTML = '<p class="empty">無法載入搜尋索引，請重新執行轉換。</p>';
  }
}

if (typeof module !== "undefined") {
  module.exports = {filterDocuments, highlightText, makeExcerpt, queryTerms};
} else {
  initializeSearch();
}
"""


def reader_script() -> str:
    return """function buildOutline(headings) {
  const entries = headings.map((heading) => ({
    id: String(heading.id ?? "").trim(),
    text: String(heading.text ?? heading.textContent ?? "").replace(/\\s+/g, " ").trim(),
    level: Number(heading.level ?? String(heading.tagName ?? "").slice(1)),
  })).filter((entry) => entry.id && entry.text && (entry.level === 2 || entry.level === 3));
  return entries.length >= 2 ? entries : [];
}

function initializeReader() {
  if (typeof document === "undefined") return;
  const outlineEl = document.querySelector("#page-outline");
  const linksEl = document.querySelector("#outline-links");
  const layoutEl = document.querySelector("#reader-layout");
  const topEl = document.querySelector("#back-to-top");
  if (!outlineEl || !linksEl || !layoutEl || !topEl) return;

  const headings = [...document.querySelectorAll(".document h2, .document h3")];
  headings.forEach((heading, index) => {
    if (!heading.id) heading.id = `section-${index + 1}`;
  });
  const entries = buildOutline(headings);
  if (entries.length) {
    const list = document.createElement("ol");
    list.className = "outline-list";
    entries.forEach((entry) => {
      const item = document.createElement("li");
      item.className = `level-${entry.level}`;
      const link = document.createElement("a");
      link.href = `#${encodeURIComponent(entry.id)}`;
      link.textContent = entry.text;
      item.append(link);
      list.append(item);
    });
    linksEl.append(list);
    outlineEl.hidden = false;
    outlineEl.open = typeof window !== "undefined" && window.matchMedia("(min-width: 901px)").matches;
    layoutEl.classList.add("has-outline");
  }

  function updateTopButton() {
    topEl.hidden = (typeof window === "undefined" ? 0 : window.scrollY) < 600;
  }
  window.addEventListener("scroll", updateTopButton, {passive: true});
  topEl.addEventListener("click", () => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({top: 0, behavior: reducedMotion ? "auto" : "smooth"});
  });
  updateTopButton();
}

if (typeof module !== "undefined") {
  module.exports = {buildOutline};
} else {
  initializeReader();
}
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="將 Word 文件轉換成 HTML 網站")
    parser.add_argument(
        "--home-title",
        default=DEFAULT_HOME_TITLE,
        help="首頁標題",
    )
    parser.add_argument(
        "--home-subtitle",
        default=DEFAULT_HOME_SUBTITLE,
        help="首頁副標",
    )
    return parser.parse_args(argv)


def convert_all(
    home_title: str = DEFAULT_HOME_TITLE,
    home_subtitle: str = DEFAULT_HOME_SUBTITLE,
) -> None:
    sources = sorted(SOURCE_DIR.glob("*.docx"), key=lambda path: path.name.lower())
    if not sources:
        raise RuntimeError(f"No .docx files found in {SOURCE_DIR}")

    clean_output()
    (ASSETS_DIR / "site.css").write_text(stylesheet(), encoding="utf-8")
    (ASSETS_DIR / "search.js").write_text(search_script(), encoding="utf-8")
    (ASSETS_DIR / "reader.js").write_text(reader_script(), encoding="utf-8")

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

    (OUT_DIR / "index.html").write_text(
        index_html(home_title, home_subtitle), encoding="utf-8"
    )
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    convert_all(args.home_title, args.home_subtitle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
