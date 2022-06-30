"""
Test oebl_editor.queries
"""

from typing import TYPE_CHECKING
from unittest import TestCase

from oebl_editor.queries import extract_marks_flat

if TYPE_CHECKING:
    from oebl_editor.markup import AbstractBaseNode
    

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
        
        
    def test_nested(self):
        node_type = 'example_node_type'
        mark1, mark2, mark3 = marks = [{'type': node_type, 'text': 'mark1'}, {'type': node_type, 'text': 'mark2'}, {'type': node_type, 'text': 'mark3'}]
        parent_node: 'AbstractBaseNode' = {
            'type': 'paragraph',
            'marks': [mark1, ],
            'content': [
                {
                    'type': 'somechildnode',
                    'marks': [
                        mark2, mark3, 
                    ]
                },
            ]
        }
        result = list(extract_marks_flat(parent_node, node_type))
        self.assertEqual(marks, result)
        
        