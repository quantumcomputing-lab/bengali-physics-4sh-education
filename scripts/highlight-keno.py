#!/usr/bin/env python3
"""
Standing rule: any full sentence containing the standalone Bengali word
কেন ("why") gets wrapped in <strong class="q-why">...</strong> so it
renders bold + dark blue (see .q-why in css/style.css).

Idempotent — safe to re-run after adding new chapters. Only touches
<p>...</p> blocks that contain Bengali script text; everything else
(English paragraphs, nav, footer, JSON-LD) is left untouched.

Usage: python3 scripts/highlight-keno.py
"""
import re
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"

BENGALI_RANGE = r"ঀ-৿"
HAS_BENGALI = re.compile(f"[{BENGALI_RANGE}]")

# Standalone কেন — not preceded/followed by another Bengali letter, so
# words like কেননা ("because") are correctly excluded.
KENO = re.compile(f"(?<![{BENGALI_RANGE}])কেন(?![{BENGALI_RANGE}])")

# One sentence = text up to and including its sentence-final punctuation
# (Bengali দাঁড়ি । or ? or ! — possibly repeated, e.g. কেন???), plus any
# trailing whitespace/newline so original formatting is preserved exactly.
SENTENCE = re.compile(r"[^।?!]+[।?!]+\s*")

# Matches a whole <p ...>...</p> block, non-greedy, across newlines.
P_TAG = re.compile(r"(<p(?:\s+[^>]*)?>)(.*?)(</p>)", re.S)

ALREADY_WRAPPED = re.compile(r'<strong class="q-why">')


def highlight_sentence(sentence: str) -> str:
    if not KENO.search(sentence):
        return sentence
    # Split off trailing whitespace so the wrap hugs the punctuation, not the newline.
    stripped = sentence.rstrip()
    trailing_ws = sentence[len(stripped):]
    return f'<strong class="q-why">{stripped}</strong>{trailing_ws}'


def process_paragraph_text(text: str) -> str:
    if not HAS_BENGALI.search(text) or not KENO.search(text):
        return text
    if ALREADY_WRAPPED.search(text):
        return text  # idempotent: skip paragraphs already processed
    return SENTENCE.sub(lambda m: highlight_sentence(m.group(0)), text)


def process(html: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        new_inner = process_paragraph_text(inner)
        if new_inner != inner:
            count += 1
        return f"{open_tag}{new_inner}{close_tag}"

    return P_TAG.sub(repl, html), count


def main():
    html = INDEX.read_text(encoding="utf-8")
    new_html, count = process(html)
    if new_html != html:
        INDEX.write_text(new_html, encoding="utf-8")
    print(f"Processed. Paragraphs modified: {count}")


if __name__ == "__main__":
    main()
