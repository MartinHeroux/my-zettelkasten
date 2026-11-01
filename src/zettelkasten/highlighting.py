"""Conservative Markdown styling ranges. Does not modify the source text.

Ranges are Python string offsets [start, end). Intentionally a useful subset,
not a full CommonMark parser; excluded fenced code is treated literally.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    kind: str
    start: int
    end: int


HEADING = re.compile(r"^(#{1,6})[ \t]+.+$")
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
LINK = re.compile(r"!?\[[^\]\n]*\]\([^\n)]*\)")
CITATION = re.compile(r"\[@[^\]\n]+\]")
INLINE_CODE = re.compile(r"(?<!`)`[^`\n]+`(?!`)")
BOLD = re.compile(r"(?<!\\)(?<!\*)\*\*(?!\s).+?(?<!\s)\*\*(?!\*)")
ITALIC = re.compile(r"(?<!\\)(?<!\*)\*(?!\*|\s)[^*\n]+?(?<!\s)\*(?!\*)")


def spans(text: str) -> list[Span]:
    result: list[Span] = []
    offset = 0
    in_fence = False
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        marker = FENCE.match(content)
        if marker:
            token = marker.group(1)
            if not in_fence:
                in_fence = True
                fence_char, fence_length = token[0], len(token)
            elif token[0] == fence_char and len(token) >= fence_length:
                in_fence = False
            result.append(Span("codeblock", offset, offset + len(content)))
        elif in_fence:
            result.append(Span("codeblock", offset, offset + len(content)))
        else:
            head = HEADING.match(content)
            if head:
                result.append(Span(f"heading{len(head.group(1))}", offset, offset + len(content)))
            # Protect inline code from being styled as emphasis/links.
            code_ranges = [(m.start(), m.end()) for m in INLINE_CODE.finditer(content) if not _escaped(content, m.start())]
            for a, b in code_ranges:
                result.append(Span("inlinecode", offset + a, offset + b))
            for kind, regex in (("link", LINK), ("citation", CITATION), ("bold", BOLD), ("italic", ITALIC)):
                for match in regex.finditer(content):
                    if _escaped(content, match.start()):
                        continue
                    if any(match.start() < b and match.end() > a for a, b in code_ranges):
                        continue
                    result.append(Span(kind, offset + match.start(), offset + match.end()))
        offset += len(line)
    return result


def _escaped(s: str, at: int) -> bool:
    n = 0
    at -= 1
    while at >= 0 and s[at] == "\\":
        n += 1
        at -= 1
    return n % 2 == 1
