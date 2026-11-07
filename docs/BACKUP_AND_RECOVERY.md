# Backups, recovery and portability

## Before using important notes

Start with a **disposable test collection** and complete [PILOT_CHECKLIST.md](PILOT_CHECKLIST.md). The application uses autosave, recovery copies and conflict detection, but none guarantees protection from every data-loss scenario.

## Back up the entire collection

Your collection contains `notes/` main Markdown files, `inbox/` fleeting notes, `attachments/`, `settings.json`, and recovery/trash folders. Back up the **whole collection** to an independent location (for example an external disk or versioned backup service), and periodically **test restoring** a copy. If the bibliography is stored outside the collection, back up that configuration/source separately as appropriate.

The application's code and Python virtual environment are replaceable; your notes are not. Do not rely only on the `recovery/` directory, as it may reside on the same failing disk.

## Zotero is separate

The Better BibTeX `.bib` export is **not** a complete Zotero backup. Back up Zotero's data directory using Zotero's documented procedure. Do **not** place Zotero's live database into an ordinary cloud-synced directory. Linked PDFs stored in Dropbox need their own backup/sync plan.

## Moving or synchronizing notes

Relative links between Markdown notes and copied attachments should survive moving the **entire collection**. If the bibliography is configured with an external absolute path, reselect it after moving computers. If you sync the collection with Dropbox or another service, avoid editing the same files on two machines at once and let synchronization finish before switching devices. Independent backups remain essential.

## Recovery, Trash and Archive

`recovery/` is saved editing history, not discarded notes. Each changed save (including autosave) copies the previous on-disk version here. Up to ten versions per note are retained, so ten edited notes can produce 100 files. Explicitly preserved unsaved conflict copies may also be present. Recovery files are not listed as active notes. To recover a version, close the app, copy the current note somewhere safe, then copy the selected recovery contents into its original note file in `notes/` or `inbox/`.

- **Note → Move to Trash** moves the note into `trash/` and retains recovery history. **Restore from Trash** restores it without overwriting an existing file. Fleeting notes trashed in this version return to Inbox; older Trash files without Inbox provenance return to notes.
- **Note → Delete Permanently** deletes the open note and its local recovery copies after confirmation. It bypasses Trash; independent backups or Dropbox history may retain copies. Attached files and other notes are not deleted. Use the file manager to remove files already in Trash if needed.
- **Develop** creates a separate Permanent note and leaves the original in Inbox.
- **Note → Archive / Unarchive** marks project notes as archived. Save the change; Archived lists them and unarchiving returns them to normal lists. Their files and links remain intact.

Do not overwrite your only good copy during recovery. Back up the whole collection independently.
