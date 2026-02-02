import unittest

from matita.reference import MarkdownTree

test_text = open("tests/test_doc_page.md", "rt").read()
test_tree = MarkdownTree(test_text)

class TestParser(unittest.TestCase):

    def test_front_matter(self):
        fm = test_tree.front_matter.variables
        self.assertEqual(fm["title"], "Lorem Ipsum")
        self.assertEqual(fm["tags"], "consectetaur adipisicing")
        self.assertEqual(fm["color"], "sed do eiusmod tempor")
    
    def test_sections(self):
        self.assertEqual(test_tree.sections[0].title, "")
        self.assertEqual(test_tree.sections[0].paragraphs[0].txt, "At vero eos et accusamus.")
        self.assertEqual(test_tree.sections[0].paragraphs[1].txt, "Praesentium voluptatum.")
        self.assertEqual(test_tree.sections[1].title, "Section A")
        self.assertEqual(test_tree.sections[1].paragraphs[0].txt, "Lorem ipsum\ndolor sit amet.")
        self.assertEqual(test_tree.sections[1].level, 1)
        self.assertEqual(test_tree.sections[2].title, "Section B")
        self.assertEqual(test_tree.sections[2].paragraphs[0].txt, "Excepteur sint occaecat.")
        self.assertEqual(test_tree.sections[2].level, 2)
        self.assertEqual(test_tree.sections[6].title, "Section F")
        self.assertEqual(test_tree.sections[6].paragraphs[0].txt, "Sed quia consequuntur.")
        self.assertEqual(test_tree.sections[6].level, 2)
    
    def test_sections_by_level(self):
        self.assertEqual(test_tree.sections_by_level(2)[1].title, "Section C")
    
    def test_sections_by_title(self):
        self.assertEqual(test_tree.sections_by_title("on C")[0].title, "Section C")

    def test_table_parsing(self):
        table_paragraph = test_tree.sections_by_title("Section G")[0].paragraphs[1]
        self.assertTrue(table_paragraph.is_table)
        rows = table_paragraph.table.rows
        self.assertEqual(rows[0][0], "Lorem")
        self.assertEqual(rows[2][1], "e")
        self.assertEqual(rows[3][2], "i")
