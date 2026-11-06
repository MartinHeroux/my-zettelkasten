"""Headless regression checks for destructive Inbox actions."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from zettelkasten.app import EditorApp


class FleetingTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.app = EditorApp.__new__(EditorApp)
        self.app.root = Mock()
        self.app.inbox_dir = self.base / 'inbox'
        self.app.inbox_dir.mkdir()
        self.app.recovery_dir = self.base / 'recovery'
        self.app.recovery_dir.mkdir()
        self.app.path = self.app.inbox_dir / 'n_test.md'
        self.app.path.write_text('# Fleeting thought')
        self.recovery = self.app.recovery_dir / 'n_test.old.md'
        self.recovery.write_text('old thought')
        self.other = self.app.recovery_dir / 'n_other.old.md'
        self.other.write_text('unrelated')
        self.app._clear_removed_note = Mock()
        self.app._refresh_inbox_count = Mock()
        self.app._set_status = Mock()

    def test_confirm_discards_source_and_its_recovery_only(self):
        developed = self.base / 'permanent.md'
        developed.write_text('developed thought')
        with patch('zettelkasten.app.messagebox.askyesno', return_value=True):
            self.app.discard_fleeting()
        self.assertFalse(self.app.path.exists())
        self.assertFalse(self.recovery.exists())
        self.assertTrue(self.other.exists())
        self.assertTrue(developed.exists())
        self.assertFalse((self.base / 'trash').exists())
        self.app._clear_removed_note.assert_called_once_with(self.app.path)

    def test_cancel_keeps_source_and_recovery(self):
        with patch('zettelkasten.app.messagebox.askyesno', return_value=False):
            self.app.discard_fleeting()
        self.assertTrue(self.app.path.exists())
        self.assertTrue(self.recovery.exists())
        self.app._clear_removed_note.assert_not_called()

    def test_discard_before_first_autosave(self):
        self.app.path.unlink()
        with patch('zettelkasten.app.messagebox.askyesno', return_value=True):
            self.app.discard_fleeting()
        self.app._clear_removed_note.assert_called_once()

    def test_failure_keeps_editor_open(self):
        with patch('zettelkasten.app.messagebox.askyesno', return_value=True), \
             patch.object(Path, 'unlink', side_effect=PermissionError('read only')), \
             patch('zettelkasten.app.messagebox.showerror') as error:
            self.app.discard_fleeting()
        error.assert_called_once()
        self.assertTrue(self.app.path.exists())
        self.app._clear_removed_note.assert_not_called()

    def test_main_note_cannot_be_discarded(self):
        self.app.path = self.base / 'main.md'
        self.app.path.write_text('permanent')
        with patch('zettelkasten.app.messagebox.askyesno') as confirm:
            self.app.discard_fleeting()
        confirm.assert_not_called()
        self.assertTrue(self.app.path.exists())

    def test_removed_note_cancels_jobs_and_clears_history(self):
        app = self.app
        del app._clear_removed_note
        app._cancel_jobs = Mock()
        app.text = Mock()
        app.path_label = Mock()
        app.refresh_inventory = Mock()
        app.fleeting_actions = [Mock(), Mock()]
        app._update_history_buttons = Mock()
        removed = app.path
        app.history = [(removed, '1.0', 0), (self.base/'other.md', '1.0', 0)]
        app.future = [(removed, '1.0', 0)]
        app._clear_removed_note(removed)
        app._cancel_jobs.assert_called_once()
        self.assertIsNone(app.path)
        self.assertFalse(app.dirty)
        self.assertEqual(len(app.history), 1)
        self.assertEqual(app.future, [])

    def test_fleeting_shortcut_both_keyboard_variants(self):
        app = self.app
        for name in ['new', 'new_fleeting', 'new_category', 'new_linked', 'attach',
                     '_focus_sidebar_search', 'toggle_pin', 'choose_reference',
                     'go_back', 'go_forward']:
            setattr(app, name, Mock())
        app._install_shortcuts()
        bindings = {c.args[0]: c.args[1] for c in app.root.bind.call_args_list}
        self.assertEqual(bindings['<Control-Shift-N>'](None), 'break')
        self.assertEqual(bindings['<Control-Shift-n>'](None), 'break')
        self.assertEqual(app.new_fleeting.call_count, 2)
