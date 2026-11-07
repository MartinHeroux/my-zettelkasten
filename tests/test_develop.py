from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch
from zettelkasten.app import EditorApp

class DevelopTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.app=EditorApp.__new__(EditorApp)
        app=self.app; app.root=Mock()
        app.inbox_dir=base/'inbox'; app.inbox_dir.mkdir()
        app.notes_dir=base/'notes'; app.notes_dir.mkdir()
        app.recovery_dir=base/'recovery'; app.recovery_dir.mkdir()
        self.source=app.inbox_dir/'n_source.md'; self.source.write_text('# Thought\nUseful insight')
        self.recovery=app.recovery_dir/'n_source.old.md'; self.recovery.write_text('old')
        app.path=self.source; app.history=[(self.source,'1.0',0)]; app.future=[]
        app._guard_unsaved=Mock(return_value=True)
        for name in ('refresh_inventory','_refresh_inbox_count','_update_history_buttons','_set_status'):
            setattr(app,name,Mock())
        def load(path):
            self.assertTrue(path.exists())
            self.assertTrue(self.source.exists())
            app.path=path
            return True
        app._load=Mock(side_effect=load)

    def test_success_saves_content_before_deleting_source_and_versions(self):
        self.app.develop_fleeting()
        self.assertFalse(self.source.exists()); self.assertFalse(self.recovery.exists())
        self.assertIn('Useful insight',self.app.path.read_text())
        self.assertIn('category: idea',self.app.path.read_text())
        self.assertEqual(self.app.history,[])

    def test_save_failure_preserves_source_and_versions(self):
        with patch('zettelkasten.app.save_note', side_effect=OSError('disk full')), patch('zettelkasten.app.messagebox.showerror'):
            self.app.develop_fleeting()
        self.assertTrue(self.source.exists()); self.assertTrue(self.recovery.exists())
        self.app._load.assert_not_called()

    def test_open_failure_preserves_source_and_versions(self):
        self.app._load=Mock(return_value=False)
        self.app.develop_fleeting()
        self.assertTrue(self.source.exists()); self.assertTrue(self.recovery.exists())

    def test_cleanup_failure_keeps_saved_permanent_note(self):
        with patch.object(Path,'unlink',side_effect=PermissionError('read only')), patch('zettelkasten.app.messagebox.showwarning') as warning:
            self.app.develop_fleeting()
        self.assertTrue(self.source.exists()); self.assertTrue(self.app.path.exists())
        warning.assert_called_once()
