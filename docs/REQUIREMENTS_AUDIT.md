# Verification for v0.5.6

Run `PYTHONPATH=src python -m unittest discover -s tests` for headless regression checks.

Desktop checks:
- Create each supported note type: Fleeting, Permanent, Project, Entry-Point. Verify Literature and References controls and shortcuts are absent.
- Choose a bibliography; verify `[@` completion and Sources cited reference details.
- Develop a fleeting note; verify the original remains and the new note is separate.
- Cancel permanent deletion; verify note and recovery files remain. Confirm deletion for a disposable fleeting and permanent note, and wait beyond autosave to ensure it is not recreated.
- Move main and Inbox notes to Trash; restore each to its original folder. Verify an existing filename is never overwritten.
- Archive, save and reopen a project; find it under Archived and unarchive it.
- Edit and autosave repeatedly; verify no more than ten saved recovery versions per note and unchanged conflict detection.
- Verify legacy paper/literature files remain editable and links continue to work under All / Uncategorised.
