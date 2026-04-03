"""
renderer.py — Converts structured page data into styled HTML.

The output is a self-contained HTML document that:
  - Renders inside QTextBrowser (limited CSS subset)
  - Can also be exported as a standalone .html file

Design: warm paper reading surface, Lora serif body, amber bold anchors.
"""

from __future__ import annotations
from bionic import transform_text

# ── Inline CSS (QTextBrowser + standalone export compatible) ────────────────
# QTextBrowser supports: font-*, color, background-color, margin, padding,
# text-align, border-bottom, and basic selectors.
_CSS = """
body {
    background-color: #f6f0e6;
    color: #2a2420;
    font-family: 'Lora', Georgia, 'Times New Roman', serif;
    font-size: 17px;
    line-height: 1.85;
    margin: 0;
    padding: 0;
}

.reader-wrap {
    max-width: 680px;
    margin: 0 auto;
    padding: 48px 32px 80px;
}

/* Page separator */
.page-marker {
    font-family: 'Courier Prime', 'Courier New', Courier, monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    color: #b8a890;
    border-bottom: 1px solid #d8cfc0;
    margin: 40px 0 28px;
    padding-bottom: 8px;
}

.page-marker:first-child {
    margin-top: 0;
}

/* Body text */
p {
    margin: 0 0 18px 0;
    padding: 0;
    color: #2a2420;
    word-spacing: 0.03em;
}

/* Heading blocks */
h2 {
    font-family: 'Lora', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #1a0e00;
    margin: 32px 0 12px;
    padding: 0;
    line-height: 1.4;
}

h2.small {
    font-size: 18px;
}

/* THE KEY RULE: bionic bold anchors */
b, strong {
    font-weight: 700;
    color: #1a0e00;
}

/* Empty state */
.empty-state {
    color: #b8a890;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    text-align: center;
    margin-top: 80px;
}
"""

_HTML_SHELL = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,700;1,400&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
  <style>{css}</style>
</head>
<body>
  <div class="reader-wrap">
{body}
  </div>
</body>
</html>
"""


def render_html(pages: list[dict], title: str = "Document") -> str:
    """
    Generate a complete HTML document from extracted PDF pages.
    Each page's text is bionic-transformed.
    """
    body_lines: list[str] = []

    for page in pages:
        page_num = page["page_num"]

        # Page marker
        body_lines.append(
            f'    <div class="page-marker" id="page-{page_num}">'
            f'PAGE {page_num}'
            f'</div>'
        )

        for blk in page["blocks"]:
            raw_text: str = blk["text"]
            btype: str = blk["type"]
            transformed = transform_text(raw_text)

            if btype == "heading":
                # Use h2 size class based on length — very long headings are section labels
                cls = "small" if len(raw_text) > 80 else ""
                tag_open = f'<h2 class="{cls}">' if cls else "<h2>"
                body_lines.append(f"    {tag_open}{transformed}</h2>")
            else:
                body_lines.append(f"    <p>{transformed}</p>")

    body = "\n".join(body_lines)
    return _HTML_SHELL.format(title=_html_attr_escape(title), css=_CSS, body=body)


def render_empty_html() -> str:
    """Return placeholder HTML shown before any PDF is loaded."""
    body = '    <div class="empty-state">No document loaded.</div>'
    return _HTML_SHELL.format(title="Bionic Reader", css=_CSS, body=body)


def _html_attr_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
