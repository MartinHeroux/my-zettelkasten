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

## Restoring mistakes

- Use **Note → Move to Trash** and **Restore from Trash** for main notes.
- **Discard** permanently removes a fleeting note and its recovery copies after confirmation. It cannot be restored through the app; independent backups or sync history may still hold older copies. The developed Permanent note is a separate file and remains intact.
- **Develop** keeps the fleeting original in Inbox until you explicitly discard it.
- Using Move to Trash on a fleeting note still moves it to collection Trash; restoring such a note currently puts it in `notes/`, not Inbox.
- Use project archiving to hide completed project notes without deleting them.
- For external-edit conflicts, preserve both versions rather than forcing an overwrite.
- Recovery copies can help after some accidental changes, but their retention is bounded; check them before cleaning them out.

Do not overwrite your only good copy during a restore. Test restores into a separate directory first.
