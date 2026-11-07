"""Run with xvfb-run or a Linux desktop."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from unittest.mock import patch
from zettelkasten.app import EditorApp
from zettelkasten.bibliography import parse_bib
from zettelkasten.storage import save_note

with TemporaryDirectory() as tmp:
    root=tk.Tk()
    app=EditorApp(root,Path(tmp))
    app.new();app.save()
    app.references=parse_bib('@article{smith2024, title={Motor Control}, author={Smith, A.}, year=2024, journal={Journal}, volume=5}')
    app.text.insert('insert','\\n[@smi')
    root.update()
    app._completion_key()
    assert app.popup is not None, 'citation popup did not open'
    app._choose_completion()
    assert '[@smith2024]' in app._content(), app._content()
    app._update_sources()
    app.source_list.selection_set(0)
    with patch('zettelkasten.app.messagebox.showinfo') as details:
        app._source_double_click()
    assert 'Motor Control' in details.call_args.args[1]
    assert not hasattr(app, 'open_paper_reference')
    root.destroy()
print('GUI bibliography regression passed')
