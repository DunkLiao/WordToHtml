from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from convert_doc_to_docx import ConversionResult, collect_doc_files, convert_doc_files


class FakeDocument:
    def __init__(self, opened_path: str) -> None:
        self.opened_path = opened_path
        self.saved_as: tuple[str, int] | None = None
        self.closed = False

    def SaveAs2(self, output_path: str, FileFormat: int) -> None:  # noqa: N803
        self.saved_as = (output_path, FileFormat)
        Path(output_path).write_text("converted", encoding="utf-8")

    def Close(self, SaveChanges: bool = False) -> None:  # noqa: N803
        self.closed = True


class FakeDocuments:
    def __init__(self) -> None:
        self.opened: list[FakeDocument] = []

    def Open(self, path: str, ReadOnly: bool = True, AddToRecentFiles: bool = False) -> FakeDocument:  # noqa: N803
        document = FakeDocument(path)
        self.opened.append(document)
        return document


class FakeWord:
    def __init__(self) -> None:
        self.Documents = FakeDocuments()
        self.Visible = True
        self.DisplayAlerts = 1
        self.quit_called = False

    def Quit(self) -> None:
        self.quit_called = True


class ConvertDocToDocxTests(unittest.TestCase):
    def test_collect_doc_files_ignores_docx_and_word_temp_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "alpha.doc").write_text("old", encoding="utf-8")
            (root / "beta.docx").write_text("new", encoding="utf-8")
            (root / "~$locked.doc").write_text("temp", encoding="utf-8")

            self.assertEqual(collect_doc_files(root), [root / "alpha.doc"])

    def test_convert_doc_files_skips_existing_docx(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "alpha.doc"
            source.write_text("old", encoding="utf-8")
            (root / "alpha.docx").write_text("existing", encoding="utf-8")
            fake_word = FakeWord()

            result = convert_doc_files([source], word_factory=lambda: fake_word)

            self.assertEqual(result, ConversionResult(converted=0, skipped=1, failed=0))
            self.assertEqual(fake_word.Documents.opened, [])
            self.assertFalse(fake_word.quit_called)

    def test_convert_doc_files_saves_doc_as_docx_and_closes_word(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "alpha.doc"
            source.write_text("old", encoding="utf-8")
            fake_word = FakeWord()

            result = convert_doc_files([source], word_factory=lambda: fake_word)

            self.assertEqual(result, ConversionResult(converted=1, skipped=0, failed=0))
            opened_document = fake_word.Documents.opened[0]
            self.assertEqual(opened_document.opened_path, str(source))
            self.assertEqual(opened_document.saved_as, (str(root / "alpha.docx"), 16))
            self.assertTrue(opened_document.closed)
            self.assertFalse(fake_word.Visible)
            self.assertEqual(fake_word.DisplayAlerts, 0)
            self.assertTrue(fake_word.quit_called)

    def test_convert_doc_files_records_failure_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.doc"
            second = root / "second.doc"
            first.write_text("old", encoding="utf-8")
            second.write_text("old", encoding="utf-8")

            class FailingDocument(FakeDocument):
                def SaveAs2(self, output_path: str, FileFormat: int) -> None:  # noqa: N803
                    raise RuntimeError("cannot save")

            class PartlyFailingDocuments(FakeDocuments):
                def Open(
                    self,
                    path: str,
                    ReadOnly: bool = True,
                    AddToRecentFiles: bool = False,
                ) -> FakeDocument:  # noqa: N803
                    if path.endswith("first.doc"):
                        document = FailingDocument(path)
                    else:
                        document = FakeDocument(path)
                    self.opened.append(document)
                    return document

            fake_word = FakeWord()
            fake_word.Documents = PartlyFailingDocuments()

            result = convert_doc_files([first, second], word_factory=lambda: fake_word)

            self.assertEqual(result, ConversionResult(converted=1, skipped=0, failed=1))
            self.assertTrue(fake_word.Documents.opened[0].closed)
            self.assertTrue(fake_word.Documents.opened[1].closed)
            self.assertTrue(fake_word.quit_called)


if __name__ == "__main__":
    unittest.main()
