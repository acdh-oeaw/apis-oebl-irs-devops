"""
Test oebl_editor.queries
"""

from abc import ABC, abstractmethod
from typing import Type, Union
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User

from oebl_editor.models import EditTypes, LemmaArticle, LemmaArticleVersion

from oebl_editor.queries import create_get_query_set_method_filtered_by_user, get_last_version
from oebl_editor.tests.utilitites.db_content import VersionGenerator, create_article
from oebl_irs_workflow.models import Author, AuthorIssueLemmaAssignment, Editor, IrsUser


class TwoVersionQueryTestCase(DjangoTestCase):

    def setUp(self) -> None:
        article = create_article()
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
        article = create_article()
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
    def Model(self) -> Union[Type['LemmaArticle'], Type['LemmaArticleVersion'], ]:
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
        article_without_assignment = create_article()
        article_with_assignment = create_article(
            issue_kwargs={'editor': self.editor})

        author_assignment: 'AuthorIssueLemmaAssignment' = AuthorIssueLemmaAssignment.objects.create(
            issue_lemma=article_with_assignment.issue_lemma,
            author=self.author,
            edit_type=EditTypes.WRITE,
        )
        author_assignment.save()

        # 3. If model not article create one model for each.
        if self.Model is not LemmaArticle:
            self.create_test_instances(
                article_with_assignment, article_without_assignment)

        class FakeView:
            def __init__(self, fakeuser: User):
                class Request:
                    user: User = fakeuser
                self.request = Request

            get_queryset = create_get_query_set_method_filtered_by_user(
                self.Model, self.lemma_article_key)

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
