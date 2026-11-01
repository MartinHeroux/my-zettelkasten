import unittest
from pathlib import Path
from zettelkasten.app import completion_matches

class OrderingTests(unittest.TestCase):
    def setUp(self):
        self.notes = [
            {'path': Path('/tmp/a.md'), 'title':'Cortical control', 'content':'a', 'modified':2},
            {'path': Path('/tmp/b.md'), 'title':'Force production', 'content':'mentions cortical', 'modified':9},
            {'path': Path('/tmp/c.md'), 'title':'Coordination', 'content':'c', 'modified':3},
            {'path': Path('/tmp/d.md'), 'title':'Visual feedback', 'content':'d', 'modified':4},
            {'path': Path('/tmp/e.md'), 'title':'Force constraints', 'content':'e', 'modified':1},
        ]
    def test_prefix_before_substring(self):
        self.assertEqual([n['title'] for n in completion_matches(self.notes, None, 'co')], ['Coordination', 'Cortical control', 'Force constraints'])
    def test_case_insensitive(self):
        self.assertEqual(len(completion_matches(self.notes, None, 'COR')), 1)
    def test_content_fallback(self):
        self.assertEqual(completion_matches(self.notes, None, 'mentions')[0]['title'], 'Force production')
    def test_empty_recent(self):
        self.assertEqual(completion_matches(self.notes, None, '')[0]['title'], 'Force production')
    def test_exclude_current(self):
        self.assertNotIn('Coordination', [n['title'] for n in completion_matches(self.notes, Path('/tmp/c.md'), 'co')])

if __name__ == '__main__': unittest.main()
