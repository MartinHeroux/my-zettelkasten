from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from zettelkasten.app import EditorApp

with TemporaryDirectory() as d:
    root = tk.Tk()
    root.withdraw()
    app = EditorApp(root, Path(d))
    app.new_category('idea')
    app.save()
    first = app.path
    app.new_category('project')
    app.save()
    second = app.path
    assert len(app.inventory) == 4  # two onboarding notes plus two created notes
    app.open_note(first)
    app.text.insert('end', f'\n[Paper]({second.name})\n')
    app.save()
    assert second in app.outgoing_paths
    app.open_note(second)
    assert first in app.incoming_paths
    app.go_back()
    assert app.path == first
    app.toggle_pin()
    assert first.name in app.pinned
    app._close_popup()
    root.destroy()
print('GUI smoke passed')
