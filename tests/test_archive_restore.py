import tempfile
import unittest
from pathlib import Path
from zettelkasten.collection import archived_of, set_archived, scan, trash_note

class ArchiveRestoreTests(unittest.TestCase):
    def test_archive_roundtrip(self):
        text='---\ncategory: project\n---\n\n# Study\n'
        archived=set_archived(text,True)
        self.assertTrue(archived_of(archived))
        self.assertIn('archived: true', archived)
        self.assertFalse(archived_of(set_archived(archived,False)))
        self.assertEqual(set_archived(archived,False),text)
    def test_archive_visible_in_scan(self):
        with tempfile.TemporaryDirectory() as d:
            notes=Path(d)/'notes';notes.mkdir()
            (notes/'n_a.md').write_text(set_archived('---\ncategory: project\n---\n# A\n',True))
            self.assertTrue(scan(notes)[0]['archived'])
    def test_trash_preserves_filename(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); notes=root/'notes';notes.mkdir()
            path=notes/'n_123.md';path.write_text('# Note')
            moved=trash_note(path,root/'trash')
            self.assertFalse(path.exists());self.assertEqual(moved.name,'n_123.md')
            moved.rename(path)
            self.assertEqual(path.read_text(),'# Note')
if __name__=='__main__': unittest.main()
