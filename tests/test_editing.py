"""Clipboard regressions without requiring a desktop."""
import tkinter as tk
from unittest import TestCase
from unittest.mock import Mock
from zettelkasten.app import EditorApp

class EditingTests(TestCase):
    def setUp(self):
        self.app = EditorApp.__new__(EditorApp)
        self.app.text = Mock()
        self.app._close_popup = Mock()
        self.app.text.tag_ranges.return_value = ('1.0', '1.5')
        self.app.text.get.return_value = 'hello'

    def test_copy_does_not_modify_text(self):
        self.assertEqual(self.app._edit_action('copy'), 'break')
        self.app.text.clipboard_append.assert_called_once_with('hello')
        self.app.text.delete.assert_not_called()

    def test_cut_copies_before_deleting(self):
        self.app._edit_action('cut')
        calls = self.app.text.method_calls
        self.assertLess(next(i for i,c in enumerate(calls) if c[0]=='clipboard_append'),
                        next(i for i,c in enumerate(calls) if c[0]=='delete'))

    def test_paste_replaces_selection(self):
        self.app.text.clipboard_get.return_value = 'replacement'
        self.app._edit_action('paste')
        self.app.text.delete.assert_called_once_with('sel.first', 'sel.last')
        self.app.text.insert.assert_called_once_with('insert', 'replacement')

    def test_empty_clipboard_preserves_selection(self):
        self.app.text.clipboard_get.side_effect = tk.TclError('empty')
        self.app._edit_action('paste')
        self.app.text.delete.assert_not_called()
        self.app.text.insert.assert_not_called()

    def test_copy_cut_without_selection_preserve_clipboard(self):
        self.app.text.tag_ranges.return_value = ()
        for action in ('copy','cut'):
            self.app._edit_action(action)
        self.app.text.clipboard_clear.assert_not_called()
        self.app.text.delete.assert_not_called()
