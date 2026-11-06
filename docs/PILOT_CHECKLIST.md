# v0.5 pilot checklist (Linux Mint)

Use a **throwaway** collection and test each item before trusting real research notes.

- [ ] Empty collection opens a pinned Start here note and linked tutorial.
- [ ] Relaunch does not duplicate welcome notes; existing collections are untouched.
- [ ] Create Fleeting, Permanent, Literature, Entry-Point and Project notes; cursor starts at title.
- [ ] Linked note saves source link, opens new note; Back returns to original position.
- [ ] Link completion and citation completion work entirely by keyboard.
- [ ] Two pinned notes remain pinned and one-click selection works.
- [ ] Search by content; verify the results count and filtering.
- [ ] Ctrl+Enter on a local note link opens it; broken links warn.
- [ ] Ctrl+Enter on an explicit HTTPS link opens the browser; Zotero links use system URL handler.
- [ ] Add PNG/PDF attachment, confirm copied file and relative link.
- [ ] Delete/restore a note, archive/unarchive a project, verify links.
- [ ] Modify an open note externally; verify it is not silently overwritten.
- [ ] Make bibliography temporarily unavailable; note editing continues.
- [ ] Restart without `--collection`; previously selected collection reopens.
- [ ] Copy the entire collection to another folder and confirm relative links still work.
- [ ] Create an independent backup, then verify you can restore it.

Report any failures with the terminal traceback and the steps to reproduce.

## Inbox and current-interface checks

- [ ] Create fleeting notes using both New Note and Ctrl+Shift+N; verify Inbox count and title focus.
- [ ] Develop a fleeting note; verify separate Permanent file, source retained, and editable content.
- [ ] Cancel Discard; verify the source and recovery copies remain.
- [ ] Confirm Discard; verify source/recovery copies are gone, no Trash entry was created, developed note remains, and waiting past autosave does not recreate the source.
- [ ] Discard a newly created fleeting note before its first autosave.
- [ ] Simulate deletion failure; verify an error is shown and the open note remains available.
- [ ] Move a main note to Trash and restore it; verify recoverable deletion still works.
- [ ] Search citations by author/title/year/key; suggestions contain only keys and selection inserts only `[@key]`.
- [ ] Check New Note labels, sidebar filters, Help shortcuts and Navigate bibliography commands against the guides.
