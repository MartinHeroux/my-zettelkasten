"""Read-only Better BibTeX reader. Supports nested braces, quoted values, comments,
string concatenation, and common BibTeX metadata. Never modifies exports.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

class BibError(ValueError):
    pass

@dataclass(frozen=True)
class Reference:
    key: str
    entry_type: str
    fields: dict[str, str]

    def field(self, name: str) -> str:
        return self.fields.get(name, '')

    @property
    def title(self):
        return plain(self.field('title'))

    @property
    def authors(self):
        return plain(self.field('author'))

    @property
    def year(self):
        return plain(self.field('year') or self.field('date')[:4])

    @property
    def search_text(self):
        return ' '.join((self.key, self.title, self.authors, self.year, plain(self.field('journal')), plain(self.field('booktitle')))).casefold()

    def display(self):
        return f'{self.authors or "Unknown author"} ({self.year or "n.d."}). {self.title or "Untitled"}'

    def full_reference(self):
        parts = [self.display().rstrip('.') + '.']
        venue = plain(self.field('journal') or self.field('journaltitle') or self.field('booktitle') or self.field('publisher'))
        volume = plain(self.field('volume'))
        issue = plain(self.field('number') or self.field('issue'))
        pages = plain(self.field('pages')).replace('--', '–')
        detail = venue
        if volume: detail += (', ' if detail else '') + volume
        if issue: detail += f'({issue})'
        if pages: detail += (', ' if detail else '') + pages
        if detail: parts.append(detail.rstrip('.') + '.')
        if self.field('doi'): parts.append('DOI: ' + plain(self.field('doi')))
        elif self.field('url'): parts.append('URL: ' + plain(self.field('url')))
        return ' '.join(parts)

# BibTeX's doubled braces protect capitalization; strip braces only for display.
def plain(value: str) -> str:
    value = value.replace('\\&', '&').replace('\\_', '_').replace('\\%', '%')
    value = re.sub(r'\\(?:textbf|emph|textit|textsc|mathrm|textnormal)\s*\{([^{}]*)\}', r'\1', value)
    value = value.replace('\\~', ' ').replace('~', ' ')
    return re.sub(r'\s+', ' ', value.replace('{', '').replace('}', '')).strip()

class Parser:
    def __init__(self, source: str):
        self.s = source
        self.i = 0
        self.n = len(source)

    def ws(self):
        while self.i < self.n and (self.s[self.i].isspace() or self.s[self.i] == '%'):
            if self.s[self.i] == '%':
                while self.i < self.n and self.s[self.i] != '\n': self.i += 1
            else: self.i += 1

    def value(self):
        self.ws()
        if self.i >= self.n: raise BibError('Unexpected end of bibliography')
        opening = self.s[self.i]
        if opening in '{"':
            self.i += 1
            depth = 1
            out = []
            while self.i < self.n:
                c = self.s[self.i]
                if c == '\\' and self.i + 1 < self.n:
                    out.extend((c, self.s[self.i+1])); self.i += 2; continue
                if opening == '{':
                    if c == '{': depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            self.i += 1; return ''.join(out)
                elif c == '"' and depth == 1:
                    self.i += 1; return ''.join(out)
                out.append(c); self.i += 1
            raise BibError('Unterminated BibTeX value')
        start = self.i
        while self.i < self.n and self.s[self.i] not in ',}#\n\r\t ':
            self.i += 1
        if start == self.i: raise BibError('Empty BibTeX value')
        return self.s[start:self.i]

    def parse(self):
        refs = {}
        while self.i < self.n:
            at = self.s.find('@', self.i)
            if at < 0: break
            self.i = at + 1
            match = re.match(r'[A-Za-z]+', self.s[self.i:])
            if not match: continue
            kind = match.group().lower(); self.i += len(match.group())
            self.ws()
            if self.i >= self.n or self.s[self.i] not in '{(': continue
            opener = self.s[self.i]; closer = '}' if opener == '{' else ')'
            self.i += 1
            if kind in {'comment', 'preamble', 'string'}:
                # These blocks are not references. Consume to their closing delimiter.
                depth = 1
                while self.i < self.n and depth:
                    if self.s[self.i] == opener: depth += 1
                    elif self.s[self.i] == closer: depth -= 1
                    self.i += 1
                continue
            start = self.i
            while self.i < self.n and self.s[self.i] not in ',' + closer: self.i += 1
            key = self.s[start:self.i].strip()
            if not key: raise BibError('Entry has no citation key')
            if self.i >= self.n or self.s[self.i] != ',': raise BibError('Missing comma after key ' + key)
            self.i += 1
            fields = {}
            while True:
                self.ws()
                if self.i >= self.n: raise BibError('Unterminated entry ' + key)
                if self.s[self.i] == closer:
                    self.i += 1; break
                if self.s[self.i] == ',': self.i += 1; continue
                name = re.match(r'[A-Za-z_][A-Za-z_0-9-]*', self.s[self.i:])
                if not name: raise BibError('Malformed field in ' + key)
                field = name.group().lower(); self.i += len(name.group()); self.ws()
                if self.i >= self.n or self.s[self.i] != '=': raise BibError('Missing = in ' + key)
                self.i += 1
                pieces = [self.value()]
                self.ws()
                while self.i < self.n and self.s[self.i] == '#':
                    self.i += 1; pieces.append(self.value()); self.ws()
                fields[field] = ''.join(pieces)
                if self.i < self.n and self.s[self.i] == ',': self.i += 1
            if key in refs: raise BibError('Duplicate citation key: ' + key)
            refs[key] = Reference(key, kind, fields)
        if '@' in self.s and not refs: raise BibError('No valid bibliography entries')
        return refs

def parse_bib(text: str) -> dict[str, Reference]:
    return Parser(text).parse()

def read_bib(path: Path) -> dict[str, Reference]:
    return parse_bib(path.read_text(encoding='utf-8-sig'))
