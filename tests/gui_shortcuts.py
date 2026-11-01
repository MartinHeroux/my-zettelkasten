"""Run under a graphical session or xvfb-run."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from zettelkasten.app import EditorApp
with TemporaryDirectory() as folder:
    root=tk.Tk()
    app=EditorApp(root, Path(folder))
    root.update()
    assert 'v0.4.2' in root.title(), root.title()
    assert root.cget('menu'), 'Application menus missing'
    app._run_shortcut(app.new)
    assert app.path is not None
    app.save()
    assert app.path.exists()
    app._run_shortcut(app._focus_sidebar_search)
    assert root.focus_get() == app.sidebar_search
    app._run_shortcut(lambda: app.new_category('paper'))
    assert 'paper' in app._content().lower()
    assert 'v0.4.2' in root.title()
    root.destroy()
print('GUI shortcut regression passed')
