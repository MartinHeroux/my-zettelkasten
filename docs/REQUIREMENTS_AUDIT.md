# Requirements audit — v0.4 pilot candidate

This is a transparent assessment, not an acceptance sign-off. The user must test the Linux Mint GUI before the pilot is approved for real research notes.

| Requirement | Status | Notes |
| --- | --- | --- |
| M01 | Partial | Collection selected on launch; startup selection persistence without CLI not complete. |
| M02 | Implemented | UUID note paths; title from first heading. |
| M03–M04 | Implemented, needs manual testing | Syntax styling and editing, including Unicode and undo. |
| M05–M06 | Implemented, needs live-export testing | Bibliography completion and last-good reference list. |
| M07 | Implemented | Note completion and standard Markdown links. |
| M08 | Partial | New linked note exists; navigation/focus behaviour needs pilot verification. |
| M09 | Partial | Back/Forward exists; opening ordinary web links from editor is not yet complete. |
| M10 | Partial | All, Recent, Pinned, Unlinked and content search; result-count display not yet included. |
| M11 | Partial | Backlinks and missing-target display; some unusual Markdown link syntax not handled. |
| M12 | Partial | Source lookup and paper association; citation indexing is intentionally simple. |
| M13 | Implemented, needs manual testing | File attachments and system opener. |
| M14–M15 | Implemented, needs failure testing | Atomic saves, recovery, external-edit conflict guard. |
| M16 | Implemented | Derived indexes rebuilt from files. |
| M17 | Partial | Explicit Zotero/ordinary web link opening from editor needs completion. |
| M18 | Implemented, needs manual testing | Categories, archive toggle, Archived filter. |
| M19 | Partial | Overview templates and ordinary Markdown links; Start here is not auto-created. |
| M20 | Implemented, needs real-BibTeX testing | Open/create paper note by source key. |
| M21 | Implemented | Paper template with full reference from export; generic templates for other types. |
| M22 | Implemented, needs manual testing | Recoverable deletion and Restore dialog. |

## Remaining acceptance work

- Confirm all 18 pilot scenarios from the v0.4 requirements document on Linux Mint.
- Improve external URL/Zotero link handling and show a link-diagnostics view.
- Finish collection-selection persistence, pinned Start here creation and result counts.
- Test changed/missing bibliography with a live Better BibTeX export, and verify complex author/title formatting.
- Check safety of moving/deleting open notes, external edits, and crash recovery with disposable sample data.
