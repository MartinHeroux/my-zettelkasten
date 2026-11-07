"""Exercise actual Trash/Restore callbacks on real files without a display."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch
from zettelkasten.app import EditorApp

class TrashFlowTests(TestCase):
    def test_trash_restore_main_and_inbox(self):
        for folder in ('notes', 'inbox'):
            with self.subTest(folder=folder), TemporaryDirectory() as tmp:
                base = Path(tmp)
                app = EditorApp.__new__(EditorApp)
                app.collection = base
                app.notes_dir = base/'notes'; app.notes_dir.mkdir()
                app.inbox_dir = base/'inbox'; app.inbox_dir.mkdir()
                app.path = base/folder/'n_test.md'; app.path.write_text('# Test')
                original = app.path
                app.root = Mock()
                for name in ('_clear_removed_note','_refresh_inbox_count','_set_status','refresh_inventory','open_note'):
                    setattr(app, name, Mock())
                app._guard_unsaved = Mock(return_value=True)
                with patch('zettelkasten.app.messagebox.askyesno', return_value=True):
                    app.delete_note()
                self.assertFalse(original.exists())
                listing = Mock(); listing.curselection.return_value = (0,)
                with patch('zettelkasten.app.tk.Toplevel'), patch('zettelkasten.app.ttk.Frame'), \
                     patch('zettelkasten.app.tk.Listbox', return_value=listing), \
                     patch('zettelkasten.app.ttk.Button') as button:
                    app.restore_note()
                    button.call_args.kwargs['command']()
                self.assertEqual(original.read_text(), '# Test')
                app.open_note.assert_called_once_with(original)
