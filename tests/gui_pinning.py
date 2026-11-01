"""Regression for click A/pin/click B/pin after sidebar reordering."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from types import SimpleNamespace
from zettelkasten.app import EditorApp

with TemporaryDirectory() as folder:
    root = tk.Tk()
    app = EditorApp(root, Path(folder))
    root.update()
    app.new_category('idea'); app.save(); a = app.path
    app.new_category('idea'); app.save(); b = app.path
    app.new_category('idea'); app.save(); c = app.path
    root.update()

    def click_note(path):
        app._populate_list()
        root.update()
        row = next(i for i, note in enumerate(app.displayed_notes) if note['path'] == path)
        app.note_list.see(row)
        root.update()
        bbox = app.note_list.bbox(row)
        assert bbox is not None
        y = bbox[1] + max(1, bbox[3] // 2)
        app.note_list.event_generate('<ButtonPress-1>', x=8, y=y)
        app.note_list.event_generate('<ButtonRelease-1>', x=8, y=y)
        root.update()
        assert app.path == path, (app.path, path)

    click_note(a)
    app.toggle_pin()
    root.update()
    assert a.name in app.pinned
    click_note(b)
    assert a.name in app.pinned
    app.toggle_pin()
    root.update()
    assert {a.name, b.name} <= app.pinned
    assert [n['path'] for n in app.displayed_notes[:2]] == [n['path'] for n in app.displayed_notes if n['path'].name in app.pinned][:2]
    click_note(c)
    assert app.path == c
    click_note(a)
    app.toggle_pin()
    assert a.name not in app.pinned and b.name in app.pinned
    # Refreshes must not switch the open note.
    app._populate_list()
    root.update()
    assert app.path == a
    root.destroy()
print('Sidebar pinning GUI regression passed')
