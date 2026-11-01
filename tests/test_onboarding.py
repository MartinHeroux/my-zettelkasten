import tempfile
import unittest
from pathlib import Path
from zettelkasten.onboarding import ensure_welcome, get_default_collection, save_default_collection

class OnboardingTests(unittest.TestCase):
    def test_welcome_once_and_preserve_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); notes=base/'notes'; notes.mkdir()
            welcome=ensure_welcome(base,notes,[])
            self.assertTrue(welcome.exists())
            self.assertEqual(len(list(notes.glob('*.md'))),2)
            self.assertIsNone(ensure_welcome(base,notes,[]))
            self.assertEqual(len(list(notes.glob('*.md'))),2)
    def test_existing_note_never_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); notes=base/'notes'; notes.mkdir()
            file=notes/'n_existing.md'; file.write_text('# Existing')
            self.assertIsNone(ensure_welcome(base,notes,[]))
            self.assertEqual(file.read_text(),'# Existing')
    def test_preference_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); prefs=base/'preferences.json'
            save_default_collection(base,prefs)
            self.assertEqual(get_default_collection(prefs),base)

if __name__=='__main__': unittest.main()
