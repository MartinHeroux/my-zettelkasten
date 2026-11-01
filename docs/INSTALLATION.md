# Installation and first launch

## Supported environment

The current pilot is tested on **Linux Mint 22.3 / Python 3.12.3**. It requires Python 3.10+ and Tkinter. Other operating systems are unverified.

```bash
sudo apt update
sudo apt install python3 python3-tk python3-venv
```

In the extracted project directory (where `pyproject.toml` is located):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m zettelkasten --collection ~/Zettelkasten-Test
```

`~/Zettelkasten-Test` is a disposable collection for evaluation. For a new, empty collection the application creates a pinned **Start here** note. Use `python -m zettelkasten` on later launches to reopen the last collection. You can override the selection at any time with `--collection /path/to/another-collection`.

## Concepts

A **collection** is a directory of notes, attachments, and settings, not a subject folder. It is separate from the Python application. The selected bibliography path is stored in the collection's `settings.json`; last-used collection preference is stored under `~/.config/personal-zettelkasten/preferences.json`.

## Common problems

- `No module named tkinter`: install `python3-tk` using your package manager.
- `No module named zettelkasten`: activate the venv and rerun `python -m pip install -e .` in the project root.
- No display / `$DISPLAY` missing: start from a graphical desktop session. Automated GUI checks can use Xvfb.
- Empty bibliography: follow [Zotero setup](ZOTERO_SETUP.md); the bundled sample contains only fictional references.

Do not store your only copy of valuable notes in the project source folder or in the sample collection. See [Backups](BACKUP_AND_RECOVERY.md).
