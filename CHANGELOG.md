# Changelog

Notable changes to **My Zettelkasten**, listed from newest to oldest.

The application remains an experimental Linux pilot. See [ROADMAP.md](ROADMAP.md) for potential future improvements.

## Unreleased

Changes being developed for the next version will be documented here.

## v0.5.4 — Version information

- Added **Help → About My Zettelkasten**, showing the installed version, developer, and GitHub repository.
- Added the `--version` command-line option to display the installed version without opening the graphical interface.
- Both features retrieve the version from Python package metadata, keeping version reporting consistent.
- Added an automated test for command-line version reporting.

## v0.5.3 — Recent Collections and welcome screen

- Added **File → Recent Collections**, remembering up to 10 previously opened collections.
- Improved the welcome screen with New Collection, Open Collection, and a list of recent collections.
- Added double-click and keyboard support for opening recent collections from the welcome screen.
- Added **Clear Recent Collections**, which removes collection history without deleting notes or folders.
- Preserved recent-collection history when closing a collection, while clearing the automatic-reopen selection.
- Added warnings for unavailable collections, including missing or temporarily inaccessible Dropbox folders.
- Updated the *Start here* tutorial with instructions for managing collections.
- Added regression tests for recent-collection ordering, duplicate prevention, history limits, first-run behaviour, and missing folders.

## v0.5.2 — Collection management

- Added **File → New Collection**, allowing users to choose a parent folder and create a named collection.
- Added **File → Open Collection** for opening existing collections, including those stored on Dropbox.
- Added **File → Close Collection**, returning to the collection-selection window without exiting the application.
- Added a collection-selection window for first-time users or when no collection is open.
- Improved automatic reopening of the last-used collection.
- Removed automatic creation of a default collection when no valid collection is selected.
- Displayed the active collection name in the application title bar and its location in the bottom status bar.
- Preserved the `--collection` command-line option for explicitly selecting a collection.
- Added regression tests for collection creation, switching, first-run behaviour, and missing directories.

## v0.5.1 — GitHub documentation and packaging

- Expanded public README, with four application screenshots.
- Added MIT license, `.gitignore`, and curated roadmap.
- Added installation, quick-start, Zotero/Better BibTeX, shortcut, and backup guides.
- Updated package and window version labels; no intended workflow changes.
- Removed generated caches and packaging artifacts from release archive.

## v0.5.0

- First-run Start here and linked tutorial for **empty collections only**; pinned automatically.
- Remember last collection in per-user preferences; command-line override retained.
- Sidebar result counts; external HTTPS/Zotero link opening and missing-link warnings.
- Documentation for onboarding, backups, portability and pilot acceptance checks.
- Added onboarding and preference regression tests.

## v0.4.2

- Empty title templates, editor focus, and jump-to-new-linked-note navigation.

## v0.4.1

- Fixed single-click sidebar navigation and independent pinning.