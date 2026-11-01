import unittest
from zettelkasten.highlighting import spans


class HighlightTests(unittest.TestCase):
    def test_basic_markdown(self):
        source = "# Heading\n**bold** and *italic* [paper](n_a.md) [@smith2024] `code`\n"
        kinds = [s.kind for s in spans(source)]
        for kind in ("heading1", "bold", "italic", "link", "citation", "inlinecode"):
            self.assertIn(kind, kinds)

    def test_code_fence_excludes_inner_markdown(self):
        source = "```md\n# not heading\n**not bold**\n```\n# Real\n"
        result = spans(source)
        self.assertEqual(len([s for s in result if s.kind == "heading1"]), 1)
        self.assertNotIn("bold", [s.kind for s in result])

    def test_escaped_emphasis(self):
        self.assertNotIn("italic", [s.kind for s in spans(r"\*literal*" )])

    def test_offsets_unicode(self):
        source = "Café ☕ **bold**"
        result = next(s for s in spans(source) if s.kind == "bold")
        self.assertEqual(source[result.start:result.end], "**bold**")


if __name__ == "__main__":
    unittest.main()
