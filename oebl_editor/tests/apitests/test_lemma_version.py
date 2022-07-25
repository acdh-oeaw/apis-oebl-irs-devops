"""

# Super users can:
- View all 
- Retrieve all
- Post all
- Patch all
- Delete all

# Authors can:

- View all versions of their assigned articles.
- Retrieve all versions of their assigned articles.
- Can not retrieve versions from articles, they are not assigned to.
- Post versions for their assigned articles.
- Can not post versions for articles, they are not assigned to.
- Patch **LATEST** versions of their assigned articles.
- Can not PATCH not latest versions of their assigned articles.
- Can not PATCH any versions of article, they are not assigned to.
- Not Delete any versions.


# Editors can:

- View all versions of their assigned articles.
- Retrieve all versions of their assigned articles.
- Can not retrieve versions from articles, they are not assigned to.
- Post versions for their assigned articles.
- Can not post versions for articles, they are not assigned to.
- Patch **LATEST** versions of their assigned articles.
- Can not PATCH not latest versions of their assigned articles.
- Can not PATCH any versions of article, they are not assigned to.
- Not Delete any versions.

"""
from typing import List
from oebl_editor.tests.utilitites.markup import create_a_document
from rest_framework.test import APITestCase
from rest_framework import status

from oebl_editor.models import LemmaArticle, LemmaArticleVersion
from oebl_irs_workflow.models import Author, EditTypes, Editor, IrsUser

from oebl_editor.tests.utilitites.db_content import SetUpUserMixin, VersionGenerator, create_and_assign_article, create_article


class SuperUserPostCase(SetUpUserMixin, APITestCase):
    """Super user can post versions to articles"""
    user: IrsUser
    article: LemmaArticle

    def setUp(self) -> None:
        self.setUpUser()
        self.article = create_article()

    def test_post_version(self):
        markup = {}
        response = self.client.post(
            '/editor/api/v1/lemma-article-version/',
            data={
                'lemma_article': self.article.pk,
                'markup': markup,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version_id = response.json().get('id')
        self.assertIsInstance(version_id, int)
        version_from_database: LemmaArticleVersion = LemmaArticleVersion.objects.get(
            pk=version_id)
        self.assertIsNotNone(version_from_database)
        self.assertDictEqual(version_from_database.markup, markup)


class EditorPostCase(SetUpUserMixin, APITestCase):
    """Editors can: 
- Post versions for their assigned articles
- Can not post versions for their assigned articles
"""

    user: Editor
    assigned_article: LemmaArticle
    not_assigned_article: LemmaArticle

    def setUp(self) -> None:
        self.setUpUser()
        self.not_assigned_article = create_article()
        self.assigned_article = create_and_assign_article(self.user)

    def test_post_version_to_assigned_article(self):
        """Editors and authors can post versions for their assigned articles."""
        markup = {}
        response = self.client.post(
            '/editor/api/v1/lemma-article-version/',
            data={
                'lemma_article': self.assigned_article.pk,
                'markup': markup,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version_id = response.json().get('id')
        self.assertIsInstance(version_id, int)
        version_from_database: LemmaArticleVersion = LemmaArticleVersion.objects.get(
            pk=version_id)
        self.assertIsNotNone(version_from_database)
        self.assertDictEqual(version_from_database.markup, markup)

    def test_post_version_to_not_assigned_article(self):
        """Editors and authors can not post versions for articles, they are not assigned too."""
        markup = {}
        response = self.client.post(
            '/editor/api/v1/lemma-article-version/',
            data={
                'lemma_article': self.not_assigned_article.pk,
                'markup': markup,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuthorPostCase(EditorPostCase):
    """
For POST this is the same as for editors
Authors can: 
- Post versions for their assigned articles
- Can not post versions for their assigned articles
"""
    user: Author


class SuperUserCase(SetUpUserMixin, APITestCase):
    """# Super users can:
- View all 
- Retrieve all
(- Post all)
- Patch all
- Delete all
    """
    user: IrsUser
    article_version: LemmaArticleVersion
    markup: dict

    def setUp(self) -> None:
        self.setUpUser()
        self.markup = {}
        self.article_version = LemmaArticleVersion.objects.create(
            lemma_article=create_article(),
            markup=self.markup,
        )

    def test_list(self):
        """Super users can view all"""
        response = self.client.get('/editor/api/v1/lemma-article-version/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        versions: List[dict] = response.json().get('results')
        self.assertEqual(versions.__len__(), 1)
        version = versions[0]
        self.assertEqual(version.get('id'), self.article_version.pk)

    def test_retrieve(self):
        """Super users can retrieve all"""
        response = self.client.get(
            f'/editor/api/v1/lemma-article-version/{self.article_version.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        version: dict = response.json()
        self.assertEqual(version.get('id'), self.article_version.pk)

    def test_patch(self):
        """Super users can patch all"""
        patched_markup = {'patched': 'markup'}
        assert patched_markup != self.markup
        response = self.client.patch(
            f'/editor/api/v1/lemma-article-version/{self.article_version.pk}/',
            data={
                'markup': patched_markup,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article_version.refresh_from_db()
        self.assertDictEqual(self.article_version.markup, patched_markup)

    def test_delete(self):
        """Super users can delete"""
        response = self.client.delete(
            f'/editor/api/v1/lemma-article-version/{self.article_version.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(LemmaArticleVersion.DoesNotExist):
            LemmaArticleVersion.objects.get(pk=self.article_version.pk)


class EditorTestCase(SetUpUserMixin, APITestCase):
    """Authors can:

- View all versions of their assigned articles.
- Retrieve all versions of their assigned articles.
- Can not retrieve versions from articles, they are not assigned to.
(- Post versions for their assigned articles.)
(- Can not post versions for articles, they are not assigned to.)
- Patch **LATEST** versions of their assigned articles.
- Can not PATCH not latest versions of their assigned articles.
- Can not PATCH any versions of article, they are not assigned to.
- Not Delete any versions."""

    user: Editor
    not_assigned_version: LemmaArticleVersion
    first_assigned_version: LemmaArticleVersion
    latest_assigned_version: LemmaArticleVersion
    markup_v1: dict
    markup_v2: dict

    def setUp(self) -> None:
        self.setUpUser()
        article_not_assigned = create_article()
        markup_generator = dict
        self.markup_v1 = markup_generator()
        self.markup_v2 = {'patched': 'markup'}
        self.not_assigned_version = LemmaArticleVersion.objects.create(
            lemma_article=article_not_assigned, markup=self.markup_v1)
        article_assigned = create_and_assign_article(self.user)

        version_generator = VersionGenerator()
        version_generator.add_versions_to_article(
            article=article_assigned, n=2, markup_generator=dict)
        self.first_assigned_version, self.latest_assigned_version = version_generator.versions

        assert self.first_assigned_version.date_created < self.latest_assigned_version.date_created
        assert self.first_assigned_version.date_modified < self.latest_assigned_version.date_modified

    def test_list(self):
        response = self.client.get('/editor/api/v1/lemma-article-version/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        versions: List[dict] = response.json().get('results')
        self.assertEqual(versions.__len__(), 2)
        version_ids = {version.get('id') for version in versions}
        self.assertSetEqual(
            version_ids, {self.first_assigned_version.pk, self.latest_assigned_version.pk, })
        self.assertNotIn(self.not_assigned_version.pk, version_ids)

    def test_retrieve_assigned(self):
        response = self.client.get(
            f'/editor/api/v1/lemma-article-version/{self.first_assigned_version.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get(
            'id'), self.first_assigned_version.pk)

        response = self.client.get(
            f'/editor/api/v1/lemma-article-version/{self.latest_assigned_version.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get(
            'id'), self.latest_assigned_version.pk)

    def test_retrieve_not_assigned(self):
        response = self.client.get(
            f'/editor/api/v1/lemma-article-version/{self.not_assigned_version.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_latest_assigned(self):
        response = self.client.patch(
            f'/editor/api/v1/lemma-article-version/{self.latest_assigned_version.pk}/',
            data={
                'markup': self.markup_v2,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.latest_assigned_version.refresh_from_db()
        self.assertDictEqual(
            self.markup_v2, self.latest_assigned_version.markup)

    def test_patch_not_latest_assigned(self):
        response = self.client.patch(
            f'/editor/api/v1/lemma-article-version/{self.first_assigned_version.pk}/',
            data={
                'markup': self.markup_v2,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.first_assigned_version.refresh_from_db()
        self.assertDictEqual(
            self.markup_v1, self.first_assigned_version.markup)

    def test_patch_not_assigned(self):
        response = self.client.patch(
            f'/editor/api/v1/lemma-article-version/{self.not_assigned_version.pk}/',
            data={
                'markup': self.markup_v2,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.first_assigned_version.refresh_from_db()
        self.assertDictEqual(
            self.markup_v1, self.first_assigned_version.markup)

    def test_delete(self):

        self.assertEqual(
            status.HTTP_403_FORBIDDEN,
            self.client.delete(
                f'/editor/api/v1/lemma-article-version/{self.not_assigned_version}/').status_code
        )
        self.assertIsNotNone(LemmaArticleVersion.objects.get(
            pk=self.not_assigned_version.pk))

        self.assertEqual(
            status.HTTP_403_FORBIDDEN,
            self.client.delete(
                f'/editor/api/v1/lemma-article-version/{self.first_assigned_version}/').status_code
        )
        self.assertIsNotNone(LemmaArticleVersion.objects.get(
            pk=self.first_assigned_version.pk))

        self.assertEqual(
            status.HTTP_403_FORBIDDEN,
            self.client.delete(
                f'/editor/api/v1/lemma-article-version/{self.latest_assigned_version}/').status_code
        )
        self.assertIsNotNone(LemmaArticleVersion.objects.get(
            pk=self.latest_assigned_version.pk))


class AuthorTestCase(EditorTestCase):
    """Authors can do the same as Editors:

- View all versions of their assigned articles.
- Retrieve all versions of their assigned articles.
- Can not retrieve versions from articles, they are not assigned to.
(- Post versions for their assigned articles.)
(- Can not post versions for articles, they are not assigned to.)
- Patch **LATEST** versions of their assigned articles.
- Can not PATCH not latest versions of their assigned articles.
- Can not PATCH any versions of article, they are not assigned to.
- Not Delete any versions."""

    user: Author


class NoRestrictionsOnMarkupTestCase(SetUpUserMixin, APITestCase):
    """
    In the first implementation, the server checked that authors would only change,
    what they have been assigned too. We decided to move this restrictions entirely
    to the frontend, hence anything is allowed.

    This test is part of TDD, to make sure all restrictions are removed.

    When all restrictions are removed, 
    this test will be pointless as checking, 
    that you can use the word "unicorn" in documents, 
    but will be most likely not removed,
    to remember that fun but needless validation code.
    """
    user: Author
    version_view: LemmaArticleVersion
    version_comment: LemmaArticleVersion
    version_annotate: LemmaArticleVersion
    version_write: LemmaArticleVersion

    n_annotations = 1
    comment_text = 'comment'

    def setUp(self) -> None:
        self.setUpUser()
        # It has 35 degrees outside. I am lazy.
        self.version_view, self.version_comment, self.version_annotate, self.version_write = [
            VersionGenerator().add_versions_to_article(
                article=create_and_assign_article(self.user, edit_type),
                n=1,
                markup_generator=lambda: create_a_document(
                    number_of_annotations=self.n_annotations, comment_text=self.comment_text)
            ).versions[0]
            for edit_type in EditTypes
        ]

    def test_markup_can_be_anything(self):
        response = self.client.patch(
            f'/editor/api/v1/lemma-article-version/{self.version_view.pk}/',
            data={
                'markup': False,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.version_view.refresh_from_db()
        self.assertEqual(self.version_view.markup, False)

        response = self.client.patch(
            f'/editor/api/v1/lemma-article-version/{self.version_write.pk}/',
            data={
                'markup': False,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.version_write.refresh_from_db()
        self.assertEqual(self.version_write.markup, False)

    def test_commenting_works_when_not_assigned(self):
        # The markup has a changed comment,
        new_markup = create_a_document(comment_text=self.comment_text + '!')
        response = self.client.patch(
            # but the user is only assigned to annotate.
            f'/editor/api/v1/lemma-article-version/{self.version_annotate.pk}/',
            data={
                'markup': new_markup,
            },
            format='json',
        )
        # But the server does not care,
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.version_annotate.refresh_from_db()
        # and updates the data anyway.
        self.assertEqual(self.version_annotate.markup, new_markup)

    def test_annotating_works_when_not_assigned(self):
        # The markup got new annotations,
        new_markup = create_a_document(
            number_of_annotations=self.n_annotations + 1)
        response = self.client.patch(
            # but the user is only assigned to comment.
            f'/editor/api/v1/lemma-article-version/{self.version_comment.pk}/',
            data={
                'markup': new_markup,
            },
            format='json',
        )
        # But the server does not care,
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.version_comment.refresh_from_db()
        # and updates the data anyway.
        self.assertEqual(self.version_comment.markup, new_markup)

    def test_annotating_works_when_not_assigned_post(self):
        # The markup got new annotations,
        new_markup = create_a_document(
            number_of_annotations=self.n_annotations + 1)
        response = self.client.post(
            # but the user is only assigned to comment.
            f'/editor/api/v1/lemma-article-version/',
            data={
                'markup': new_markup,
                'lemma_article': self.version_comment.lemma_article.pk,
            },
            format='json',
        )
        # But the server does not care,
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(
            new_markup,
            # and updates the data anyway
            LemmaArticleVersion.objects.get(pk=response.json()['id']).markup,
        )

    def test_commenting_works_when_not_assigned_post(self):
        # The markup got new annotations,
        new_markup = create_a_document(comment_text=self.comment_text + '!')
        response = self.client.post(
            # but the user is only assigned to comment.
            f'/editor/api/v1/lemma-article-version/',
            data={
                'markup': new_markup,
                'lemma_article': self.version_annotate.lemma_article.pk,
            },
            format='json',
        )
        # But the server does not care,
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(
            new_markup,
            # and updates the data anyway
            LemmaArticleVersion.objects.get(pk=response.json()['id']).markup,
        )
