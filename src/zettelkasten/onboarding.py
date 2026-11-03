"""First-run sample onboarding and per-user collection preference."""
from pathlib import Path
import json
from uuid import uuid4

PREFS_PATH = Path.home() / '.config' / 'personal-zettelkasten' / 'preferences.json'


def get_default_collection(prefs_path=None):
    path = Path(prefs_path) if prefs_path else PREFS_PATH
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        saved = data.get('collection')
        if isinstance(saved, str) and saved and Path(saved).expanduser().is_dir():
            return Path(saved).expanduser()
    except (OSError, ValueError, TypeError):
        pass
    return None


def save_default_collection(collection, prefs_path=None):
    path = Path(prefs_path) if prefs_path else PREFS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({'collection': str(Path(collection).expanduser().resolve())}, indent=2), encoding='utf-8')
    temp.replace(path)


def ensure_welcome(collection, notes_dir, inventory):
    """Only initialize a genuinely empty collection; never alter existing notes."""
    if inventory or any(notes_dir.glob('*.md')):
        return None
    # Don't regenerate an intro after the user deletes it or moves it to trash.
    marker = Path(collection) / '.welcome-initialized'
    if marker.exists():
        return None
    welcome = notes_dir / ('n_' + uuid4().hex + '.md')
    tutorial = notes_dir / ('n_' + uuid4().hex + '.md')
    welcome.write_text('---\ncategory: overview\n---\n\n# Start here\n\n'
        'Welcome to your personal Zettelkasten. This is an ordinary Markdown note: edit or unpin it whenever you like.\n\n'
        '## First steps\n\n'
        '1. Click **Idea** (Ctrl+Shift+I) and give your note a descriptive title.\n'
        '2. Type `[[` to link an existing note, or use **Linked note** (Ctrl+Shift+L) to branch into a new idea.\n'
        '3. Type `[@` to insert a citation after selecting your Better BibTeX export under File → Choose bibliography.\n'
        '4. Use the sidebar search, **Pinned**, and **Links to / Linked from** to find ideas again.\n'
        '5. Keep Zotero as the source of bibliographic records, PDFs and annotations; write your paper notes here.\n\n'
        f'## Tutorial\n\n[Reading to writing: worked example]({tutorial.name})\n\n'
        '## Keeping your work safe\n\nYour notes are Markdown files in `notes/`. '
        'Use independent backups of the entire collection; `recovery/` is not a substitute. '
        'Use Trash/Restore for accidental deletions.\n', encoding='utf-8')
    tutorial.write_text('---\ncategory: overview\n---\n\n# Reading to writing: worked example\n\n'
        'This fictional example demonstrates a workflow, not a published scientific finding.\n\n'
        '## 1. Paper note\n\nIn Zotero, read a paper and annotate its PDF. '
        'In the app, choose **References**, select a citation and create its associated Paper note. '
        'Record findings, methods, page numbers, and your own questions separately.\n\n'
        '## 2. Idea note\n\nA reusable insight might be: '
        '“Normalising measurements changes how comparisons should be interpreted.” '
        'Create an Idea note, explain the reasoning and limitations, cite the paper with `[@`, '
        'and link the Paper note using `[[`.\n\n'
        '## 3. Project note\n\nCreate a Project note for a manuscript or lecture. '
        'Link relevant Idea notes rather than copying all their contents. '
        'Archive the Project note when finished; keep reusable ideas available.\n\n'
        '## 4. Return later\n\nSearch by concept, select a cited source, '
        'or open a pinned Overview. Back/Forward retraces visited notes; '
        'it does not choose which connection to follow.\n', encoding='utf-8')
    marker.write_text('Created initial onboarding notes. Remove this marker only if you intentionally want first-run notes recreated in an empty collection.\n', encoding='utf-8')
    return welcome


def clear_default_collection(prefs_path=None):
    path = Path(prefs_path) if prefs_path else PREFS_PATH
    if path.exists():
        path.unlink()


def collection_is_valid(path):
    path = Path(path).expanduser()
    return path.is_dir() and (path / 'notes').is_dir()


def create_collection(parent, name):
    parent = Path(parent).expanduser()
    if not parent.is_dir():
        raise ValueError('The parent folder does not exist.')
    if not name or name.strip() != name or name in ('.', '..') or '/' in name or '\\' in name:
        raise ValueError('Enter a valid single folder name.')
    destination = parent / name
    if destination.exists():
        raise ValueError('A folder with this name already exists. Use Open Collection instead.')
    destination.mkdir()
    (destination / 'notes').mkdir()
    return destination
