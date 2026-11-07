# Connect Zotero using Better BibTeX

This guide connects a **local, automatically updated `.bib` export** to Personal Zettelkasten. Zotero manages source records, PDFs, and annotations; the app reads bibliographic metadata for citation completion. The app does **not** write to Zotero or import its notes automatically.

## 1. Install the tools

1. Install [Zotero](https://www.zotero.org/download/).
2. Install the [Better BibTeX for Zotero](https://retorque.re/zotero-better-bibtex/) add-on using its official instructions and a release compatible with your Zotero version.
3. Restart Zotero if the add-on installation requests it. Confirm that **Better BibTeX** appears among available export formats.

## 2. Create a continuously updated export

1. In Zotero's left pane, right-click **My Library** (or a collection, if you want only part of the library).
2. Choose **Export Library…** (or **Export Collection…**).
3. In **Format**, select **Better BibTeX** rather than the built-in BibTeX exporter.
4. Check **Keep updated** (wording may vary by plugin version).
5. Save as a `.bib` file in a stable, locally accessible location, for example `~/Documents/Zettelkasten/references/library.bib`.

This is Better BibTeX's **automatic export**, not the application's Markdown autosave. Keep the export file in place and let Better BibTeX manage its contents; **do not edit the generated `.bib` file by hand**. If your library is in Dropbox, ensure the export is locally available before launching the app.

## 3. Point Personal Zettelkasten to the export

1. Open the application and your intended collection.
2. Select **Navigate → Choose Bibliography** and choose the exported `.bib` file.
3. In a note, type `[@` and check that citation suggestions appear.
4. In a note, type `[@` and part of an author name, title, year or citation key. Suggestions show citation keys only; search still matches authors, titles, years and keys. Select with arrows and Enter to insert `[@key]` without reference text.
5. Write literature notes directly in Zotero, attached to their references.

The chosen bibliography path is saved in the **collection settings**, so it should persist across application sessions. Different collections can point to different exports. The app reloads the bibliography when reference features are accessed and a change is detected; it does not continuously watch the file in the background.

## 4. Verify updates

1. Open the `.bib` file in a text editor (read-only, if possible) and note a known reference.
2. Add a test reference in Zotero or change a nonessential field of an existing test entry.
3. Allow Better BibTeX a moment to update its export, then reopen/reload the `.bib` file to confirm the change appeared.
4. Trigger `[@` completion and check for the change.
5. Revert your test change if appropriate.

If the file is missing, moved, temporarily unreadable or partially written, the app should report the issue and retain the last successfully loaded references **within the current session**. The saved path is not automatically repaired; reselect the file after moving it. Do not rely on the cached list after restarting while the file is unavailable.

## 5. Citation keys and source identifiers

The text between `@article{` and the first comma in BibTeX is a **citation key**. The app inserts that exact key, e.g. `[@example2024]`. Keep keys stable once used in Markdown; consider pinning keys in Better BibTeX. DOI and URL fields can provide additional source context. **A `.bib` entry does not necessarily contain Zotero's internal item ID**, so direct Zotero item links are not inferred from citation keys.

## Troubleshooting

- **Only two references appear:** the bundled sample bibliography is selected; choose your own `.bib` export.
- **New Zotero item not visible:** verify Better BibTeX's **Keep updated** export is configured, the export file itself changed, and the app points to that exact file.
- **Citation key changes:** the old Markdown citation may no longer resolve; reconcile it explicitly instead of assuming a new key.
- **Moved file:** use **Navigate → Choose Bibliography** again. Your Markdown notes remain editable without Zotero running.

More information: [Zotero documentation](https://www.zotero.org/support/) and [Better BibTeX documentation](https://retorque.re/zotero-better-bibtex/).
