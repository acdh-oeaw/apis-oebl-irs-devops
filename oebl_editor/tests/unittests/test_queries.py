"""
Test oebl_editor.queries
"""

from pydoc import doc
from typing import TYPE_CHECKING
from unittest import TestCase, result
from django.test import TestCase as DjangoTestCase

from oebl_editor.queries import check_if_docs_diff_regarding_mark_types, extract_marks_flat, get_last_version
from oebl_editor.tests.utilitites.db_content import VersionGenerator, createLemmaArticle
from oebl_editor.tests.utilitites.markup import create_a_document

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
        
        self.assertTrue(
            all(
                (mark['type'] == mark_type_1 for mark in result1)
            )
        )
        
        self.assertTrue(
            all(
                (mark['type'] == mark_type_2 for mark in result2)
            )
        )
        
    def test_mixed_nested(self):
        mark_type_1 = 'mark_type_1'
        mark_type_2 = 'mark_type_2'
        
        mark1, mark2, mark3 = [{'type': mark_type_1, 'text': 'mark1'}, {'type': mark_type_2, 'text': 'mark2'}, {'type': mark_type_1, 'text': 'mark3'}]
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
        
        self.assertTrue(
            all(
                (mark['type'] == mark_type_1 for mark in result1)
            )
        )
        
        self.assertTrue(
            all(
                (mark['type'] == mark_type_2 for mark in result2)
            )
        )
        
        
    def test_copy_of_real_doc(self):
        doc = create_a_document()
        annotations = list(extract_marks_flat(doc, 'annotation'))
        self.assertEqual(annotations.__len__(), 1)
        comments = list(extract_marks_flat(doc, 'comment'))
        self.assertEqual(comments.__len__(), 1)

         
         
class TestDocDiff(TestCase):
        
        def test_no_changes(self):
            doc1 = create_a_document()
            doc2 = create_a_document()
            
            annotate_diff = check_if_docs_diff_regarding_mark_types(
                {'annotation', },
                doc1,
                doc2,
            )
            
            self.assertFalse(annotate_diff)
            
            comment_diff = check_if_docs_diff_regarding_mark_types(
                {'comment', },
                doc1,
                doc2,
            )
            
            self.assertFalse(comment_diff)
            
            any_diff = check_if_docs_diff_regarding_mark_types(
                {'annotation', 'comment', },
                doc1,
                doc2,
            )
            
            self.assertFalse(any_diff)
            
        def test_added_annotation(self):
            doc1 = create_a_document(number_of_annotations=1)
            doc2 = create_a_document(number_of_annotations=2)
            
            self.assertTrue(
                check_if_docs_diff_regarding_mark_types(
                    {'annotation', },
                    doc1,
                    doc2
                )
            )
            
        def test_changed_comment(self):
            doc1 = create_a_document(comment_text='Comment 1')
            doc2 = create_a_document(comment_text='Comment 2')
            
            self.assertTrue(
                check_if_docs_diff_regarding_mark_types(
                    {'comment', },
                    doc1,
                    doc2
                )
            )
            
        def test_for_annotations_with_changed_comment(self):
            """Just to be sure"""
            doc1 = create_a_document(comment_text='Comment 1')
            doc2 = create_a_document(comment_text='Comment 2')
            
            self.assertFalse(
                check_if_docs_diff_regarding_mark_types(
                    {'annotation', },
                    doc1,
                    doc2
                )
            )
            
        def test_for_all_with_one_change(self):
            """Just to be sure"""
            doc1 = create_a_document(comment_text='Comment 1')
            doc2 = create_a_document(comment_text='Comment 2')
            
            self.assertTrue(
                check_if_docs_diff_regarding_mark_types(
                    {'annotation', 'comment'},
                    doc1,
                    doc2
                )
            )
            
        def test_all_with_changes(self):
            """Just to be sure"""
            doc1 = create_a_document(comment_text='Comment 1', number_of_annotations=0)
            doc2 = create_a_document(comment_text='Comment 2', number_of_annotations=2)
            
            self.assertTrue(
                check_if_docs_diff_regarding_mark_types(
                    {'annotation', 'comment'},
                    doc1,
                    doc2
                )
            )
            
            
class TwoVersionQueryTestCase(DjangoTestCase):
    
    def setUp(self) -> None:
        article = createLemmaArticle()
        version_generator = VersionGenerator()
        version_generator.add_versions_to_article(article, n=2)
        self.version_1, self.version_2 = version_generator.versions
        
    def test_query_last_version_with_no_update(self):
        version = get_last_version(self.version_2, update=False)
        self.assertEqual(version, self.version_1)
        
    def test_query_last_version_with_update(self):
        version = get_last_version(self.version_2, update=True)
        self.assertEqual(version, self.version_2)



class OneVersionQueryTestCase(DjangoTestCase):
    
    def setUp(self) -> None:
        article = createLemmaArticle()
        version_generator = VersionGenerator()
        version_generator.add_versions_to_article(article, n=1)
        self.version_1 = version_generator.versions[0]
        
    def test_query_last_version_with_no_update(self):
        version = get_last_version(self.version_1, update=False)
        self.assertEqual(version, self.version_1)
        
    def test_query_last_version_with_update(self):
        version = get_last_version(self.version_1, update=True)
        self.assertEqual(version, self.version_1)