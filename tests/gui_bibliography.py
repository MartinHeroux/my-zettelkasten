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
    ref=app.references['smith2024']
    with patch('zettelkasten.app.messagebox.askyesno',return_value=True):
        app.open_paper_reference(ref)
    assert 'source_key: "smith2024"' in app._content(), app._content()
    previous=app.path
    app.refresh_inventory()
    assert len([n for n in app.inventory if n.get('source_key')=='smith2024']) == 1
    app.open_paper_reference(ref)
    assert app.path == previous
    root.destroy()
print('GUI bibliography regression passed')
