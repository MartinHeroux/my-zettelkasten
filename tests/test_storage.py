import tempfile
import unittest
from pathlib import Path
from zettelkasten.storage import (ExternalChangeError, load_note, new_note_path,
                                   preserve_unsaved_copy, save_note)


class StorageTests(unittest.TestCase):
    def test_roundtrip_and_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = new_note_path(root / "notes")
            self.assertFalse(path.exists())
            first = save_note(path, "# Café ☕\n", None, root / "recovery")
            self.assertEqual(load_note(path), ("# Café ☕\n", first))
            second = save_note(path, "# Revised\n", first, root / "recovery")
            self.assertNotEqual(first, second)
            self.assertEqual(len(list((root / "recovery").glob("*.md"))), 1)
            self.assertEqual(list((root / "recovery").glob("*.md"))[0].read_text(), "# Café ☕\n")

    def test_external_edit_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "notes" / "a.md"
            original = save_note(path, "original", None, root / "recovery")
            path.write_text("external")
            with self.assertRaises(ExternalChangeError):
                save_note(path, "local", original, root / "recovery")
            self.assertEqual(path.read_text(), "external")
            recovered = preserve_unsaved_copy(path, "local", root / "recovery")
            self.assertEqual(recovered.read_text(), "local")

    def test_new_file_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "a.md"
            path.write_text("existing")
            with self.assertRaises(ExternalChangeError):
                save_note(path, "new", None, root / "recovery")

    def test_bounded_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "n.md"
            digest = save_note(path, "0", None, root / "recovery")
            for i in range(1, 7):
                digest = save_note(path, str(i), digest, root / "recovery", max_copies=3)
            self.assertEqual(len(list((root / "recovery").glob("*.md"))), 3)


if __name__ == "__main__":
    unittest.main()
