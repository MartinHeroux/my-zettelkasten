"""Run under xvfb-run; validate title focus, link persistence and Back."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from zettelkasten.app import EditorApp
from zettelkasten.collection import category_of, targets

for category in ('idea','paper','overview','project'):
    with TemporaryDirectory() as d:
        root=tk.Tk(); app=EditorApp(root,Path(d)); root.update()
        app.new_category(category); root.update()
        body=app._content()
        assert category_of(body)==category
        assert '# \n' in body
        assert app.text.index('insert') == next(f'{i}.{len(line)}' for i,line in enumerate(body.splitlines(),1) if line.startswith('# ')), (category,app.text.index('insert'))
        if category=='paper': assert '## What the paper contributes' in body
        if category=='overview': assert '## Entry points' in body
        assert app.save()
        app._cancel_jobs(); root.destroy()

with TemporaryDirectory() as d:
    root=tk.Tk(); app=EditorApp(root,Path(d)); root.update()
    app.new_category('idea')
    app.text.insert('insert','Original idea')
    app.text.insert('end','\n\nAn interesting connection: ')
    app.text.mark_set('insert','end-1c')
    root.update(); source=app.path
    app.new_linked(); root.update()
    target=app.path
    assert target != source
    assert target in targets(source.read_text(),source,app.notes_dir)
    assert 'New linked idea' in source.read_text()
    assert '# \n' in target.read_text()
    assert app.text.index('insert') == next(f'{i}.{len(line)}' for i,line in enumerate(app._content().splitlines(),1) if line.startswith('# '))
    assert app.go_back()
    assert app.path==source
    assert app.go_forward()
    assert app.path==target
    app._cancel_jobs(); root.destroy()
print('v0.4.2 note creation GUI regression passed')
