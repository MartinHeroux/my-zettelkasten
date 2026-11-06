import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from zettelkasten.onboarding import (
    save_default_collection,
    get_default_collection,
    get_recent_collections,
    clear_default_collection,
    clear_recent_collections,
    collection_is_valid,
)


class RecentCollectionsTests(unittest.TestCase):

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prefs = self.root / "preferences.json"

    def make_collection(self, name):
        folder = self.root / name
        (folder / "notes").mkdir(parents=True)
        return folder

    def test_first_run(self):
        self.assertIsNone(get_default_collection(self.prefs))
        self.assertEqual(get_recent_collections(self.prefs), [])

    def test_recent_order_and_duplicates(self):
        a = self.make_collection("A")
        b = self.make_collection("B")

        save_default_collection(a, self.prefs)
        save_default_collection(b, self.prefs)
        save_default_collection(a, self.prefs)

        self.assertEqual(
            get_recent_collections(self.prefs),
            [str(a), str(b)]
        )

    def test_recent_limit(self):
        for i in range(12):
            folder = self.make_collection(f"Collection-{i}")
            save_default_collection(folder, self.prefs)

        recent = get_recent_collections(self.prefs)
        self.assertEqual(len(recent), 10)
        self.assertTrue(recent[0].endswith("Collection-11"))
        self.assertTrue(recent[-1].endswith("Collection-2"))

    def test_close_preserves_history(self):
        a = self.make_collection("A")
        save_default_collection(a, self.prefs)
        clear_default_collection(self.prefs)

        self.assertIsNone(get_default_collection(self.prefs))
        self.assertEqual(get_recent_collections(self.prefs), [str(a)])

    def test_clear_history_preserves_current_collection(self):
        a = self.make_collection("A")
        save_default_collection(a, self.prefs)
        clear_recent_collections(self.prefs)

        self.assertEqual(get_recent_collections(self.prefs), [])
        self.assertEqual(get_default_collection(self.prefs), a)

    def test_missing_dropbox_folder(self):
        folder = self.make_collection("Dropbox-Collection")
        save_default_collection(folder, self.prefs)

        folder.rename(self.root / "Moved-Collection")

        self.assertIsNone(get_default_collection(self.prefs))
        self.assertEqual(
            get_recent_collections(self.prefs),
            []
        )
        self.assertFalse(collection_is_valid(folder))

    def test_missing_collection_reappears_when_restored(self):
        folder = self.make_collection("Removable")
        save_default_collection(folder, self.prefs)
        moved = self.root / "Temporarily-elsewhere"
        folder.rename(moved)
        self.assertEqual(get_recent_collections(self.prefs), [])
        moved.rename(folder)
        self.assertEqual(get_recent_collections(self.prefs), [str(folder)])

    def test_existing_non_collection_folder_hidden(self):
        folder = self.root / "NotACollection"
        folder.mkdir()
        self.prefs.write_text(json.dumps({"recent_collections": [str(folder)]}), encoding="utf-8")
        self.assertEqual(get_recent_collections(self.prefs), [])

    def test_legacy_preferences(self):
        a = self.make_collection("A")
        self.prefs.write_text(
            json.dumps({"collection": str(a)}),
            encoding="utf-8"
        )

        self.assertEqual(get_default_collection(self.prefs), a)
        self.assertEqual(get_recent_collections(self.prefs), [])


if __name__ == "__main__":
    unittest.main()
