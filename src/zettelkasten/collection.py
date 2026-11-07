"""Portable note indexing, templates, and link handling (no database)."""
from __future__ import annotations
import re
import shutil
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from urllib.parse import unquote

LINK_RE = re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+\.md)(?:#[^)]*)?\)')
FENCE_RE = re.compile(r'^\s*(```|~~~)')


def title_of(text: str, fallback: str = 'Untitled') -> str:
    match = re.search(r'^#\s+(.+)$', text, re.M)
    return match.group(1).strip() if match else fallback


def category_of(text: str) -> str:
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    if match:
        field = re.search(r'^category:\s*([\w-]+)', match.group(1), re.M)
        if field:
            value = field.group(1).lower()
            return 'uncategorised' if value in {'paper', 'literature'} else value
    return 'uncategorised'


def template(category: str = 'idea', title: str = '') -> str:
    category = category.lower()
    if category not in {'idea','overview','project','inbox'}:
        raise ValueError('Invalid note category')
    headings = {
        'overview': '\n## Entry points\n',
        'project': '\n## Working question\n\n## Outline and decisions\n\n## Open questions\n',
        'inbox': '\n',
        'idea': '\n',
    }
    return f'---\ncategory: {category}\n---\n\n# {title}\n' + headings[category] + '\n'


def update_placeholder_links(notes_dir: Path, target: Path, text: str, recovery_dir: Path) -> list[str]:
    """Resolve generated link labels after a target gets its first H1 title.

    Keep custom labels and code examples intact. Use normal conflict detection
    and recovery copies for every source changed; return failures to the UI.
    """
    from .storage import ExternalChangeError, load_note, save_note

    heading = re.search(r'^#[ \t]+([^\r\n]+)', text, re.M)
    if not heading or not heading.group(1).strip():
        return []
    title = heading.group(1).strip()
    label = title.replace('\\', '\\\\').replace('[', r'\[').replace(']', r'\]')
    pattern = re.compile(r'(?<!!)(?<!\\)\[(?:New linked idea|New Linked Note)\]\(([^)]+)\)')
    failures = []
    for source in notes_dir.glob('*.md'):
        if source.resolve() == target.resolve():
            continue
        try:
            original, digest = load_note(source)
            fenced = False
            lines = []
            def replace(match):
                dest = unquote(match.group(1).split('#', 1)[0])
                if '://' in dest or (source.parent / dest).resolve() != target.resolve():
                    return match.group(0)
                return f'[{label}]({match.group(1)})'
            for line in original.splitlines(keepends=True):
                if FENCE_RE.match(line):
                    fenced = not fenced
                    lines.append(line)
                elif fenced:
                    lines.append(line)
                else:
                    # Split out inline code so examples remain literal.
                    parts = re.split(r'(`+[^`]*`+)', line)
                    lines.append(''.join(part if part.startswith('`') else pattern.sub(replace, part)
                                         for part in parts))
            updated = ''.join(lines)
            if updated != original:
                save_note(source, updated, digest, recovery_dir)
        except (OSError, UnicodeError, ExternalChangeError):
            failures.append(source.name)
    return failures


def source_key_of(text: str) -> str | None:
    import json
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not match:
        return None
    field = re.search(r'^source_key:\s*(.+?)\s*$', match.group(1), re.M)
    if not field:
        return None
    raw = field.group(1)
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except ValueError:
            return None
    return raw.strip("'\"")


def targets(text: str, source: Path, notes_dir: Path) -> set[Path]:
    """Only local links within notes_dir; ignore fenced code and inline code."""
    cleaned = []
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            cleaned.append(re.sub(r'`[^`\n]*`', '', line))
    result = set()
    root = notes_dir.resolve()
    for match in LINK_RE.finditer('\n'.join(cleaned)):
        dest = unquote(match.group(1).split('?', 1)[0])
        if '://' in dest or dest.startswith('/'):
            continue
        path = (source.parent / dest).resolve()
        if path.parent == root and path.suffix.lower() == '.md':
            result.add(path)
    return result


def scan(notes_dir: Path) -> list[dict]:
    result = []
    for path in sorted(notes_dir.glob('*.md')):
        try:
            text = path.read_text(encoding='utf-8-sig')
            result.append({'path': path.resolve(), 'title': title_of(text, path.stem),
                           'category': category_of(text), 'source_key': source_key_of(text), 'archived': archived_of(text), 'content': text,
                           'modified': path.stat().st_mtime,
                           'targets': targets(text, path, notes_dir)})
        except (OSError, UnicodeError):
            continue
    return result


def link_for(source: Path, dest: Path, label: str) -> str:
    if source.parent.resolve() != dest.parent.resolve():
        raise ValueError('Cross-collection note links are not supported')
    return f'[{label}]({dest.name})'


def trash_note(path: Path, trash_dir: Path) -> Path:
    trash_dir.mkdir(parents=True, exist_ok=True)
    target = trash_dir / path.name
    if target.exists():
        target = trash_dir / f'{path.stem}.{uuid4().hex[:8]}.md'
    shutil.move(str(path), str(target))
    return target


def archived_of(text: str) -> bool:
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    return bool(match and re.search(r'^archived:\s*true\s*$', match.group(1), re.M | re.I))


def set_archived(text: str, archived: bool) -> str:
    match = re.match(r'\A(---\s*\n)(.*?)(\n---\s*\n)', text, re.S)
    if not match:
        return text
    metadata = re.sub(r'^archived:.*(?:\n|$)', '', match.group(2), flags=re.M).rstrip('\n')
    if archived:
        metadata += '\narchived: true'
    return match.group(1) + metadata + match.group(3) + text[match.end():]
