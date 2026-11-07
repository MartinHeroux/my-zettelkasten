"""First-run sample onboarding and per-user collection preference."""
from pathlib import Path
import json
from uuid import uuid4

PREFS_PATH = Path.home() / '.config' / 'personal-zettelkasten' / 'preferences.json'


MAX_RECENT_COLLECTIONS = 10


def _read_preferences(prefs_path=None):
    path = Path(prefs_path) if prefs_path else PREFS_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_preferences(data, prefs_path=None):
    path = Path(prefs_path) if prefs_path else PREFS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )
    temp.replace(path)


def get_default_collection(prefs_path=None):
    data = _read_preferences(prefs_path)
    saved = data.get("collection")
    if isinstance(saved, str) and saved:
        collection = Path(saved).expanduser()
        if collection_is_valid(collection):
            return collection
    return None


def get_recent_collections(prefs_path=None):
    data = _read_preferences(prefs_path)
    recent = data.get("recent_collections", [])
    if not isinstance(recent, list):
        return []

    result = []
    for item in recent:
        if isinstance(item, str) and item and collection_is_valid(item) and item not in result:
            result.append(item)
        if len(result) >= MAX_RECENT_COLLECTIONS:
            break
    return result


def save_default_collection(collection, prefs_path=None):
    data = _read_preferences(prefs_path)
    location = str(Path(collection).expanduser().resolve())

    data["collection"] = location
    recent = get_recent_collections(prefs_path)
    data["recent_collections"] = (
        [location] + [p for p in recent if p != location]
    )[:MAX_RECENT_COLLECTIONS]

    _write_preferences(data, prefs_path)


def clear_recent_collections(prefs_path=None):
    data = _read_preferences(prefs_path)
    data["recent_collections"] = []
    _write_preferences(data, prefs_path)


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
        '## Fleeting Inbox\n\n'
        'Capture a thought with Ctrl+Shift+N or New Note → Fleeting Note. Open Inbox to revisit it. '
        'Develop saves and opens a Permanent note, then permanently deletes the fleeting original and its recovery copies. '
        'For thoughts you do not develop, use Note → Move to Trash, or Note → Delete Permanently. Permanent deletion removes the note '
        'and its recovery copies, bypassing Trash; developed notes remain.\n\n'
        '## First steps\n\n'
        '1. Choose **New Note → Permanent Note** (Ctrl+Shift+I) and give your note a descriptive title.\n'
        '2. Type `[[` to link an existing note, or use **Linked note** (Ctrl+Shift+L) to branch into a new idea.\n'
        '3. Type `[@` to search citation keys and insert only `[@key]` after selecting your Better BibTeX export under Navigate → Choose Bibliography.\n'
        '4. Use the sidebar search, **Pinned**, and **Links to / Linked from** to find ideas again.\n'
        '5. Keep Zotero as the source of bibliographic records, PDFs and annotations; keep literature notes in Zotero and develop connected ideas here.\n\n'
        f'## Tutorial\n\n[Reading to writing: worked example]({tutorial.name})\n\n'
        '## Managing collections\n\n'
       'A collection is a folder containing your notes and associated files.\n\n'
       '- **New Collection:** Use File → New Collection to choose a parent folder and name a new collection.\n'
       '- **Open Collection:** Use File → Open Collection to select an existing collection, including one on Dropbox.\n'
       '- **Recent Collections:** Use File → Recent Collections to reopen a previously used collection.\n'
       '- **Close Collection:** Use File → Close Collection to return to the welcome screen without deleting any notes.\n\n'
       'When you quit with a collection open, My Zettelkasten remembers it for next time. '
       'If you close the collection first, the next launch shows the collection-selection screen instead.\n\n'
       '## Keeping your work safe\n\nYour notes are Markdown files in `notes/`. '
        'Use independent backups of the entire collection; `recovery/` is not a substitute. '
        'Use Note → Move to Trash / Restore from Trash for main notes. Note → Delete Permanently also removes recovery copies.\n', encoding='utf-8')
    tutorial.write_text('---\ncategory: overview\n---\n\n# Reading to writing: worked example\n\n'
        'This fictional example demonstrates a workflow, not a published scientific finding.\n\n'
        '## 1. Literature note\n\nIn Zotero, read a paper and annotate its PDF. '
        'Write a literature note attached to the reference in Zotero. '
        'Record findings, methods, page numbers, and your own questions separately.\n\n'
        '## 2. Permanent note\n\nA reusable insight might be: '
        '“Normalising measurements changes how comparisons should be interpreted.” '
        'Create an Permanent note, explain the reasoning and limitations, cite the paper with `[@`, '
        'and link related ideas using `[[`.\n\n'
        '## 3. Project note\n\nCreate a Project note for a manuscript or lecture. '
        'Link relevant Permanent notes rather than copying all their contents. '
        'Archive the Project note when finished; keep reusable ideas available.\n\n'
        '## 4. Return later\n\nSearch by concept, select a cited source, '
        'or open a pinned Entry-Point note. Back/Forward retraces visited notes; '
        'it does not choose which connection to follow.\n', encoding='utf-8')
    marker.write_text('Created initial onboarding notes. Remove this marker only if you intentionally want first-run notes recreated in an empty collection.\n', encoding='utf-8')
    return welcome


def clear_default_collection(prefs_path=None):
    data = _read_preferences(prefs_path)
    data.pop("collection", None)
    _write_preferences(data, prefs_path)


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
