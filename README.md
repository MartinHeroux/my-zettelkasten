<p align="center">
  <img src="assets/branding/logo-banner.svg"
       alt="My Zettelkasten"
       width="700">
</p>

A lightweight, local-first Markdown note editor for **connecting ideas, papers, and projects**. Built with Python and Tkinter, inspired by the Zettelkasten workflow discussed in Sönke Ahrens’s *How to Take Smart Notes*.

**Version 0.5.3 — experimental Linux pilot.** Tested by the project author on Linux Mint; other platforms are not yet verified. Back up your notes independently before relying on the application for important work.

![My Zettelkasten main window showing notes, editor, and links](screenshots/main_app.png)

## Why this application?

Write notes in ordinary `.md` files, follow relationships between ideas, and retrieve useful thoughts later. The collection is readable without this program. The application is deliberately modest: it does not replace Zotero, a PDF reader, or a manuscript editor.

### Features

- Markdown editor with **visible syntax** and live styling for headings, emphasis, links, code, and citations.
- Idea, Paper, Overview, and Project notes with simple templates; stable note filenames.
- Fast `[[` note linking, backlinks, searchable inventory, pinned notes, and browser-style Back/Forward history.
- `[@` citation autocomplete using a **read-only** Better BibTeX export from Zotero.
- Create or reopen Paper notes from bibliography entries; attach figures and PDFs as copied local files.
- Autosave, recovery copies, recoverable deletion, project archiving, and external-edit conflict warnings.
- An editable, pinned **Start here** tutorial for newly created empty collections.

## What's New in v0.5.3 — Recent Collections and Welcome Screen

My Zettelkasten v0.5.3 improves collection navigation and the first-run experience.

### New features

- **Recent Collections:** Access up to 10 previously opened collections from File → Recent Collections.
- **Improved welcome screen:** Create a new collection, open an existing collection, or select a recently used collection.
- **Automatic reopening:** The last-used collection opens automatically when restarting the application.
- **Collection history:** Recently opened collections remain available after closing a collection.
- **Dropbox support:** Collections stored in Dropbox or other external directories can be opened without command-line arguments.
- **Missing collections:** Unavailable collection folders produce a warning without deleting their history.
- **Clear Recent Collections:** Remove collection history without affecting notes or collection folders.
- **Updated onboarding:** The Start Here note now explains how to manage collections.

### Compatibility

Existing collections remain compatible. No migration or changes to note files are required.

## Installation (Linux Mint / Ubuntu)

Requires **Python 3.10+**, Tkinter and Python virtual-environment support. On Mint/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-tk python3-venv
```

Download and extract the source ZIP (or clone the repository), open a terminal in the directory containing `pyproject.toml`, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m zettelkasten --collection ~/Zettelkasten-Test
```

The first run with a new empty collection creates a pinned **Start here** note and a linked tutorial. Once a collection is selected, launch it again with `python -m zettelkasten` (or `zettelkasten`). Use a disposable collection while learning. See [full installation instructions](docs/INSTALLATION.md).

## First five minutes

1. Open the pinned **Start here** note and follow its links.
2. Click **Idea** or press `Ctrl+Shift+I`; type your title after `# `.
3. Type `[[` to search and insert a link to another note; `Ctrl+Shift+L` creates and opens a new linked Idea note.
4. Use the left search field, Pinned and Recent to find notes; use **Links to** and **Linked from** to explore relationships.
5. Optionally connect Zotero via **File → Choose bibliography**, then type `[@` to insert a citation.

Read [Quick start](docs/QUICK_START.md) and [Keyboard shortcuts](docs/KEYBOARD_SHORTCUTS.md).

## Zotero + Better BibTeX

Zotero manages references, PDFs, and PDF annotations. This application manages your Markdown Paper and Idea notes. The connection is a `.bib` file that Better BibTeX can **automatically re-export** when the Zotero library changes; the app reads that file and remembers its path for the collection. **It does not modify Zotero or synchronize Zotero notes.**

To set up: install [Zotero](https://www.zotero.org/), install [Better BibTeX](https://retorque.re/zotero-better-bibtex/), right-click **My Library → Export Library**, choose **Better BibTeX**, enable **Keep updated**, and save to a stable location. In this app, use **File → Choose bibliography**. Verify with `[@` and the **References** window.

For exact steps, export verification, and troubleshooting, read **[Zotero and Better BibTeX setup](docs/ZOTERO_SETUP.md)**.

| Note linking (`[[`) | Zotero citation completion (`[@`) |
|:--:|:--:|
| ![Note link suggestions](screenshots/quick_linking_notes.png) | ![Citation suggestions from a bibliography](screenshots/reference_papers_in_zotero_via_bib.png) |

**Paper-note template** — headings are prefilled so you can start with the title:

![Paper note with headings](screenshots/paper_note_auto_headings.png)

## Where are my notes?

A **collection** is a directory containing `notes/` (Markdown), `attachments/` (copied files), `settings.json`, and recovery/trash folders. The optional bibliography may live inside or outside the collection. Your code and Python environment are separate from your collection. Keep backups of the entire collection, and back up Zotero separately. [Backup and recovery](docs/BACKUP_AND_RECOVERY.md).

## Status and limitations

This is a **pilot**, not a data-loss guarantee. It has been tested on Linux Mint, but broad multi-user, cross-platform, and large-library testing is incomplete. It has no automatic Zotero-note synchronization, no rendered WYSIWYG editor, and no mobile app. Attached files are **copied** into the collection. The bibliography export is **read-only**. Please test with disposable notes first and report issues with reproduction steps.

## Future improvements

We keep a curated [ROADMAP.md](ROADMAP.md) of possible improvements (ideas are **not promises**). Examples include clipboard image paste, linking existing files without copying, improved Zotero item links, and optional Markdown preview. Contributions and bug reports can be discussed in GitHub Issues once a repository is published.

## Documentation and development

- [Installation](docs/INSTALLATION.md) · [Quick start](docs/QUICK_START.md) · [Zotero setup](docs/ZOTERO_SETUP.md)
- [Keyboard shortcuts](docs/KEYBOARD_SHORTCUTS.md) · [Backups](docs/BACKUP_AND_RECOVERY.md)
- [Pilot checklist](docs/PILOT_CHECKLIST.md) · [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md)

Run the unit tests from the project root:

```bash
python -m unittest discover -s tests -v
```

Tkinter GUI smoke tests can run on a Linux desktop or with `xvfb-run -a python tests/gui_smoke.py` (install `xvfb` if needed). Tests are useful but do not replace manual testing on your desktop.

## License

[MIT](LICENSE). This project is independent of Zotero, Better BibTeX, and the author/publisher of *How to Take Smart Notes*.
