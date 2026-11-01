import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zettelkasten.bibliography import parse_bib, read_bib, BibError, paper_template, paper_matches
from zettelkasten.collection import scan

SAMPLE = r'''@article{garcia2024Reach,
  title = {Reaching under {{Force Constraints}}},
  author = {García, Ana and Smith, John},
  year = 2024,
  journal = {Motor Research},
  volume = {12}, number = {3}, pages = {11--25},
  doi = {10.5555/test},
  note = {Some notes. \par \textbf{Bold} and {nested} braces.}
}
@book{lee2020Book, title = {A {Book}}, author = {Lee, B.}, year = 2020, publisher = {Fictional Press}}
'''
class TestBib(unittest.TestCase):
    def test_parse_nested_and_unicode(self):
        refs = parse_bib(SAMPLE)
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs['garcia2024Reach'].title, 'Reaching under Force Constraints')
        self.assertIn('garcía', refs['garcia2024Reach'].search_text)
        self.assertIn('12(3)', refs['garcia2024Reach'].full_reference())
        self.assertIn('nested', refs['garcia2024Reach'].field('note'))
    def test_invalid_file(self):
        with self.assertRaises(BibError): parse_bib('@article{broken, title={oops}')
    def test_paper_association(self):
        ref = parse_bib(SAMPLE)['garcia2024Reach']
        with TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes/'n_123.md').write_text(paper_template(ref))
            inventory = scan(notes)
            self.assertEqual(len(paper_matches(inventory, ref.key)), 1)
            self.assertEqual(inventory[0]['source_key'], ref.key)
            self.assertIn('## My observations and questions', inventory[0]['content'])
    def test_real_export(self):
        real = Path('/mnt/data/My Library.bib')
        if real.exists():
            refs = read_bib(real)
            self.assertGreater(len(refs), 400)
            self.assertIn('aiyegbusiConsiderationsPatientPublic2023', refs)
if __name__ == '__main__': unittest.main()
