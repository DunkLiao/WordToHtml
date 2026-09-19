from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

import convert_word_to_html as converter


class ElementCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.elements.append(
            (tag, {name: value or "" for name, value in attrs})
        )


def parse_elements(markup: str) -> list[tuple[str, dict[str, str]]]:
    parser = ElementCollector()
    parser.feed(markup)
    return parser.elements


def run_javascript(source: str, expression: str) -> object:
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "generated.js"
        script_path.write_text(source, encoding="utf-8")
        command = [
            "node",
            "-e",
            (
                "global.window = {SEARCH_INDEX: []};"
                "global.document = {querySelector() { return {"
                "textContent: '', innerHTML: '', value: '', hidden: false,"
                "addEventListener() {}, classList: {add() {}, remove() {}}"
                "}; }};"
                f"const api = require({json.dumps(str(script_path))});"
                f"process.stdout.write(JSON.stringify({expression}));"
            ),
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip())
        return json.loads(completed.stdout)


class GeneratedInterfaceTests(unittest.TestCase):
    def test_clean_output_preserves_tracked_directory_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            out_dir = root / "out_html"
            pages_dir = out_dir / "pages"
            assets_dir = out_dir / "assets"
            out_dir.mkdir()
            (out_dir / ".gitkeep").write_bytes(b"\n")
            (out_dir / "stale.html").write_text("old", encoding="utf-8")

            with (
                patch.object(converter, "ROOT", root),
                patch.object(converter, "OUT_DIR", out_dir),
                patch.object(converter, "PAGES_DIR", pages_dir),
                patch.object(converter, "ASSETS_DIR", assets_dir),
            ):
                converter.clean_output()

            self.assertTrue((out_dir / ".gitkeep").is_file())
            self.assertEqual((out_dir / ".gitkeep").read_bytes(), b"\n")
            self.assertFalse((out_dir / "stale.html").exists())

    def test_index_exposes_accessible_search_controls(self) -> None:
        elements = parse_elements(converter.index_html())
        by_id = {
            attrs["id"]: (tag, attrs)
            for tag, attrs in elements
            if "id" in attrs
        }

        self.assertEqual(by_id["search"][0], "input")
        self.assertEqual(by_id.get("clear-search", (None, {}))[0], "button")
        self.assertEqual(
            by_id.get("result-count", (None, {}))[1].get("aria-live"),
            "polite",
        )
        self.assertEqual(by_id["results"][1]["aria-live"], "polite")

    def test_document_page_escapes_metadata_and_loads_reader_controls(self) -> None:
        markup = converter.page_html("A < B", 'manual "draft".docx', "<p>Body</p>")
        elements = parse_elements(markup)
        by_id = {
            attrs["id"]: (tag, attrs)
            for tag, attrs in elements
            if "id" in attrs
        }

        self.assertIn("A &lt; B", markup)
        self.assertIn("manual &quot;draft&quot;.docx", markup)
        self.assertEqual(by_id.get("page-outline", (None, {}))[0], "details")
        self.assertEqual(by_id.get("back-to-top", (None, {}))[0], "button")
        self.assertTrue(
            any(
                tag == "script" and attrs.get("src") == "../../assets/reader.js"
                for tag, attrs in elements
            )
        )

    def test_search_helpers_require_every_term_and_escape_highlights(self) -> None:
        expression = "api.filterDocuments ? ({matches: api.filterDocuments(["
        expression += "{title:'Alpha guide',source:'one.docx',text:'Beta steps'},"
        expression += "{title:'Alpha only',source:'two.docx',text:'Other'}"
        expression += "], 'alpha beta').map(item => item.source),"
        expression += "highlight: api.highlightText('<Alpha & beta>', ['alpha', 'beta'])})"
        expression += " : ({matches: null, highlight: null})"

        result = run_javascript(converter.search_script(), expression)

        self.assertEqual(result["matches"], ["one.docx"])
        self.assertEqual(
            result["highlight"],
            "&lt;<mark>Alpha</mark> &amp; <mark>beta</mark>&gt;",
        )

    def test_search_excerpt_centers_on_first_matching_term(self) -> None:
        result = run_javascript(
            converter.search_script(),
            "api.makeExcerpt ? api.makeExcerpt('0123456789 target 9876543210', ['target'], 18) : null",
        )

        self.assertIsInstance(result, str)
        self.assertIn("target", result)
        self.assertLessEqual(len(result), 21)
        self.assertTrue(result.startswith("..."))
        self.assertTrue(result.endswith("..."))

    def test_search_highlight_treats_regular_expression_symbols_as_text(self) -> None:
        result = run_javascript(
            converter.search_script(),
            "api.highlightText('Use a+b (draft)', ['a+b', '(draft)'])",
        )

        self.assertEqual(
            result,
            "Use <mark>a+b</mark> <mark>(draft)</mark>",
        )

    def test_reader_outline_requires_two_headings(self) -> None:
        expression = "({empty: api.buildOutline([{id:'one',text:'One',level:2}]),"
        expression += "full: api.buildOutline(["
        expression += "{id:'one',text:'One',level:2},"
        expression += "{id:'two',text:'Two',level:3}])})"

        source = getattr(
            converter,
            "reader_script",
            lambda: "module.exports = { buildOutline() { return null; } };",
        )()
        result = run_javascript(source, expression)

        self.assertEqual(result["empty"], [])
        self.assertEqual(
            result["full"],
            [
                {"id": "one", "text": "One", "level": 2},
                {"id": "two", "text": "Two", "level": 3},
            ],
        )


if __name__ == "__main__":
    unittest.main()
