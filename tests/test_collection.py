import tempfile
import unittest
from pathlib import Path
from zettelkasten.collection import template, scan, targets, category_of, title_of, link_for, trash_note

class CollectionTests(unittest.TestCase):
    def test_templates(self):
        for category in ('idea','paper','overview','project','inbox'):
            value = template(category, 'Example')
            self.assertEqual(category_of(value), category)
            self.assertEqual(title_of(value), 'Example')
        self.assertIn('## Methods and results', template('paper'))

    def test_links_and_backlinks_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / 'notes'; folder.mkdir()
            a = folder / 'n_a.md'; b = folder / 'n_b.md'
            a.write_text('# Alpha\n\n[Beta](n_b.md)\n```\n[Bad](n_c.md)\n```\n', encoding='utf-8')
            b.write_text('# Beta\n', encoding='utf-8')
            self.assertEqual(targets(a.read_text(), a, folder), {b.resolve()})
            notes = scan(folder)
            self.assertEqual(len(notes), 2)
            self.assertEqual(link_for(a, b, 'Beta'), '[Beta](n_b.md)')

    def test_trash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'n_abc.md'; p.write_text('hello')
            dest = trash_note(p, Path(d) / 'trash')
            self.assertFalse(p.exists())
            self.assertEqual(dest.read_text(), 'hello')
