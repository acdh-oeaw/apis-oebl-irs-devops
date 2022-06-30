"""
Test oebl_editor.queries
"""

from typing import TYPE_CHECKING
from unittest import TestCase, result

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
        
    
    def test_mixed_mark_types(self):
        mark_type_1 = 'mark_type_1'
        mark_type_2 = 'mark_type_2'
        
        mark1, mark2, mark3 = marks = [{'type': mark_type_1, 'text': 'mark1'}, {'type': mark_type_2, 'text': 'mark2'}, {'type': mark_type_1, 'text': 'mark3'}]
        node: 'AbstractBaseNode' = {'type': 'parentnode', 'marks': marks}
        
        result1 = list(extract_marks_flat(node, mark_type_1))
        self.assertEqual(result1, [mark1, mark3])
        
        result2 = list(extract_marks_flat(node, mark_type_2))
        self.assertEqual(result2, [mark2, ])
        
        
    def test_mixed_nested(self):
        mark_type_1 = 'mark_type_1'
        mark_type_2 = 'mark_type_2'
        
        mark1, mark2, mark3 = marks = [{'type': mark_type_1, 'text': 'mark1'}, {'type': mark_type_2, 'text': 'mark2'}, {'type': mark_type_1, 'text': 'mark3'}]
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
        
        result1 = list(extract_marks_flat(parent_node, mark_type_1))
        self.assertEqual(result1, [mark1, mark3])
        
        result2 = list(extract_marks_flat(parent_node, mark_type_2))
        self.assertEqual(result2, [mark2, ])

         
        
        