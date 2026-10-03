"""Render only case pages whose extracted text is unusable. Originals remain untouched."""

from contextlib import closing
from pathlib import Path
from threading import Lock

from readmark.ingest import IngestError

_RENDER_LOCK = Lock()  # PDFium is not thread-safe; concurrent uploads render one at a time.


def usable_text(text: str) -> bool:
    visible = [char for char in text if not char.isspace()]
    return (any(char.isalnum() for char in visible)
            and sum(char.isprintable() and char != "\ufffd" for char in visible)
            >= 0.8 * len(visible))


def render_page(pdf: Path, page_number: int, target: Path) -> None:
    import pypdfium2 as pdfium

    # PDF sizes are untrusted; cap the long edge while rendering at up to 144 dpi.
    # PDFium resources are explicitly released, including when a render or PNG write fails.
    try:
        with _RENDER_LOCK, closing(pdfium.PdfDocument(pdf)) as document:
            with closing(document[page_number - 1]) as page:
                width, height = page.get_size()
                scale = min(2, 2400 / max(width, height))
                with closing(page.render(scale=scale)) as bitmap:
                    image = bitmap.to_pil()
                    if all(low == high and high >= 250 for low, high in
                           image.convert("RGB").getextrema()):
                        raise IngestError(
                            "A scanned page has no readable text; your files are kept."
                        )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    image.save(target, format="PNG")
    except IngestError:
        raise
    except Exception as exc:
        raise IngestError("A scanned page could not be rendered; your files are kept.") from exc
