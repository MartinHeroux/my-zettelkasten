"""Fresh-launch regression: all note creation actions work without an open note."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tkinter as tk
from zettelkasten.app import EditorApp

cases = [
    ('Idea', 'idea', '<Control-Shift-I>'),
    ('Paper', 'paper', '<Control-Shift-P>'),
    ('Overview', 'overview', '<Control-Shift-O>'),
    ('Project', 'project', '<Control-Shift-J>'),
]
for label, category, shortcut in cases:
    for route in ('toolbar', 'shortcut'):
        with TemporaryDirectory() as d:
            root = tk.Tk()
            app = EditorApp(root, Path(d))
            root.update()
            # Simulate the delayed modified state that previously triggered
            # save() with no associated note.
            app.dirty = True
            with patch('zettelkasten.app.messagebox.showinfo', side_effect=AssertionError('unexpected No note dialog')):
                if route == 'toolbar':
                    app.toolbar_buttons[label].invoke()
                else:
                    root.focus_force()
                    app.text.focus_force()
                    root.update()
                    root.event_generate(shortcut)
                root.update()
            assert app.path is not None, (label, route)
            assert f'category: {category}' in app._content(), (label, route, app._content())
            assert app.save(), (label, route)
            path = app.path
            assert path.exists(), (label, route)
            assert f'category: {category}' in path.read_text(), (label, route)
            app._cancel_jobs()
            root.destroy()

# A draft typed into the unbound editor must not be silently discarded.
with TemporaryDirectory() as d:
    root = tk.Tk()
    app = EditorApp(root, Path(d))
    app.text.insert('1.0', 'An important draft')
    root.update()
    with patch('zettelkasten.app.messagebox.askyesnocancel', return_value=True):
        app.new()
    assert app.path is not None
    assert list((Path(d) / 'recovery').glob('*'))
    app._cancel_jobs()
    root.destroy()
print('First-note GUI regression passed (8 fresh-launch routes + draft preservation)')
