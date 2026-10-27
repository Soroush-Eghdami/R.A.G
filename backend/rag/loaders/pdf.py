"""PDF files, one block per page so citations can show a page number."""

from __future__ import annotations

from pathlib import Path

from .base import EmptyDocument, LoaderError, TextBlock, clean_text

try:
    import pymupdf
except ImportError as exc:  # pragma: no cover
    pymupdf = None  # type: ignore[assignment]
    _IMPORT_ERROR: Exception | None = exc
else:
    _IMPORT_ERROR = None


def load(path: Path) -> list[TextBlock]:
    if pymupdf is None:  # pragma: no cover
        raise LoaderError("PyMuPDF is not installed.") from _IMPORT_ERROR

    try:
        document = pymupdf.open(path)
    except Exception as exc:  # noqa: BLE001 - PyMuPDF raises many types
        raise LoaderError(f"Could not open {path.name}: {exc}") from exc

    blocks: list[TextBlock] = []
    try:
        if document.needs_pass:
            raise LoaderError(f"{path.name} is password protected.")
        for page_number, page in enumerate(document, start=1):
            try:
                text = clean_text(page.get_text("text"))
            except Exception as exc:  # noqa: BLE001
                raise LoaderError(
                    f"Could not read page {page_number} of {path.name}: {exc}"
                ) from exc
            if text:
                blocks.append(TextBlock(text=text, page=page_number))
    finally:
        document.close()

    if not blocks:
        raise EmptyDocument(f"{path.name} has no text. Scanned PDFs need OCR.")
    return blocks
