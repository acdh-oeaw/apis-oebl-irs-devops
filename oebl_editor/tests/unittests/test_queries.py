"""
Test oebl_editor.queries
"""

from unittest import TestCase

from oebl_editor.queries import extract_marks_flat


class TestExtractMarksFlat(TestCase):
    
    def test_flat(self):
        node_type = 'example_node_type'
        marks = [
            {'type': node_type, 'text': 'mark1'},
            {'type': node_type, 'text': 'mark2'},
        ]
        node = {'type': 'someparenttype', 'marks': marks}
        result = list(extract_marks_flat(node, node_type))
        self.assertEqual(marks, result)
        