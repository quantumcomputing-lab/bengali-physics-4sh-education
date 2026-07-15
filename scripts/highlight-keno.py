#!/usr/bin/env python3
"""
Standing rule: any full sentence containing BOTH the standalone Bengali
word কেন ("why") AND a question mark gets wrapped in
<strong class="q-why">...</strong> so it renders bold + dark blue (see
.q-why in css/style.css).

কেন alone is not enough — it's also used idiomatically/declaratively
without asking a question, e.g. "যত জোরেই হোক না কেন" ("no matter how
hard") or "Friction কেন হয়, সেটা আমরা জানি।" (declarative, ends in ।).
Only sentences that are actually asking "why...?" get bolded.

Fully re-derives the wrapping on every run (first strips any existing
<strong class="q-why"> wraps, then reapplies from current rules), so
it's safe to re-run after both adding new chapters AND after changing
this rule itself. Only touches <p>...</p> blocks that contain Bengali
script text; everything else (English paragraphs, nav, footer,
JSON-LD) is left untouched.

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

EXISTING_WRAP = re.compile(r'<strong class="q-why">(.*?)</strong>', re.S)


def should_highlight(sentence: str) -> bool:
    return bool(KENO.search(sentence)) and "?" in sentence


def highlight_sentence(sentence: str) -> str:
    if not should_highlight(sentence):
        return sentence
    # Split off trailing whitespace so the wrap hugs the punctuation, not the newline.
    stripped = sentence.rstrip()
    trailing_ws = sentence[len(stripped):]
    return f'<strong class="q-why">{stripped}</strong>{trailing_ws}'


def process_paragraph_text(text: str) -> str:
    # Always unwrap first so a rule change (or a sentence edit) is
    # correctly reflected rather than left stale from a previous run.
    text = EXISTING_WRAP.sub(lambda m: m.group(1), text)
    if not HAS_BENGALI.search(text) or not KENO.search(text):
        return text
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
