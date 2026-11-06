"""Personal Zettelkasten v0.4.2: local connected Markdown notes."""
from __future__ import annotations

import argparse
import os
import json
import re
import shutil
import subprocess
import sys
import webbrowser
from urllib.parse import urlsplit, unquote
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, font, messagebox, simpledialog, ttk

from .highlighting import spans
from .bibliography import BibError, read_bib, paper_matches, paper_template
from .collection import archived_of, title_of, category_of, scan, template, link_for, trash_note
from .onboarding import ensure_welcome, get_default_collection, save_default_collection, clear_default_collection, create_collection, collection_is_valid, get_recent_collections, clear_recent_collections
from .storage import ExternalChangeError, load_note, new_note_path, preserve_unsaved_copy, save_note


def completion_matches(inventory, current_path, query, limit=12):
    """Rank title-prefix matches before title substrings; fall back to content.

    Empty query shows the most recently edited notes. Case-insensitive.
    """
    candidates = [n for n in inventory if n['path'] != current_path]
    if not query:
        return sorted(candidates, key=lambda n: (-n['modified'], n['title'].casefold()))[:limit]
    query = query.casefold()
    titles = [n for n in candidates if query in n['title'].casefold()]
    if titles:
        titles.sort(key=lambda n: (not n['title'].casefold().startswith(query), -n['modified'], n['title'].casefold()))
        return titles[:limit]
    contents = [n for n in candidates if query in n['content'].casefold()]
    contents.sort(key=lambda n: (-n['modified'], n['title'].casefold()))
    return contents[:limit]


class EditorApp:
    AUTOSAVE_MS = 1400
    HIGHLIGHT_MS = 160

    def __init__(self, root: tk.Tk, collection: Path):
        self.root = root
        self.collection = collection.expanduser().resolve()
        self.notes_dir = self.collection / "notes"
        self.inbox_dir = self.collection / "inbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_dir = self.collection / "recovery"
        self.attachments_dir = self.collection / "attachments"
        self.settings_path = self.collection / "settings.json"
        self.pinned = set()
        self.bib_path = self.collection / 'references' / 'library.bib'
        self.references = {}
        self.bib_signature = None
        self.bib_error = None
        try:
            settings = json.loads(self.settings_path.read_text())
            self.pinned = set(settings.get('pinned', []))
            if settings.get('bibliography'):
                self.bib_path = Path(settings['bibliography']).expanduser()
        except (OSError, ValueError, TypeError):
            pass
        self.history = []
        self.future = []
        self._populating_list = False
        self._popup_signature = None
        self.inventory = []
        self.popup = None
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.path: Path | None = None
        self.expected_hash: str | None = None
        self.dirty = False
        self.conflicted = False
        self._loading = False
        self._autosave_job = None
        self._highlight_job = None
        self._make_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Control-s>", lambda e: self._shortcut_save())
        self.root.bind("<Control-o>", lambda e: self._shortcut_open())
        self.root.bind("<Control-n>", lambda e: self._shortcut_new())
        self.root.bind("<Control-f>", lambda e: self._shortcut_find())
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-Shift-Z>", lambda e: self._redo())
        self.root.bind("<Control-Shift-z>", lambda e: self._redo())
        self.root.bind("<Control-plus>", lambda e: self._zoom(1))
        self.root.bind("<Control-minus>", lambda e: self._zoom(-1))
        self.root.geometry("1250x780")
        self.root.after_idle(self._maximize_window)
        self.refresh_inventory()
        welcome = ensure_welcome(self.collection, self.notes_dir, self.inventory)
        if welcome is not None:
            self.pinned.add(welcome.name)
            self._settings_save()
            self.refresh_inventory()
            self._load(welcome)
        self.refresh_bibliography()
        self.text.bind("<KeyRelease>", self._completion_key, add="+")
        self.text.bind("<KeyPress>", self._popup_keypress, add="+")
        self.text.bind("<Control-Return>", self._follow_at_cursor, add="+")
        self.text.bind("<Control-Button-1>", self._follow_at_cursor, add="+")
        self._install_shortcuts()
        self._set_status("Ready — Idea or Open a Markdown note")
        self._update_history_buttons()

    def _make_ui(self):
        self.root.title(f"My Zettelkasten — {self.collection.name}")
        self.root.minsize(650, 450)
        bar = ttk.Frame(self.root, padding=8)
        bar.pack(fill="x")
        self.toolbar_buttons = {}
        self._build_menus()
        # Note types belong in one creation menu; Linked Note is an action,
        # not a note category. Keep Back/Forward as individually addressable buttons.
        new_button = ttk.Menubutton(bar, text="New Note ▾")
        new_menu = tk.Menu(new_button, tearoff=False)
        for label, command in (
            ("Fleeting Note", self.new_fleeting),
            ("Literature Note", lambda: self.new_category("paper")),
            ("Permanent Note", self.new),
            ("Project Note", lambda: self.new_category("project")),
            ("Entry-Point Note", lambda: self.new_category("overview")),
        ):
            new_menu.add_command(label=label, command=command)
        new_button.configure(menu=new_menu)
        new_button.pack(side="left", padx=(0, 10))
        for label, command in (
            ("Linked Note", self.new_linked),
            ("Inbox", self.show_inbox),
            ("Save", self.save),
            ("Back", self.go_back),
            ("Forward", self.go_forward),
            ("References", self.choose_reference),
            ("Find", self.find),
        ):
            button = ttk.Button(bar, text=label, command=command)
            button.pack(side="left", padx=(0, 6))
            self.toolbar_buttons[label] = button
        self.fleeting_actions = []
        for label, action in (("Develop", self.develop_fleeting), ("Discard", self.discard_fleeting)):
            button = ttk.Button(bar, text=label, command=action, state='disabled')
            button.pack(side='left', padx=(0, 5))
            self.fleeting_actions.append(button)
        self.path_label = ttk.Label(bar, text="No note open")
        self.path_label.pack(side="left", padx=12)
        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=6)
        frame = ttk.Frame(body, padding=(8, 0, 8, 5))
        right = ttk.Frame(body, padding=6)
        body.add(left, weight=1)
        body.add(frame, weight=4)
        body.add(right, weight=1)
        ttk.Label(left, text="Search notes").pack(anchor="w")
        self.query_var = tk.StringVar()
        self.query_var.trace_add("write", lambda *_: self._populate_list())
        self.sidebar_search = ttk.Entry(left, textvariable=self.query_var)
        self.sidebar_search.pack(fill="x", pady=4)
        self.filter_var = tk.StringVar(value="All")
        # Read-only section headings and separators in a dropdown, not fake filters.
        self.filter_choices = ("All", "Recent", "Pinned", "────────────", "Permanent", "Literature", "Project", "Entry Point", "─────────────", "Unlinked", "Archived", "Uncategorised")
        self.filter_combo = ttk.Combobox(left, textvariable=self.filter_var, values=self.filter_choices, state="readonly")
        self.filter_combo.pack(fill="x", pady=4)
        self.filter_combo.bind('<<ComboboxSelected>>', self._filter_selected)
        self.filter_var.trace_add("write", lambda *_: self._populate_list())
        self.results_var = tk.StringVar(value="0 notes")
        ttk.Label(left, textvariable=self.results_var).pack(anchor="w")
        self.note_list = tk.Listbox(left, exportselection=False, width=32)
        self.note_list.pack(fill="both", expand=True)
        # A ListboxSelect virtual event can arrive after a programmatic reorder.
        # Navigate only from explicit pointer/keyboard actions, never stale events.
        self.note_list.bind("<ButtonRelease-1>", self._sidebar_click)
        for key in ("Up", "Down", "Home", "End", "Prior", "Next"):
            self.note_list.bind(f"<KeyRelease-{key}>", self._sidebar_keyboard)
        ttk.Label(right, text="Sources cited").pack(anchor="w")
        self.source_list = tk.Listbox(right, height=5, width=28, exportselection=False)
        self.source_list.pack(fill='x', pady=(0, 8))
        self.source_list.bind('<Double-Button-1>', self._source_double_click)
        ttk.Label(right, text="Links to").pack(anchor="w")
        self.outgoing_list = tk.Listbox(right, height=9, width=28, exportselection=False)
        self.outgoing_list.pack(fill="both", expand=True, pady=(0, 12))
        self.outgoing_list.bind("<Double-Button-1>", lambda e: self._open_relation(self.outgoing_list, self.outgoing_paths))
        ttk.Label(right, text="Linked from").pack(anchor="w")
        self.incoming_list = tk.Listbox(right, height=9, width=28, exportselection=False)
        self.incoming_list.pack(fill="both", expand=True)
        self.incoming_list.bind("<Double-Button-1>", lambda e: self._open_relation(self.incoming_list, self.incoming_paths))
        self.text = tk.Text(frame, wrap="word", undo=True, maxundo=500, autoseparators=True,
                            padx=16, pady=16, relief="flat", borderwidth=0, insertwidth=2,
                            tabs=("2c",))
        scroller = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroller.set)
        scroller.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.base_size = 12
        self._set_fonts()
        self.text.bind("<<Modified>>", self._modified)
        self.status_var = tk.StringVar()
        status_frame = ttk.Frame(self.root, padding=(12, 5))
        status_frame.pack(fill="x")
        ttk.Label(
            status_frame,
            text=f"{self.collection.name}  |  {self.collection}",
            anchor="w"
        ).pack(side="left")
        ttk.Separator(
            status_frame, orient="vertical"
        ).pack(side="left", fill="y", padx=10)
        ttk.Label(
            status_frame, textvariable=self.status_var, anchor="w"
        ).pack(side="left", fill="x", expand=True)
        self.text.focus_set()

    def _maximize_window(self):
        """Use the desktop's maximized state, not borderless fullscreen."""
        try:
            self.root.state('zoomed')
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)
            except tk.TclError:
                # Window managers without a zoomed state keep the usable default.
                pass

    def _run_shortcut(self, action):
        action()
        return 'break'

    def _focus_sidebar_search(self):
        self.sidebar_search.focus_set()
        self.sidebar_search.select_range(0, 'end')

    def _install_shortcuts(self):
        shortcuts = {
            '<Control-Shift-N>': self.new_fleeting,
            '<Control-Shift-I>': self.new,
            '<Control-Shift-P>': lambda: self.new_category('paper'),
            '<Control-Shift-O>': lambda: self.new_category('overview'),
            '<Control-Shift-J>': lambda: self.new_category('project'),
            '<Control-Shift-L>': self.new_linked,
            '<Control-Shift-A>': self.attach,
            '<Control-Shift-F>': self._focus_sidebar_search,
            '<Control-Shift-K>': self.toggle_pin,
            '<Control-Shift-R>': self.choose_reference,
            '<Alt-Left>': self.go_back,
            '<Alt-Right>': self.go_forward,
        }
        for sequence, action in shortcuts.items():
            self.root.bind(sequence, lambda event, fn=action: self._run_shortcut(fn))
        # Some Tk/Linux keyboard layouts report uppercase shortcuts differently.
        for letter, action in [('n',self.new_fleeting),('i',self.new),('p',lambda: self.new_category('paper')),
                               ('o',lambda: self.new_category('overview')),
                               ('j',lambda: self.new_category('project')),
                               ('l',self.new_linked),('a',self.attach),
                               ('f',self._focus_sidebar_search),('k',self.toggle_pin),('r',self.choose_reference)]:
            self.root.bind(f'<Control-Shift-{letter}>', lambda event, fn=action: self._run_shortcut(fn))

    def _filter_selected(self, event=None):
        if self.filter_var.get().startswith('─'):
            self.filter_var.set(getattr(self, '_last_filter', 'All'))
        else:
            self._last_filter = self.filter_var.get()

    def _build_menus(self):
        menu = tk.Menu(self.root)
        filemenu = tk.Menu(menu, tearoff=False)
        filemenu.add_command(label='New Collection...', command=self.new_collection)
        filemenu.add_command(label='Open Collection...', command=self.open_collection)
        recent_menu = tk.Menu(filemenu, tearoff=False)
        filemenu.add_cascade(label='Recent Collections', menu=recent_menu)
        recent_menu.configure(
            postcommand=lambda: self._populate_recent_menu(recent_menu)
        )
        filemenu.add_command(label='Close Collection', command=self.close_collection)
        filemenu.add_separator()
        filemenu.add_command(label='Open Markdown file', command=self.open_dialog, accelerator='Ctrl+O')
        filemenu.add_command(label='Save', command=self.save, accelerator='Ctrl+S')
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.close)
        menu.add_cascade(label='File', menu=filemenu)

        notemenu = tk.Menu(menu, tearoff=False)
        for label, action, shortcut in (
            ('New Fleeting Note', self.new_fleeting, 'Ctrl+Shift+N'),
            ('New Permanent Note', self.new, 'Ctrl+Shift+I'),
            ('New Literature Note', lambda: self.new_category('paper'), 'Ctrl+Shift+P'),
            ('New Project Note', lambda: self.new_category('project'), 'Ctrl+Shift+J'),
            ('New Entry-Point Note', lambda: self.new_category('overview'), 'Ctrl+Shift+O'),
            ('New Linked Note', self.new_linked, 'Ctrl+Shift+L'),
        ):
            notemenu.add_command(label=label, command=action, accelerator=shortcut)
        notemenu.add_separator()
        for label, action, shortcut in (
            ('Pin / Unpin', self.toggle_pin, 'Ctrl+Shift+K'),
            ('Attach File', self.attach, 'Ctrl+Shift+A'),
            ('Archive / Unarchive', self.toggle_archive, ''),
            ('Move to Trash', self.delete_note, ''),
            ('Restore from Trash', self.restore_note, ''),
        ):
            notemenu.add_command(label=label, command=action, accelerator=shortcut)
        menu.add_cascade(label='Note', menu=notemenu)

        navmenu = tk.Menu(menu, tearoff=False)
        for label, action, shortcut in (
            ('Back', self.go_back, 'Alt+Left'),
            ('Forward', self.go_forward, 'Alt+Right'),
            ('Search Notes', self._focus_sidebar_search, 'Ctrl+Shift+F'),
            ('Find in Current Note', self.find, 'Ctrl+F'),
            ('Fleeting Inbox', self.show_inbox, ''),
            ('Find Reference / Paper Note', self.choose_reference, 'Ctrl+Shift+R'),
            ('Choose Bibliography', self.choose_bibliography, ''),
            ('Reload Bibliography', lambda: self.refresh_bibliography(force=True), ''),
            ('Refresh Notes', self.refresh_inventory, ''),
        ):
            navmenu.add_command(label=label, command=action, accelerator=shortcut)
        menu.add_cascade(label='Navigate', menu=navmenu)
        helpmenu = tk.Menu(menu, tearoff=False)
        helpmenu.add_command(label='Keyboard shortcuts', command=self._show_shortcuts)
        helpmenu.add_separator()
        helpmenu.add_command(label='About My Zettelkasten...', command=self.show_about)
        menu.add_cascade(label='Help', menu=helpmenu)
        self.root.configure(menu=menu)

    def show_about(self):
        """Display application information and installed version."""
        from importlib.metadata import version, PackageNotFoundError

        try:
            app_version = version("personal-zettelkasten")
        except PackageNotFoundError:
            app_version = "Unknown"

        messagebox.showinfo(
            "About My Zettelkasten",
            f"My Zettelkasten\n"
            f"Version {app_version}\n\n"
            "Developed by Martin Heroux\n\n"
            "A personal knowledge management application.\n\n"
            "https://github.com/MartinHeroux/my-zettelkasten",
            parent=self.root
        )

    def _show_shortcuts(self):
        messagebox.showinfo('Keyboard shortcuts',
            'New Fleeting: Ctrl+Shift+N\nNew Permanent: Ctrl+Shift+I\nNew Literature: Ctrl+Shift+P\n'
            'New Entry-Point: Ctrl+Shift+O\nNew Project: Ctrl+Shift+J\n'
            'New linked note: Ctrl+Shift+L\nAttach: Ctrl+Shift+A\n'
            'Save: Ctrl+S\nOpen: Ctrl+O\nSearch notes: Ctrl+Shift+F\n'
            'Find in note: Ctrl+F\nBack / Forward: Alt+Left / Alt+Right\n'
            'Pin / Unpin: Ctrl+Shift+K\nUndo / Redo: Ctrl+Z / Ctrl+Y\n'
            'References: Ctrl+Shift+R\nCitation completion: [@ then type\n'
            'Markdown link completion: [[ then type; arrows, Enter, Esc', parent=self.root)

    def _set_fonts(self):
        family = "DejaVu Sans Mono"
        self.fonts = {
            "normal": font.Font(family=family, size=self.base_size),
            "bold": font.Font(family=family, size=self.base_size, weight="bold"),
            "italic": font.Font(family=family, size=self.base_size, slant="italic"),
            "code": font.Font(family=family, size=self.base_size),
        }
        self.text.configure(font=self.fonts["normal"])
        for level in range(1, 7):
            sz = self.base_size + {1: 8, 2: 6, 3: 4, 4: 2, 5: 1, 6: 0}[level]
            self.fonts[f"heading{level}"] = font.Font(family=family, size=sz, weight="bold")
            self.text.tag_configure(f"heading{level}", font=self.fonts[f"heading{level}"], foreground="#29476a")
        self.text.tag_configure("bold", font=self.fonts["bold"])
        self.text.tag_configure("italic", font=self.fonts["italic"])
        self.text.tag_configure("inlinecode", font=self.fonts["code"], background="#e9edf1", foreground="#5b355f")
        self.text.tag_configure("codeblock", font=self.fonts["code"], background="#f0f2f4", foreground="#454d58")
        self.text.tag_configure("link", foreground="#006f9b", underline=True)
        self.text.tag_configure("citation", foreground="#8c4b16")
        self.text.tag_configure("find_match", background="#ffe59a")

    def _zoom(self, delta):
        self.base_size = min(24, max(9, self.base_size + delta))
        self._set_fonts()
        self._apply_highlighting()
        return "break"

    def _set_status(self, message):
        self.status_var.set(message)
        self.root.title(f"{'* ' if self.dirty else ''}My Zettelkasten — {self.collection.name}")

    def _content(self):
        return self.text.get("1.0", "end-1c")

    def _modified(self, event=None):
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        if self._loading:
            return
        self.dirty = True
        self._set_status("Unsaved changes — autosave pending")
        self._schedule_highlight()
        self._schedule_autosave()
        self._update_sources()

    def _schedule_highlight(self):
        if self._highlight_job:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(self.HIGHLIGHT_MS, self._apply_highlighting)

    def _apply_highlighting(self):
        self._highlight_job = None
        source = self._content()
        # Tkinter Text indices count characters, not bytes. +Nc works for Unicode.
        for tag in ("bold", "italic", "inlinecode", "codeblock", "link", "citation", *(f"heading{i}" for i in range(1, 7))):
            self.text.tag_remove(tag, "1.0", "end")
        for span in spans(source):
            self.text.tag_add(span.kind, f"1.0+{span.start}c", f"1.0+{span.end}c")
        self.text.tag_raise("sel")

    def _schedule_autosave(self):
        if self._autosave_job:
            self.root.after_cancel(self._autosave_job)
        self._autosave_job = self.root.after(self.AUTOSAVE_MS, self._autosave)

    def _autosave(self):
        self._autosave_job = None
        if self.dirty and not self.conflicted and self.path:
            self.save(automatic=True)

    def _cancel_jobs(self):
        if self._autosave_job:
            self.root.after_cancel(self._autosave_job)
            self._autosave_job = None
        if self._highlight_job:
            self.root.after_cancel(self._highlight_job)
            self._highlight_job = None

    def _load(self, path):
        path = Path(path).expanduser().resolve()
        try:
            content, digest = load_note(path)
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Cannot open note", str(error))
            return False
        self._cancel_jobs()
        self._loading = True
        try:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.text.edit_reset()
            self.text.edit_modified(False)
        finally:
            self._loading = False
        self.path, self.expected_hash = path, digest
        self.dirty = False
        self.conflicted = False
        self.path_label.configure(text=path.name)
        self._apply_highlighting()
        self._set_status(f"Opened {path}")
        if hasattr(self, 'fleeting_actions'):
            is_fleeting = path.parent == self.inbox_dir.resolve()
            for button in self.fleeting_actions:
                button.configure(state='normal' if is_fleeting else 'disabled')
        self.refresh_inventory()
        self.text.focus_set()
        return True

    def _guard_unsaved(self):
        # The empty editor shown at startup is not an open note. Tk can deliver
        # a delayed <<Modified>> event even when no file is associated with it.
        # Never attempt to save that empty editor: save() would display the
        # misleading "Use New or Open first" message and block note creation.
        if self.path is None:
            if not self._content().strip():
                self.dirty = False
                self.conflicted = False
                return True
            # Preserve genuinely typed text in the unbound startup editor.
            choice = messagebox.askyesnocancel(
                "Unsaved draft",
                "Text was entered before opening a note. Preserve it in recovery before creating another note?\n\n"
                "Yes: save a recovery copy and continue\n"
                "No: discard the draft and continue\n"
                "Cancel: stay here",
                parent=self.root,
            )
            if choice is None:
                return False
            if choice:
                try:
                    preserve_unsaved_copy(Path('startup-draft.md'), self._content(), self.recovery_dir)
                except OSError as error:
                    messagebox.showerror('Recovery failed', str(error))
                    return False
            self.dirty = False
            self.conflicted = False
            return True
        if not self.dirty:
            return True
        if not self.conflicted and self.save():
            return True
        choice = messagebox.askyesnocancel("Unsaved changes", "Save a separate recovery copy before leaving this note?\n\nYes: preserve copy and continue\nNo: discard unsaved changes\nCancel: stay here")
        if choice is None:
            return False
        if choice:
            try:
                path = preserve_unsaved_copy(self.path or Path("untitled.md"), self._content(), self.recovery_dir)
            except OSError as error:
                messagebox.showerror("Recovery failed", str(error))
                return False
            messagebox.showinfo("Recovery saved", f"Saved unsaved text to:\n{path}")
        return True

    def _focus_title(self):
        """Place caret after the first Markdown H1 marker, never in YAML."""
        for number, line in enumerate(self._content().splitlines(), 1):
            if line.startswith('# '):
                index = f'{number}.{len(line)}'
                self.text.mark_set('insert', index)
                self.text.see(index)
                self.text.focus_set()
                return
        self.text.focus_set()

    def new(self):
        if not self._guard_unsaved():
            return
        previous = self._current_location()
        self._cancel_jobs()
        self.path = new_note_path(self.notes_dir)
        self.expected_hash = None
        self.dirty = True
        self.conflicted = False
        self._loading = True
        try:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", template("idea"))
            self.text.edit_reset()
            self.text.edit_modified(False)
        finally:
            self._loading = False
        self.path_label.configure(text=self.path.name)
        self._apply_highlighting()
        self._set_status("New note — save or wait for autosave")
        for button in self.fleeting_actions:
            button.configure(state='disabled')
        if previous:
            self.history.append(previous)
        self.future.clear()
        self._update_history_buttons()
        self._schedule_autosave()
        self.refresh_inventory()
        self._focus_title()

    def open_dialog(self):
        if not self._guard_unsaved():
            return
        path = filedialog.askopenfilename(title="Open Markdown note", initialdir=self.notes_dir,
                                          filetypes=[("Markdown", "*.md"), ("All files", "*")])
        if path:
            self._load(path)

    def reload(self):
        if not self.path or not self.path.exists():
            return
        if self.dirty and not messagebox.askyesno("Reload", "Discard editor changes and reload from disk?"):
            return
        self._load(self.path)

    def save(self, automatic=False):
        if not self.path:
            if not automatic:
                messagebox.showinfo("No note", "Use New or Open first.")
            return False
        try:
            digest = save_note(self.path, self._content(), self.expected_hash, self.recovery_dir)
        except ExternalChangeError:
            self.conflicted = True
            self._set_status("CONFLICT — file changed on disk. Reload or save recovery copy before leaving.")
            if not automatic:
                messagebox.showwarning("External change detected", "The file changed on disk. It was NOT overwritten.\nUse Reload to discard local changes, or New/Open/Close to preserve a separate recovery copy.")
            return False
        except OSError as error:
            self._set_status(f"SAVE FAILED: {error}")
            if not automatic:
                messagebox.showerror("Save failed", str(error))
            return False
        self.expected_hash = digest
        self.dirty = False
        self.conflicted = False
        self._refresh_inbox_count()
        self._set_status(f"Saved {self.path.name}{' (autosave)' if automatic else ''}")
        self.refresh_inventory()
        return True

    def find(self):
        query = simpledialog.askstring("Find in note", "Find text:", parent=self.root)
        if query is None:
            return
        self.text.tag_remove("find_match", "1.0", "end")
        if not query:
            return
        start = "1.0"
        while True:
            idx = self.text.search(query, start, stopindex="end", nocase=True)
            if not idx:
                break
            end = self.text.index(f"{idx}+{len(query)}c")
            self.text.tag_add("find_match", idx, end)
            start = end
        matches = self.text.tag_ranges("find_match")
        if matches:
            self.text.see(matches[0])
            self.text.mark_set("insert", matches[0])
        self._set_status(f"Find: {len(matches)//2} matches")

    def _undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def _shortcut_save(self):
        self.save()
        return "break"

    def _shortcut_open(self):
        self.open_dialog()
        return "break"

    def _shortcut_new(self):
        self.new()
        return "break"

    def _shortcut_find(self):
        self.find()
        return "break"

    def _settings_save(self):
        self.settings_path.write_text(json.dumps({'pinned': sorted(self.pinned), 'bibliography': str(self.bib_path)}, indent=2), encoding='utf-8')

    def refresh_inventory(self):
        self.inventory = scan(self.notes_dir)
        self._populate_list()
        self._refresh_inbox_count()
        self._update_relations()
        self._update_sources()

    def choose_bibliography(self):
        selected = filedialog.askopenfilename(title='Choose Better BibTeX export',
            initialdir=self.bib_path.parent, filetypes=[('BibTeX', '*.bib'), ('All files', '*')])
        if selected:
            self.bib_path = Path(selected).expanduser().resolve()
            self.bib_signature = None
            self._settings_save()
            self.refresh_bibliography(force=True)

    def refresh_bibliography(self, force=False):
        try:
            stat = self.bib_path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if not force and signature == self.bib_signature:
                return
            loaded = read_bib(self.bib_path)
            if not loaded:
                raise BibError('The bibliography is empty')
            self.references = loaded
            self.bib_signature = signature
            self.bib_error = None
            self._set_status(f'Bibliography loaded: {len(loaded)} references from {self.bib_path.name}')
        except (OSError, UnicodeError, BibError, ValueError) as error:
            self.bib_error = str(error)
            self._set_status(f'Bibliography unavailable ({error}); retaining {len(self.references)} last good references')

    def choose_reference(self):
        self.refresh_bibliography()
        if not self.references:
            messagebox.showinfo('No references', 'Choose a Better BibTeX .bib export using File > Choose bibliography.', parent=self.root)
            return
        window = tk.Toplevel(self.root)
        window.title('References — open or create paper note')
        window.geometry('850x460')
        window.transient(self.root)
        frame = ttk.Frame(window, padding=10)
        frame.pack(fill='both', expand=True)
        query = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=query)
        entry.pack(fill='x')
        listbox = tk.Listbox(frame, exportselection=False)
        listbox.pack(fill='both', expand=True, pady=8)
        matches = []
        def populate(*_):
            needle = query.get().casefold().strip()
            matches[:] = sorted((r for r in self.references.values() if needle in r.search_text),
                                key=lambda r: (not r.title.casefold().startswith(needle), r.title.casefold()))[:100]
            listbox.delete(0, 'end')
            for ref in matches:
                listbox.insert('end', ref.key)
            if matches: listbox.selection_set(0)
        def open_selected(event=None):
            selection = listbox.curselection()
            if not selection: return
            ref = matches[selection[0]]
            window.destroy()
            self.open_paper_reference(ref)
        query.trace_add('write', populate)
        entry.bind('<Return>', open_selected)
        listbox.bind('<Double-Button-1>', open_selected)
        listbox.bind('<Return>', open_selected)
        window.bind('<Escape>', lambda e: window.destroy())
        ttk.Button(frame, text='Open / Create paper note', command=open_selected).pack(anchor='e')
        populate()
        entry.focus_set()

    def open_paper_reference(self, ref):
        matches = paper_matches(self.inventory, ref.key)
        if len(matches) == 1:
            return self.open_note(matches[0]['path'])
        if len(matches) > 1:
            messagebox.showwarning('Multiple paper notes',
                'More than one paper note has this source_key. Choose one in All notes:\n\n' +
                '\n'.join(n['title'] + ' — ' + n['path'].name for n in matches), parent=self.root)
            return False
        if not messagebox.askyesno('Create paper note',
                f'No associated paper note for {ref.key}. Create one?', parent=self.root):
            return False
        if not self._guard_unsaved(): return False
        target = new_note_path(self.notes_dir)
        try:
            save_note(target, paper_template(ref), None, self.recovery_dir)
        except OSError as error:
            messagebox.showerror('Create failed', str(error), parent=self.root)
            return False
        opened = self.open_note(target)
        if opened:
            self._focus_title()
        return opened

    def _update_sources(self):
        if not hasattr(self, 'source_list'): return
        content = self._content() if self.path else ''
        keys = set(re.findall(r'\[@([^\]\s;,]+)', content))
        current = next((n for n in self.inventory if n['path'] == self.path), None)
        if current and current.get('source_key'): keys.add(current['source_key'])
        self.displayed_sources = sorted(keys)
        self.source_list.delete(0, 'end')
        for key in self.displayed_sources:
            ref = self.references.get(key)
            self.source_list.insert('end', (ref.display()[:48] if ref else '⚠ Unresolved: ' + key))

    def _source_double_click(self, event=None):
        selection = self.source_list.curselection()
        if not selection: return
        key = self.displayed_sources[selection[0]]
        ref = self.references.get(key)
        if not ref:
            messagebox.showwarning('Unknown citation', f'No reference for {key}', parent=self.root)
            return
        matches = paper_matches(self.inventory, key)
        other = [n for n in self.inventory if n['path'] != self.path and ('[@'+key) in n['content']]
        summary = ref.full_reference() + '\n\nPaper notes: ' + str(len(matches)) + '\nOther citing notes: ' + str(len(other))
        if messagebox.askyesno('Source information', summary + '\n\nOpen or create its paper note?', parent=self.root):
            self.open_paper_reference(ref)

    def _populate_list(self):
        if not hasattr(self, 'note_list'):
            return
        selected = self.path
        query = self.query_var.get().casefold()
        mode = self.filter_var.get()
        notes = self.inventory[:]
        if mode == 'Archived':
            notes = [n for n in notes if n.get('archived')]
        elif mode != 'All':
            notes = [n for n in notes if not n.get('archived')]
        if mode == 'Pinned':
            notes = [n for n in notes if n['path'].name in self.pinned]
        elif mode == 'Recent':
            pass
        elif mode == 'Archived':
            pass
        elif mode == 'Unlinked':
            linked = set().union(*(n['targets'] for n in notes)) if notes else set()
            notes = [n for n in notes if n['path'] not in linked and not (n['targets'] - {n['path']})]
        elif mode != 'All':
            category = {'Permanent': 'idea', 'Literature': 'paper',
                        'Entry Point': 'overview', 'Project': 'project',
                        'Uncategorised': 'uncategorised'}.get(mode, mode)
            notes = [n for n in notes if n['category'] == category]
        if query:
            notes = [n for n in notes if query in n['title'].casefold() or query in n['content'].casefold()]
        # Pinned first in All; all remaining notes most recently modified first.
        # Other filters use recency, without duplicating pinned entries.
        if mode == 'All':
            notes.sort(key=lambda n: (n['path'].name not in self.pinned, -n['modified'], n['title'].casefold()))
        else:
            notes.sort(key=lambda n: (-n['modified'], n['title'].casefold()))
        self.displayed_notes = notes
        if hasattr(self, "results_var"):
            self.results_var.set(f"{len(notes)} of {len(self.inventory)} notes")
        # Listbox selection-change events can be queued by programmatic refreshes.
        # Ignore those events: only deliberate sidebar interactions navigate.
        self._populating_list = True
        try:
            self.note_list.delete(0, 'end')
            for i, n in enumerate(notes):
                excerpt = ''
                if query and query not in n['title'].casefold():
                    at = n['content'].casefold().find(query)
                    excerpt = ' · ' + ' '.join(n['content'][max(0, at-20):at+45].split())
                label = ('★ ' if n['path'].name in self.pinned else '') + ('[Archived] ' if n.get('archived') else '') + n['title'] + ' [' + n['category'] + ']' + excerpt
                self.note_list.insert('end', label[:100])
                if n['path'] == selected:
                    self.note_list.selection_set(i)
        finally:
            self._populating_list = False

    def _sidebar_open_selection(self):
        """Resolve the selected row against the latest inventory, by path."""
        chosen = self.note_list.curselection()
        if not chosen or chosen[0] >= len(self.displayed_notes):
            return
        target = self.displayed_notes[chosen[0]]['path']
        if target != self.path:
            self.open_note(target)

    def _sidebar_click(self, event):
        # Clicking empty space must not navigate to the last visible row.
        if not (0 <= event.y < self.note_list.winfo_height()):
            return
        row = self.note_list.nearest(event.y)
        if row >= self.note_list.size():
            return
        bbox = self.note_list.bbox(row)
        if bbox is None or not (bbox[1] <= event.y < bbox[1] + bbox[3]):
            return
        self.note_list.selection_clear(0, 'end')
        self.note_list.selection_set(row)
        self._sidebar_open_selection()

    def _sidebar_keyboard(self, event):
        self._sidebar_open_selection()

    def _current_location(self):
        if self.path is None:
            return None
        return (self.path, self.text.index('insert'), self.text.yview()[0])

    def _update_history_buttons(self):
        if hasattr(self, 'toolbar_buttons'):
            self.toolbar_buttons['Back'].configure(state='normal' if self.history else 'disabled')
            self.toolbar_buttons['Forward'].configure(state='normal' if self.future else 'disabled')


    def open_note(self, target: Path, record=True):
        target = Path(target).resolve()
        if not target.is_file() or target.parent not in (self.notes_dir.resolve(), self.inbox_dir.resolve()):
            messagebox.showwarning('Missing note', f'Cannot open note: {target}')
            return False
        if target == self.path:
            return True
        if not self._guard_unsaved():
            return False
        previous = self._current_location()
        if not self._load(target):
            return False
        if record:
            if previous:
                self.history.append(previous)
            self.future.clear()
        self._update_history_buttons()
        return True

    def _navigate(self, source, destination):
        if not source:
            return False
        # Do not modify history until the destination has loaded successfully.
        target, cursor, scroll = source[-1]
        if not target.is_file():
            messagebox.showwarning('Missing note', f'History target is missing: {target}')
            return False
        if not self._guard_unsaved():
            return False
        previous = self._current_location()
        if not self._load(target):
            return False
        source.pop()
        if previous:
            destination.append(previous)
        self.text.mark_set('insert', cursor)
        self.text.see(cursor)
        self.text.yview_moveto(scroll)
        self._update_history_buttons()
        return True

    def go_back(self):
        return self._navigate(self.history, self.future)

    def go_forward(self):
        return self._navigate(self.future, self.history)

    def _update_relations(self):
        if not hasattr(self, 'outgoing_list'):
            return
        current = self.path.resolve() if self.path else None
        bypath = {n['path']: n for n in self.inventory}
        note = bypath.get(current)
        self.outgoing_paths = sorted(note['targets']) if note else []
        self.incoming_paths = sorted(n['path'] for n in self.inventory if current and current in n['targets'] and n['path'] != current)
        for widget, paths in ((self.outgoing_list, self.outgoing_paths), (self.incoming_list, self.incoming_paths)):
            widget.delete(0, 'end')
            for path in paths:
                widget.insert('end', bypath[path]['title'] if path in bypath else '⚠ Missing: ' + path.name)

    def _open_relation(self, widget, paths):
        selection = widget.curselection()
        if selection:
            self.open_note(paths[selection[0]])

    def new_category(self, category='idea'):
        if not self._guard_unsaved():
            return
        self.new_without_guard(category)

    def new_without_guard(self, category):
        previous = self._current_location()
        self._cancel_jobs()
        self.path = new_note_path(self.inbox_dir if category == 'fleeting' else self.notes_dir)
        self.expected_hash = None
        self.dirty = True
        self.conflicted = False
        self._loading = True
        try:
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', '# Fleeting thought\n\n' if category == 'fleeting' else template(category))
            self.text.edit_reset()
            self.text.edit_modified(False)
        finally:
            self._loading = False
        self.path_label.configure(text=self.path.name)
        self._apply_highlighting()
        self._set_status('New ' + category + ' note')
        for button in self.fleeting_actions:
            button.configure(state='normal' if category == 'fleeting' else 'disabled')
        if previous:
            self.history.append(previous)
        self.future.clear()
        self._update_history_buttons()
        self._schedule_autosave()
        self.refresh_inventory()
        self._focus_title()

    def new_fleeting(self):
        self.new_category('fleeting')

    def _inbox_paths(self):
        return sorted(self.inbox_dir.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)

    def _refresh_inbox_count(self):
        if hasattr(self, 'toolbar_buttons') and 'Inbox' in self.toolbar_buttons:
            self.toolbar_buttons['Inbox'].configure(text=f'Inbox ({len(self._inbox_paths())})')

    def show_inbox(self):
        if not self._guard_unsaved():
            return
        dialog = tk.Toplevel(self.root)
        dialog.title('Fleeting Inbox')
        dialog.geometry('540x390')
        dialog.transient(self.root)
        ttk.Label(dialog, text='Unprocessed fleeting notes').pack(anchor='w', padx=12, pady=8)
        listing = tk.Listbox(dialog, exportselection=False)
        listing.pack(fill='both', expand=True, padx=12, pady=4)
        paths = self._inbox_paths()
        for path in paths:
            try:
                content = path.read_text(encoding='utf-8-sig')
                title = title_of(content) if False else next((line[2:].strip() for line in content.splitlines() if line.startswith('# ')), path.stem)
            except OSError:
                title = path.stem
            listing.insert('end', title + '  —  ' + path.stem[:12])
        def open_selected(event=None):
            selected = listing.curselection()
            if not selected:
                return
            target = paths[selected[0]]
            dialog.destroy()
            self.open_note(target)
        ttk.Button(dialog, text='Open selected', command=open_selected).pack(pady=8)
        listing.bind('<Double-Button-1>', open_selected)

    def develop_fleeting(self):
        if not self.path or self.path.parent.resolve() != self.inbox_dir.resolve():
            return
        if not self._guard_unsaved():
            return
        source = self.path
        try:
            content = source.read_text(encoding='utf-8-sig')
        except OSError as error:
            messagebox.showerror('Cannot develop note', str(error))
            return
        # Create the destination before offering to remove the source.
        target = new_note_path(self.notes_dir)
        developed = template('idea') + '\n## From fleeting note\n\n' + content + '\n'
        try:
            save_note(target, developed, None, self.recovery_dir)
        except OSError as error:
            messagebox.showerror('Cannot develop note', str(error))
            return
        if self._load(target):
            self._set_status('Permanent note created. Edit and save it; the fleeting source remains in Inbox.')
            messagebox.showinfo('Permanent note created', 'A new permanent note has been created from the fleeting note. The original remains in Inbox until you explicitly discard it.')

    def discard_fleeting(self):
        if not self.path or self.path.parent.resolve() != self.inbox_dir.resolve():
            return
        if not messagebox.askyesno(
            'Permanently discard fleeting note',
            f'Permanently delete {self.path.name} and its recovery copies?\n\n'
            'This cannot be undone with Restore from Trash.', parent=self.root
        ):
            return
        discarded = self.path
        try:
            # Remove saved versions first; retain the source if cleanup fails.
            for recovery in self.recovery_dir.glob(f'{discarded.stem}.*.md'):
                recovery.unlink()
            discarded.unlink(missing_ok=True)
        except OSError as error:
            messagebox.showerror('Discard failed', str(error), parent=self.root)
            return
        self._clear_removed_note(discarded)
        self._refresh_inbox_count()
        self._set_status('Fleeting note permanently deleted')

    def new_linked(self):
        """Branch to a new idea; persist the source link before navigating."""
        if not self.path:
            self.new_category('idea')
            return
        if self.path.parent.resolve() == self.inbox_dir.resolve():
            messagebox.showinfo('Fleeting note', 'Develop this note before creating linked permanent notes.')
            return
        oldpath = self.path
        original_cursor = self.text.index('insert')
        original_scroll = self.text.yview()[0]
        selected = self.text.get('sel.first', 'sel.last') if self.text.tag_ranges('sel') else ''
        if not self._guard_unsaved():
            return
        target = new_note_path(self.notes_dir)
        # The source link needs a readable label before the target has a title.
        # It can be edited in ordinary Markdown later without changing the ID.
        label = 'New linked idea'
        content = template('idea') + ('\n' + selected + '\n' if selected else '')
        try:
            save_note(target, content, None, self.recovery_dir)
        except OSError as error:
            messagebox.showerror('Create failed', str(error))
            return
        # Insert at the original cursor. Keep selected text intact.
        self.text.mark_set('insert', original_cursor)
        self.text.insert('insert', link_for(oldpath, target, label))
        # A failed save must never navigate away from the unsaved source link.
        if not self.save():
            self._set_status('New note created, but source link could not be saved; still in source note')
            return
        # The saved source is now the Back destination, at the original location.
        self.history.append((oldpath, original_cursor, original_scroll))
        self.future.clear()
        if not self._load(target):
            self.history.pop()
            self._update_history_buttons()
            return
        self._update_history_buttons()
        self._focus_title()

    def toggle_pin(self):
        if not self.path:
            return
        if self.path.name in self.pinned:
            self.pinned.remove(self.path.name)
        else:
            self.pinned.add(self.path.name)
        self._settings_save()
        self._populate_list()

    def delete_note(self):
        if not self.path or not self.path.exists():
            return
        if not messagebox.askyesno('Move to trash', f'Move {self.path.name} to collection trash?'):
            return
        if not self._guard_unsaved():
            return
        try:
            moved = trash_note(self.path, self.collection / 'trash')
        except OSError as error:
            messagebox.showerror('Trash failed', str(error))
            return
        self._clear_removed_note(moved)
        self._set_status(f'Moved to {moved}')

    def _clear_removed_note(self, removed):
        # Pending autosave must not recreate a discarded note.
        self._cancel_jobs()
        self.path = None
        self.expected_hash = None
        self._loading = True
        self.text.delete('1.0', 'end')
        self.text.edit_modified(False)
        self._loading = False
        self.dirty = False
        self.path_label.configure(text='No note open')
        self.refresh_inventory()
        for button in self.fleeting_actions:
            button.configure(state='disabled')
        self.history = [entry for entry in self.history if entry[0] != removed and entry[0].name != removed.name]
        self.future = [entry for entry in self.future if entry[0] != removed and entry[0].name != removed.name]
        self._update_history_buttons()

    def restore_note(self):
        """Restore a deleted note without overwriting a file with the same ID."""
        trash = self.collection / 'trash'
        candidates = sorted(trash.glob('*.md')) if trash.exists() else []
        if not candidates:
            messagebox.showinfo('Restore', 'There are no deleted Markdown notes to restore.', parent=self.root)
            return
        window = tk.Toplevel(self.root)
        window.title('Restore deleted note')
        window.geometry('600x360')
        frame = ttk.Frame(window, padding=10)
        frame.pack(fill='both', expand=True)
        items = tk.Listbox(frame, exportselection=False)
        items.pack(fill='both', expand=True)
        for path in candidates:
            try:
                label = title_of(path.read_text(encoding='utf-8-sig'), path.stem)
            except (OSError, UnicodeError):
                label = path.name
            items.insert('end', f'{label} — {path.name}')
        def restore(event=None):
            selection = items.curselection()
            if not selection: return
            source = candidates[selection[0]]
            destination = self.notes_dir / source.name
            if destination.exists():
                messagebox.showerror('Cannot restore', 'A note with that filename already exists. Nothing was overwritten.', parent=window)
                return
            try:
                source.rename(destination)
            except OSError as error:
                messagebox.showerror('Cannot restore', str(error), parent=window)
                return
            window.destroy()
            self.refresh_inventory()
            self.open_note(destination)
        ttk.Button(frame, text='Restore selected', command=restore).pack(pady=6)
        items.bind('<Double-Button-1>', restore)
        items.bind('<Return>', restore)
        items.focus_set()

    def toggle_archive(self):
        if not self.path: return
        content = self._content()
        if category_of(content) != 'project':
            messagebox.showinfo('Archive', 'Archiving is intended for Project notes.', parent=self.root)
            return
        from .collection import set_archived
        revised = set_archived(content, not archived_of(content))
        if revised != content:
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', revised)
            self._set_status('Project archive state changed; save to retain it')

    def attach(self):
        if not self.path:
            messagebox.showinfo('No note', 'Open a note before attaching a file.')
            return
        source = filedialog.askopenfilename(title='Attach file')
        if not source:
            return
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        src = Path(source)
        destination = self.attachments_dir / src.name
        if destination.exists():
            destination = self.attachments_dir / f'{src.stem}-{os.urandom(4).hex()}{src.suffix}'
        try:
            shutil.copy2(src, destination)
        except OSError as error:
            messagebox.showerror('Attachment failed', str(error))
            return
        label = destination.name.replace(']', '')
        prefix = '!' if destination.suffix.lower() in {'.png','.jpg','.jpeg','.gif','.webp','.svg'} else ''
        self.text.insert('insert', f'{prefix}[{label}](../attachments/{destination.name})')

    def _follow_at_cursor(self, event=None):
        """Follow safe local note/attachment links or explicit HTTP(S)/Zotero URIs."""
        if not self.path:
            return 'break'
        if event is not None and getattr(event, 'num', None) == 1:
            self.text.mark_set('insert', self.text.index(f'@{event.x},{event.y}'))
        line = self.text.get('insert linestart', 'insert lineend')
        col = int(self.text.index('insert').split('.')[1])
        for match in re.finditer(r'(!?)\[[^\]]+\]\(([^)]+)\)', line):
            if not (match.start() <= col <= match.end()):
                continue
            raw = match.group(2).strip()
            parsed = urlsplit(raw)
            if parsed.scheme.lower() in ('http', 'https', 'zotero'):
                try:
                    webbrowser.open(raw)
                except Exception as error:
                    messagebox.showerror('Cannot open link', str(error), parent=self.root)
                break
            if parsed.scheme or raw.startswith('//'):
                messagebox.showwarning('Unsupported link', f'Cannot open this link: {raw}', parent=self.root)
                break
            target = (self.path.parent / unquote(parsed.path)).resolve()
            if target.suffix.lower() == '.md' and target.parent == self.notes_dir.resolve():
                if not target.is_file():
                    messagebox.showwarning('Broken link', f'Note not found: {target.name}', parent=self.root)
                else:
                    self.open_note(target)
            elif target.is_file() and self.attachments_dir.resolve() in target.parents:
                try:
                    subprocess.Popen(['xdg-open', str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError as error:
                    messagebox.showerror('Cannot open attachment', str(error), parent=self.root)
            else:
                messagebox.showwarning('Unavailable link', f'No permitted target found for: {raw}', parent=self.root)
            break
        return 'break'

    def _popup_keypress(self, event):
        if not self.popup or event.keysym not in ('Return', 'Escape', 'Up', 'Down'):
            return
        if event.keysym == 'Escape':
            self._close_popup()
        elif event.keysym == 'Return':
            self._choose_completion()
        else:
            if not self.popup_list.size():
                return 'break'
            idx = self.popup_list.curselection()
            at = ((idx[0] if idx else (0 if event.keysym == 'Up' else -1)) + (-1 if event.keysym == 'Up' else 1)) % self.popup_list.size()
            self.popup_list.selection_clear(0, 'end')
            self.popup_list.selection_set(at)
            self.popup_list.activate(at)
            self.popup_list.see(at)
        return 'break'

    def _completion_key(self, event=None):
        if event is not None and event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return
        if not self.path:
            return
        before = self.text.get('insert linestart', 'insert')
        citation = re.search(r'\[@([^\]\n;,]*)$', before)
        if citation:
            self.refresh_bibliography()
            needle = citation.group(1).casefold().strip()
            matches = [r for r in self.references.values() if needle in r.search_text]
            matches.sort(key=lambda r: (not r.key.casefold().startswith(needle),
                                        not r.title.casefold().startswith(needle), r.title.casefold()))
            if matches:
                self._show_popup(matches[:12], len(citation.group(0)), 'citation')
                return
        link = re.search(r'\[\[([^\]\n]*)$', before)
        if link:
            matches = completion_matches(self.inventory, self.path, link.group(1))
            if matches:
                self._show_popup(matches, len(link.group(0)), 'note')
                return
        self._close_popup()

    def _show_popup(self, matches, prefix_len, kind='note'):
        signature = (kind, tuple(n['path'] if kind == 'note' else n.key for n in matches), prefix_len)
        if self.popup is not None and signature == self._popup_signature:
            return
        self._close_popup()
        self._popup_signature = signature
        self.popup_matches = matches
        self.popup_kind = kind
        self.popup_prefix_len = prefix_len
        self.popup = tk.Toplevel(self.root)
        self.popup.overrideredirect(True)
        self.popup.transient(self.root)
        self.popup_list = tk.Listbox(self.popup, height=min(8, len(matches)), width=85, exportselection=False)
        self.popup_list.pack()
        for n in matches:
            label = (n['title'] + ' [' + n['category'] + ']') if kind == 'note' else n.key
            self.popup_list.insert('end', label[:135])
        self.popup_list.selection_set(0)
        self.popup_list.bind('<Double-Button-1>', lambda e: self._choose_completion())
        bbox = self.text.bbox('insert')
        if bbox:
            x, y, w, h = bbox
            self.popup.geometry(f'+{self.text.winfo_rootx()+x}+{self.text.winfo_rooty()+y+h}')

    def _close_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
        self._popup_signature = None

    def _choose_completion(self):
        if not self.popup:
            return
        selection = self.popup_list.curselection()
        if not selection:
            return
        item = self.popup_matches[selection[0]]
        start = self.text.index(f'insert-{self.popup_prefix_len}c')
        if self.popup_kind == 'citation':
            replacement = f'[@{item.key}'
            # Reuse a closing bracket already present after the caret.
            if self.text.get('insert', 'insert+1c') != ']':
                replacement += ']'
        else:
            replacement = link_for(self.path, item['path'], item['title'])
        self.text.delete(start, 'insert')
        self.text.insert(start, replacement)
        self._close_popup()
        self.text.focus_set()
        self._update_sources()

    def _switch_collection(self, collection=None):
        if not self._guard_unsaved():
            return False
        self._cancel_jobs()
        command = [sys.executable, '-m', 'zettelkasten']
        if collection is None:
            command.append('--welcome')
        else:
            command.extend(['--collection', str(collection)])
        try:
            subprocess.Popen(command, cwd=str(Path.home()))
        except OSError as error:
            messagebox.showerror('Cannot switch collection', str(error), parent=self.root)
            return False
        self.root.destroy()
        return True

    def new_collection(self):
        if not self._guard_unsaved():
            return
        parent = filedialog.askdirectory(parent=self.root, title='Choose parent folder for new collection', mustexist=True)
        if not parent:
            return
        name = simpledialog.askstring('New Collection', 'Collection folder name:', parent=self.root)
        if not name:
            return
        try:
            destination = create_collection(Path(parent), name)
        except (OSError, ValueError) as error:
            messagebox.showerror('Cannot create collection', str(error), parent=self.root)
            return
        self._switch_collection(destination)

    def _populate_recent_menu(self, menu):
        """Refresh recent collections whenever the menu opens."""
        menu.delete(0, 'end')
        recent = get_recent_collections()

        if not recent:
            menu.add_command(label='No recent collections', state='disabled')
        else:
            for location in recent:
                collection = Path(location).expanduser()
                label = f"{collection.name} — {collection}"

                menu.add_command(
                    label=label,
                    command=lambda path=collection: self._open_recent_collection(path)
                )

        menu.add_separator()
        menu.add_command(
            label='Clear Recent Collections',
            command=self._clear_recent_menu,
            state='normal' if recent else 'disabled'
        )

    def _open_recent_collection(self, collection):
        """Open a recent collection without creating missing folders."""
        if not collection_is_valid(collection):
            messagebox.showwarning(
                'Collection unavailable',
                f'Cannot open this collection:\n\n{collection}\n\n'
                'The folder may have been moved, or Dropbox may be unavailable.',
                parent=self.root
            )
            return

        if collection.resolve() == self.collection:
            return

        self._switch_collection(collection)

    def _clear_recent_menu(self):
        if messagebox.askyesno(
            'Clear Recent Collections',
            'Remove the recent collection history?\n\n'
            'Your notes and collection folders will not be deleted.',
            parent=self.root
        ):
            clear_recent_collections()

    def open_collection(self):
        selected = filedialog.askdirectory(parent=self.root, title='Open existing collection', mustexist=True)
        if not selected:
            return
        if not collection_is_valid(Path(selected)):
            messagebox.showerror('Not a collection', 'Choose a folder containing a notes directory.', parent=self.root)
            return
        self._switch_collection(Path(selected))

    def close_collection(self):
        if self._switch_collection():
            clear_default_collection()

    def close(self):
        if not self._guard_unsaved():
            return
        self._cancel_jobs()
        self.root.destroy()


def show_welcome(root):
    """Welcome screen with new, open and recent collections."""
    root.title('My Zettelkasten — Welcome')
    root.geometry('760x520')
    root.minsize(620, 420)

    panel = ttk.Frame(root, padding=25)
    panel.pack(expand=True, fill='both')

    ttk.Label(
        panel,
        text='Welcome to My Zettelkasten',
        font=('TkDefaultFont', 17, 'bold')
    ).pack(pady=(5, 8))

    ttk.Label(
        panel,
        text='Create a collection or open an existing one to get started.'
    ).pack(pady=(0, 18))

    def launch(collection):
        if collection is None:
            return
        if not collection_is_valid(collection):
            messagebox.showwarning(
                'Collection unavailable',
                f'Cannot open this collection:\\n\\n{collection}\\n\\n'
                'The folder may have been moved, or Dropbox may be unavailable.',
                parent=root
            )
            return
        save_default_collection(collection)
        try:
            subprocess.Popen(
                [sys.executable, '-m', 'zettelkasten',
                 '--collection', str(collection)],
                cwd=str(Path.home())
            )
        except OSError as error:
            messagebox.showerror(
                'Cannot open collection', str(error), parent=root
            )
            return
        root.destroy()

    def new():
        parent = filedialog.askdirectory(
            parent=root,
            title='Choose parent folder for new collection',
            mustexist=True
        )
        if not parent:
            return
        name = simpledialog.askstring(
            'New Collection', 'Collection folder name:', parent=root
        )
        if not name:
            return
        try:
            destination = create_collection(Path(parent), name)
        except (ValueError, OSError) as error:
            messagebox.showerror(
                'Cannot create collection', str(error), parent=root
            )
            return
        launch(destination)

    def open_existing():
        selected = filedialog.askdirectory(
            parent=root,
            title='Open existing collection',
            mustexist=True
        )
        if not selected:
            return
        launch(Path(selected))

    buttons = ttk.Frame(panel)
    buttons.pack(pady=(0, 20))

    ttk.Button(
        buttons, text='New Collection...', command=new
    ).pack(side='left', padx=8)

    ttk.Button(
        buttons, text='Open Collection...', command=open_existing
    ).pack(side='left', padx=8)

    ttk.Separator(panel, orient='horizontal').pack(
        fill='x', pady=(0, 15)
    )

    recent_header = ttk.Frame(panel)
    recent_header.pack(fill='x', pady=(0, 8))

    ttk.Label(
        recent_header,
        text='Recent Collections',
        font=('TkDefaultFont', 11, 'bold')
    ).pack(side='left')

    recent = get_recent_collections()

    if recent:
        list_frame = ttk.Frame(panel)
        list_frame.pack(fill='both', expand=True)

        collection_list = tk.Listbox(
            list_frame,
            height=10,
            activestyle='dotbox',
            exportselection=False
        )
        collection_list.pack(
            side='left', fill='both', expand=True
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient='vertical',
            command=collection_list.yview
        )
        scrollbar.pack(side='right', fill='y')
        collection_list.configure(yscrollcommand=scrollbar.set)

        for location in recent:
            collection = Path(location).expanduser()
            collection_list.insert(
                'end', f'{collection.name}  —  {collection}'
            )

        def open_selected(event=None):
            selection = collection_list.curselection()
            if selection:
                launch(Path(recent[selection[0]]))

        collection_list.bind('<Double-Button-1>', open_selected)
        collection_list.bind('<Return>', open_selected)

        ttk.Button(
            panel,
            text='Open Selected Collection',
            command=open_selected
        ).pack(pady=(10, 0))

    else:
        ttk.Label(
            panel,
            text='No recent collections yet.',
            foreground='gray'
        ).pack(pady=25)

    ttk.Label(
        panel,
        text='New collections include introductory Start Here notes.',
        foreground='gray'
    ).pack(pady=(15, 0))



def main():
    from importlib.metadata import version, PackageNotFoundError

    try:
        app_version = version("personal-zettelkasten")
    except PackageNotFoundError:
        app_version = "Unknown"

    parser = argparse.ArgumentParser(description='My Zettelkasten editor')
    parser.add_argument(
        '--version',
        action='version',
        version=f'My Zettelkasten {app_version}'
    )
    parser.add_argument('--collection', type=Path, default=None, help='Collection folder')
    parser.add_argument('--open', type=Path, help='Markdown note to open at launch')
    parser.add_argument('--welcome', action='store_true', help='Show the collection chooser')
    args = parser.parse_args()
    try:
        root = tk.Tk()
    except tk.TclError as error:
        parser.exit(1, f'Cannot open Tk window: {error}\n')
    selected = None if args.welcome else (args.collection or get_default_collection())
    if selected is not None and collection_is_valid(selected):
        app = EditorApp(root, selected)
        save_default_collection(selected)
        if args.open:
            app._load(args.open)
    else:
        show_welcome(root)
    root.mainloop()


if __name__ == '__main__':
    main()
