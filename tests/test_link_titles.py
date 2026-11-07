import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zettelkasten.collection import update_placeholder_links
from zettelkasten.storage import ExternalChangeError


class LinkTitleTests(unittest.TestCase):
    def test_resolves_placeholders_preserves_custom_labels_and_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / 'n_target.md'
            target.write_text('# A title\n')
            source = root / 'n_source.md'
            original = ('[New linked idea](n_target.md)\n'
                        '[New Linked Note](./n_target.md#section)\n'
                        '[My wording](n_target.md)\n'
                        '[New linked idea](n_other.md)\n'
                        '![New linked idea](n_target.md)\n'
                        '`[New linked idea](n_target.md)`\n'
                        '```md\n[New linked idea](n_target.md)\n```\n')
            source.write_text(original)
            recovery = root / 'recovery'
            self.assertEqual(update_placeholder_links(root, target, '# A [title]\n', recovery), [])
            expected = original.replace('[New linked idea](n_target.md)', '[A \\[title\\]](n_target.md)', 1)
            expected = expected.replace('[New Linked Note](./n_target.md#section)', '[A \\[title\\]](./n_target.md#section)')
            self.assertEqual(source.read_text(), expected)
            self.assertEqual(next(recovery.glob('*.md')).read_text(), original)
            update_placeholder_links(root, target, '# Later title', recovery)
            self.assertEqual(source.read_text(), expected)

    def test_blank_title_waits_and_conflicts_are_reported(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / 'n_target.md'
            source = root / 'n_source.md'
            original = '[New linked idea](n_target.md)'
            source.write_text(original)
            self.assertEqual(update_placeholder_links(root, target, '# \n\n## Connections', root / 'recovery'), [])
            self.assertEqual(source.read_text(), original)
            with patch('zettelkasten.storage.save_note', side_effect=ExternalChangeError):
                self.assertEqual(update_placeholder_links(root, target, '# Title', root / 'recovery'), [source.name])
            self.assertEqual(source.read_text(), original)
