"""
extractor.py — PDF text extraction via PyMuPDF (fitz).

Returns a list of pages. Each page is a dict:
    {
        'page_num': int,          # 1-indexed
        'blocks': [
            {
                'type': 'heading' | 'body',
                'text': str,       # raw text of the block
            },
            ...
        ]
    }

Heading detection: any span whose font size exceeds the page's modal
body-text size by ≥ 20% is treated as a heading.
"""

from __future__ import annotations
from statistics import mode, StatisticsError
from typing import Any
import fitz  # PyMuPDF


def extract_pdf(path: str) -> list[dict]:
    """Open a PDF and return structured page data."""
    doc = fitz.open(path)
    pages: list[dict] = []

    for page_index, page in enumerate(doc):
        raw_dict: dict[str, Any] = page.get_text("dict")  # type: ignore[attr-defined]
        raw_blocks: list[dict] = raw_dict.get("blocks", [])

        # ── 1. Collect all font sizes on the page ──────────────────────────
        font_sizes: list[float] = []
        for blk in raw_blocks:
            if blk.get("type") != 0:
                continue
            for line in blk.get("lines", []):
                for span in line.get("spans", []):
                    sz = span.get("size", 12.0)
                    if sz > 0:
                        font_sizes.append(round(sz, 1))

        # Determine the "body" size (statistical mode, or median fallback)
        if font_sizes:
            try:
                body_size = mode(font_sizes)
            except StatisticsError:
                sorted_sizes = sorted(font_sizes)
                body_size = sorted_sizes[len(sorted_sizes) // 2]
        else:
            body_size = 12.0

        heading_threshold = body_size * 1.20

        # ── 2. Build structured blocks ─────────────────────────────────────
        page_blocks: list[dict] = []
        for blk in raw_blocks:
            if blk.get("type") != 0:
                continue  # skip image / drawing blocks

            text_parts: list[str] = []
            block_is_heading = False

            for line in blk.get("lines", []):
                line_parts: list[str] = []
                for span in line.get("spans", []):
                    span_text: str = span.get("text", "")
                    if not span_text.strip():
                        continue
                    span_size: float = span.get("size", 12.0)
                    if span_size >= heading_threshold:
                        block_is_heading = True
                    line_parts.append(span_text)

                line_text = "".join(line_parts).strip()
                if line_text:
                    text_parts.append(line_text)

            combined = " ".join(text_parts).strip()
            if combined:
                page_blocks.append(
                    {
                        "type": "heading" if block_is_heading else "body",
                        "text": combined,
                    }
                )

        pages.append({"page_num": page_index + 1, "blocks": page_blocks})

    doc.close()
    return pages


def word_count(pages: list[dict]) -> int:
    """Count total words across all extracted pages."""
    total = 0
    for page in pages:
        for blk in page["blocks"]:
            total += len(blk["text"].split())
    return total
