# Current implementation audit

This records behaviour found in the current source, rather than certifying desktop acceptance. Historical releases are listed in the Changelog.

| Area | Current implementation | Remaining verification |
|---|---|---|
| Collections | Welcome screen, create/open/close, last-used collection, up to 10 Recent Collections; unavailable collections are not silently recreated | Desktop switching and unavailable Dropbox folders |
| Note creation | New Note menu: Fleeting, Permanent, Literature, Project, Entry-Point; stable filenames and title focus | Keyboard and menu parity on Linux Mint |
| Inbox | Separate `inbox/`, count, open, Develop to separate Permanent note; original retained | Full capture/process workflow |
| Discard | Fleeting original and recovery copies permanently deleted after confirmation; autosave cancelled and visit history cleared for deleted note | Desktop confirmation/cancellation and no recreation after autosave delay |
| Main-note deletion | Move to collection Trash and Restore; restored files go to `notes/` | Restore collision handling; fleeting origin is not tracked |
| Editing | Markdown syntax styling, autosave, recovery, external-change conflict detection | Real-world conflict and failure checks |
| Linking | Note completion, outgoing links, backlinks, missing-target indication, linked-note creation, Back/Forward | Complex Markdown syntax remains limited |
| Sources | Read-only Better BibTeX, key-only suggestions, citation insertion, associated Literature notes, last-good session cache | Live and complex Better BibTeX exports |
| Discovery | Search, result count, pinning; All, Recent, Pinned, Permanent, Literature, Project, Entry Point, Unlinked, Archived, Uncategorised | Larger collections and filter interaction |
| Navigation | Markdown links at cursor; explicit web/Zotero URLs through system handler | Desktop URL handlers |
| Onboarding | Pinned editable Start here and linked tutorial, only for empty uninitialised collections | Existing tutorial notes are intentionally not overwritten |
| Attachments | Copies into collection; relative links and system opener | Desktop image/PDF handling |

Use [Pilot checklist](PILOT_CHECKLIST.md) for remaining manual checks. No automatic Zotero-note synchronization, graph interface or rendered Markdown preview is implemented.
