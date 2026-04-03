"""
bionic.py — Core Bionic Reading transform engine.

Rules (per spec):
  1–3 chars  → bold full word
  4–5 chars  → bold first 2
  6–9 chars  → bold first 3
  10+ chars  → bold first 4

Punctuation and whitespace are preserved exactly.
"""

import re

# Pre-compiled pattern: split a token into (leading_punct, word_core, trailing_punct)
_WORD_RE = re.compile(r'^([^A-Za-z0-9]*)([A-Za-z0-9]+)([^A-Za-z0-9]*)$')
# Whitespace splitter (keeps the whitespace tokens)
_SPLIT_RE = re.compile(r'(\s+)')


def _bold_length(n: int) -> int:
    """Return how many characters to bold for a word of length n."""
    if n <= 3:
        return n
    if n <= 5:
        return 2
    if n <= 9:
        return 3
    return 4


def _transform_token(token: str) -> str:
    """
    Apply bionic transform to a single non-whitespace token.
    Handles tokens like: "word", "word.", "(word)", "word's", "123", etc.
    """
    m = _WORD_RE.match(token)
    if not m:
        # Pure punctuation / symbol — return as-is (escaped for HTML)
        return _html_escape(token)

    lead = m.group(1)
    core = m.group(2)
    trail = m.group(3)

    n = len(core)
    cut = _bold_length(n)
    bold_part = core[:cut]
    rest_part = core[cut:]

    # Build HTML: escape each fragment individually
    parts = [
        _html_escape(lead),
        f'<b>{_html_escape(bold_part)}</b>',
        _html_escape(rest_part),
        _html_escape(trail),
    ]
    return ''.join(parts)


def _html_escape(s: str) -> str:
    """Minimal HTML escaping for text content (not attributes)."""
    return (
        s.replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
    )


def transform_text(text: str) -> str:
    """
    Apply Bionic Reading transform to an arbitrary string.
    Returns HTML fragment with <b> tags around bold portions.
    Whitespace runs (spaces, newlines) are preserved as-is (space chars in HTML).
    """
    tokens = _SPLIT_RE.split(text)
    parts = []
    for token in tokens:
        if not token:
            continue
        if _SPLIT_RE.match(token):
            # Whitespace — preserve spaces, collapse newlines to space within a block
            parts.append(' ' if '\n' in token else token)
        else:
            parts.append(_transform_token(token))
    return ''.join(parts)
