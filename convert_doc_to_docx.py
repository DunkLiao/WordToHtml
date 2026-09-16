from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Protocol


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "source_word"
WD_FORMAT_XML_DOCUMENT = 16


class WordDocument(Protocol):
    def SaveAs2(self, output_path: str, FileFormat: int) -> None: ...

    def Close(self, SaveChanges: bool = False) -> None: ...


class WordDocuments(Protocol):
    def Open(
        self,
        path: str,
        ReadOnly: bool = True,
        AddToRecentFiles: bool = False,
    ) -> WordDocument: ...


class WordApplication(Protocol):
    Documents: WordDocuments
    Visible: bool
    DisplayAlerts: int

    def Quit(self) -> None: ...


@dataclass(frozen=True)
class ConversionResult:
    converted: int = 0
    skipped: int = 0
    failed: int = 0


def collect_doc_files(source_dir: Path = SOURCE_DIR) -> list[Path]:
    return sorted(
        (
            path
            for path in source_dir.glob("*.doc")
            if path.is_file() and not path.name.startswith("~$")
        ),
        key=lambda path: path.name.lower(),
    )


def create_word_application() -> WordApplication:
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is not installed. Run: pip install -r requirements.txt"
        ) from exc

    try:
        return win32com.client.DispatchEx("Word.Application")
    except Exception as exc:  # pragma: no cover - depends on local Office install
        raise RuntimeError(
            "Microsoft Word automation is not available. Install Microsoft Word "
            "or repair the Office installation, then try again."
        ) from exc


def convert_doc_files(
    sources: Iterable[Path],
    word_factory: Callable[[], WordApplication] = create_word_application,
) -> ConversionResult:
    converted = 0
    skipped = 0
    failed = 0
    word: WordApplication | None = None

    for source in sources:
        output = source.with_suffix(".docx")
        if output.exists():
            print(f"Skipped existing {output.name}")
            skipped += 1
            continue

        if word is None:
            word = word_factory()
            word.Visible = False
            word.DisplayAlerts = 0

        document: WordDocument | None = None
        try:
            print(f"Converting {source.name} -> {output.name}")
            document = word.Documents.Open(
                str(source),
                ReadOnly=True,
                AddToRecentFiles=False,
            )
            document.SaveAs2(str(output), FileFormat=WD_FORMAT_XML_DOCUMENT)
            converted += 1
        except Exception as exc:
            failed += 1
            print(f"Failed {source.name}: {exc}")
        finally:
            if document is not None:
                try:
                    document.Close(SaveChanges=False)
                except Exception as exc:
                    failed += 1
                    print(f"Failed to close {source.name}: {exc}")

    if word is not None:
        word.Quit()

    return ConversionResult(converted=converted, skipped=skipped, failed=failed)


def main() -> int:
    sources = collect_doc_files()
    if not sources:
        print(f"No .doc files found in {SOURCE_DIR}")
        return 0

    try:
        result = convert_doc_files(sources)
    except RuntimeError as exc:
        print(exc)
        return 1

    print(
        "DOC conversion finished. "
        f"Converted: {result.converted}, skipped: {result.skipped}, failed: {result.failed}."
    )
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
