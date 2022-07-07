"""
Test oebl_editor.queries
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Type, Union
from unittest import TestCase
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User

from oebl_editor.models import EditTypes, LemmaArticle, LemmaArticleVersion

from oebl_editor.queries import check_if_docs_diff_regarding_mark_types, create_get_query_set_method_filtered_by_user, extract_marks_flat, get_last_version
from oebl_editor.tests.utilitites.db_content import VersionGenerator, createLemmaArticle
from oebl_editor.tests.utilitites.markup import create_a_document
from oebl_irs_workflow.models import Author, AuthorIssueLemmaAssignment, Editor, IrsUser

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
        self.assertEqual(version, None)
        
    def test_query_last_version_with_update(self):
        version = get_last_version(self.version_1, update=True)
        self.assertEqual(version, self.version_1)


class DynamicFilterQuerySetMethodTestCasePrototype(ABC):
    """
    Prototype for all versions o this function
    """ 

    @property
    @abstractmethod
    def Model(self) -> Union[ Type['LemmaArticle'], Type['LemmaArticleVersion'], ]:
         raise NotImplemented

    @abstractmethod
    def create_test_instances(self, article_1: 'LemmaArticle', article_2: 'LemmaArticle') -> None:
        raise NotImplemented

    @property
    @abstractmethod
    def lemma_article_key(self) -> str:
        raise NotImplemented

    def setUp(self) -> None:
        """
        1. Create an author, an editor and an super user.
        2. Create one article, with assignments for editor and author, and one with no assignments.
        3. If model not article create one model for each.
        4. Create fake view and method.
        """
        # 1. Create an editor and an super user
        self.author = Author.objects.create(username='Author')
        self.editor = Editor.objects.create(username='Editor')
        self.superuser = IrsUser.objects.create_superuser(username='Superuser')

        # 2. Create one article, with assignments for both users and one with no assignments.
        article_without_assignment = createLemmaArticle()
        article_with_assignment = createLemmaArticle(issue_kwargs={'editor': self.editor})
        
        author_assignment: 'AuthorIssueLemmaAssignment' = AuthorIssueLemmaAssignment.objects.create(
            issue_lemma = article_with_assignment.issue_lemma,
            author = self.author,
            edit_type = EditTypes.WRITE,
        )
        author_assignment.save()

        # 3. If model not article create one model for each.
        if self.Model is not LemmaArticle:
            self.create_test_instances(article_with_assignment, article_without_assignment)

        class FakeView:
            def __init__(self, fakeuser: User):
                class Request:
                    user: User = fakeuser
                self.request = Request

            get_queryset = create_get_query_set_method_filtered_by_user(self.Model, self.lemma_article_key)


        self.fakeSuperUserView = FakeView(fakeuser=self.superuser)
        self.fakeEditorView = FakeView(fakeuser=self.editor)
        self.fakeAuthorView = FakeView(fakeuser=self.author)

    def test_super_user_gets_it_all(self):
        """test super user gets 2 models (of right type)"""
        result = self.fakeSuperUserView.get_queryset().all()
        self.assertEqual(result.__len__(), 2)
        self.assertTrue(all(model.__class__ is self.Model for model in result))

        
    def test_editor_gets_only_his_own(self):
        """test editor user gets 1 model (of right type)"""
        result = self.fakeEditorView.get_queryset().all()
        self.assertEqual(result.__len__(), 1)
        self.assertTrue(all(model.__class__ is self.Model for model in result))

    def test_author_gets_only_his_own(self):
        """test author user gets 1 model (of right type)"""
        result = self.fakeAuthorView.get_queryset().all()
        self.assertEqual(result.__len__(), 1)
        self.assertTrue(all(model.__class__ is self.Model for model in result))

    
class LemmaArticleFilterQuerySetMethodTestCase(DynamicFilterQuerySetMethodTestCasePrototype, DjangoTestCase):
    
    @property
    def Model(self) -> Type['LemmaArticle']:
        return LemmaArticle

    @property
    def lemma_article_key(self) -> str:
        return 'pk'

    def create_test_instances(self, article_1: 'LemmaArticle', article_2: 'LemmaArticle') -> None:
        return  # They are already there


class LemmaArticleVersionFilterQuerySetMethodTestCase(DynamicFilterQuerySetMethodTestCasePrototype, DjangoTestCase):
    
    @property
    def Model(self) -> Type['LemmaArticleVersion']:
        return LemmaArticleVersion

    @property
    def lemma_article_key(self) -> str:
        return 'lemma_article'

    def create_test_instances(self, article_1: 'LemmaArticle', article_2: 'LemmaArticle') -> None:
        v1 = LemmaArticleVersion(lemma_article=article_1, markup={})
        v1.save()
        v2 = LemmaArticleVersion(lemma_article=article_2, markup={})
        v2.save()
