# v0.2.1 manual acceptance checklist

Work only in the disposable example collection.

1. Create at least three notes (Idea, Paper, Overview). Confirm the normal new-note button says **Idea**.
2. In a note type `[[`. Press Down twice, then Up once; selection should stay on the intended suggestion rather than jump to the top. Press Enter; confirm the selected note's link is inserted. Repeat with typed search text and Esc.
3. Open notes A, B, C by clicking their sidebar entries. Back should open B, then A. Forward should open B, then C. Verify buttons disable at the ends.
4. Navigate Back to B and then open a different note D; Forward should now be disabled.
5. Move the cursor and scroll within A before navigating away; Back should restore its previous position.
6. Confirm links, backlinks, search, attachments and autosave still work as they did in v0.2.
7. Make an external edit to a note and confirm it is not silently overwritten.

If a problem occurs, report the steps and any terminal traceback.

## v0.2.2 regression checks

1. Pin two notes and select All: both should appear above unpinned notes.
2. Edit an unpinned note, save and refresh: it should become the first unpinned note.
3. Search the sidebar: matching pinned notes should still appear above matching unpinned notes.
4. In a note, type `[[c`: the popup should show only matching C titles when available.
5. Continue typing `ort`, use Down/Up and Enter. Verify the selected target is inserted.
6. Search for a word only found in note content: the popup should show content matches when no title matches.
7. Esc dismisses suggestions; typing an unmatched string should close the popup.

## v0.3 reference integration checks

1. Launch the app with the disposable sample collection; choose **References** and find the fictional García article by title.
2. Create its paper note and verify `source_key`, full reference, DOI and four headings.
3. Open **References** again and select the same article: the existing note should open, not duplicate.
4. In an idea note type `[@gar` and press Enter: the citation should complete. Try searching by `García`, `2024` and `Reaching` too.
5. Try `[@gar]` with the closing bracket already typed: the completion must not create `]]`.
6. Use File > Choose bibliography to point to a *copy* of your real Better BibTeX export; try author/title/key searches.
7. Update the copied export and try completion again; confirm changes load. Temporarily move the export and check the status message while continuing to edit.
8. Double-click a citation in the Sources cited panel to inspect it and open its associated paper note.
9. Verify existing `[[` completion, Back/Forward, pinned notes, autosave, and external-edit protection still work.

## v0.3.1 — First-note creation regression

1. Start the app with an empty disposable collection and **no note open**.
2. Press **Ctrl+Shift+I**. Confirm an Idea note opens immediately without a
   “No note” dialog. Save, restart, and confirm it reopens from the sidebar.
3. Repeat from fresh empty collections for **Ctrl+Shift+P**, **Ctrl+Shift+O**,
   and **Ctrl+Shift+J** (Paper, Overview, Project).
4. Repeat the same four actions using the toolbar buttons.
5. Confirm creating a second note still works and citation completion still
   works with the sample bibliography.
