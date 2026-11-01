"""Tk regression tests; run with xvfb-run if no graphical session."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from types import SimpleNamespace
from zettelkasten.app import EditorApp

with TemporaryDirectory() as folder:
    root = tk.Tk()
    root.geometry('1250x780')
    app = EditorApp(root, Path(folder))
    root.update()
    assert app.toolbar_buttons['Back'].instate(['disabled'])
    assert app.toolbar_buttons['Forward'].instate(['disabled'])
    app.new_category('idea'); app.save(); a = app.path
    app.new_category('idea'); app.save(); b = app.path
    app.new_category('idea'); app.save(); c = app.path
    assert app.toolbar_buttons['Back'].instate(['!disabled'])
    assert app.toolbar_buttons['Forward'].instate(['disabled'])
    app.go_back(); assert app.path == b
    app.go_back(); assert app.path == a
    app.go_forward(); assert app.path == b
    app.go_forward(); assert app.path == c
    assert app.toolbar_buttons['Forward'].instate(['disabled'])
    app.go_back(); assert app.path == b
    app.open_note(a)
    assert not app.future, 'A new navigation must invalidate the forward branch'
    app.text.insert('end', '\n[[')
    root.update()
    app._completion_key(SimpleNamespace(keysym='bracketleft'))
    assert app.popup is not None
    assert app.popup_list.size() >= 2
    app._popup_keypress(SimpleNamespace(keysym='Down'))
    selection = app.popup_list.curselection()
    assert selection == (1,), selection
    popup = app.popup
    app._completion_key(SimpleNamespace(keysym='Down'))
    assert app.popup is popup
    assert app.popup_list.curselection() == (1,)
    app._completion_key(SimpleNamespace(keysym='bracketleft'))
    assert app.popup is popup, 'No refresh when search/results are unchanged'
    assert app.popup_list.curselection() == (1,)
    chosen = app.popup_matches[1]
    app._popup_keypress(SimpleNamespace(keysym='Return'))
    assert app.popup is None
    assert chosen['path'].name in app._content()
    assert app.root.focus_get() == app.text
    # Live completion filtering and pinned-first sidebar ordering.
    app.text.insert('end', '\n[[')
    app.text.mark_set('insert', 'end-1c')
    app._completion_key(SimpleNamespace(keysym='bracketleft'))
    assert app.popup is not None
    app._close_popup()
    app.pinned.add(c.name)
    app.filter_var.set('All')
    app._populate_list()
    assert app.displayed_notes[0]['path'] == c, 'Pinned note must lead All'
    app.pinned.clear()
    app._populate_list()
    mods = [n['modified'] for n in app.displayed_notes]
    assert mods == sorted(mods, reverse=True), 'Unpinned notes must sort by recency'
    root.destroy()
print('GUI regression tests passed')
