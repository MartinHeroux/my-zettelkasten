import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zettelkasten.onboarding import (create_collection, collection_is_valid,
    save_default_collection, get_default_collection, clear_default_collection)


class CollectionManagementTests(unittest.TestCase):
    def test_first_run_has_no_implicit_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(get_default_collection(Path(tmp) / 'missing.json'))

    def test_create_and_switch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            a = create_collection(base, 'A')
            b = create_collection(base, 'B')
            prefs = base / 'prefs.json'
            self.assertTrue(collection_is_valid(a))
            save_default_collection(a, prefs)
            self.assertEqual(get_default_collection(prefs), a)
            save_default_collection(b, prefs)
            self.assertEqual(get_default_collection(prefs), b)
            clear_default_collection(prefs)
            self.assertIsNone(get_default_collection(prefs))
            self.assertTrue(a.is_dir())
            self.assertTrue(b.is_dir())

    def test_missing_dropbox_folder_does_not_get_recreated(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dropbox = create_collection(base, 'Dropbox')
            prefs = base / 'prefs.json'
            save_default_collection(dropbox, prefs)
            (dropbox / 'notes').rmdir()
            dropbox.rmdir()
            self.assertIsNone(get_default_collection(prefs))
            self.assertFalse(dropbox.exists())

    def test_never_overwrite_existing_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'Existing').mkdir()
            with self.assertRaises(ValueError):
                create_collection(base, 'Existing')
            with self.assertRaises(ValueError):
                create_collection(base, '../escape')
