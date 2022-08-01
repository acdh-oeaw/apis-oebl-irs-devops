"""
# Super users can:
- View all
- Retrieve all
- Post
- Patch all
- Delete all

# Editors can:

- View assigned articles
- Not view not assigned articles
- Retrieve assigned articles
- Not retrieve not assigned articles
- Not Post articles
- Not Patch
    - assigned articles
    - not assigned articles
- Not Delete
    - assigned articles
    - not assigned articles

# Authors can:

- View assigned articles
- Not view not assigned articles
- Retrieve assigned articles
- Not retrieve not assigned articles
- Not Post articles
- Not Patch
    - assigned articles
    - not assigned articles
- Not Delete
    - assigned articles
    - not assigned articles
"""


from typing import List

from rest_framework.test import APITestCase
from rest_framework import status

from oebl_editor.models import LemmaArticle
from oebl_irs_workflow.models import Editor, IrsUser, Author, IssueLemma

from oebl_irs_workflow.tests.utilities import SetUpUserMixin
from oebl_editor.tests.utilitites.db_content import create_and_assign_article, create_article


class SuperUserTestCase(SetUpUserMixin, APITestCase):
    """Super users can:
- View all
- Retrieve all
- Patch all
- Delete all
    """
    user: IrsUser
    article: LemmaArticle

    def setUp(self) -> None:
        self.setUpUser()
        self.article = create_article()

    def test_list(self):
        """Super users can: - View all"""
        response = self.client.get('/editor/api/v1/lemma-article/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_articles: List[dict] = response.json()['results']
        self.assertEqual(
            1,
            response_articles.__len__(),
        )
        response_article = response_articles[0]
        self.assertEqual(
            response_article.get('issue_lemma'),
            self.article.pk,
        )

    def test_retrieve_respone(self):
        """Super users can: - Retrieve all"""
        response = self.client.get(
            f'/editor/api/v1/lemma-article/{self.article.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_article: dict = response.json()
        self.assertEqual(
            response_article.get('issue_lemma'),
            self.article.pk,
        )

    def test_patch(self):
        """Super user can: - Patch all"""
        old_published_value = self.article.published
        response = self.client.patch(
            f'/editor/api/v1/lemma-article/{self.article.pk}/',
            data={
                'published': not old_published_value,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get(
            'published'), not old_published_value)
        self.article.refresh_from_db()
        self.assertEqual(self.article.published, not old_published_value)

    def test_delete(self):
        """Super user can: - Delete all"""
        response = self.client.delete(
            f'/editor/api/v1/lemma-article/{self.article.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(LemmaArticle.DoesNotExist):
            LemmaArticle.objects.get(pk=self.article.pk)


class SuperUserPostTestCase(APITestCase, SetUpUserMixin):
    """Super users can post"""
    user: IrsUser
    issue: IssueLemma

    def setUp(self) -> None:
        self.setUpUser()
        self.issue = IssueLemma.objects.create()

    def test_post(self):
        """Super Users can: - Post all"""
        response = self.client.post(
            '/editor/api/v1/lemma-article/',
            data={
                'issue_lemma': self.issue.pk,
            },
            format='json'
        )
        self.assertEqual(response.status_code,
                         status.HTTP_201_CREATED, response.content)
        response_article: dict = response.json()
        self.assertEqual(
            response_article.get('issue_lemma'),
            self.issue.pk,
        )
        self.assertIsNotNone(LemmaArticle.objects.get(pk=self.issue.pk))


class EditorTestCase(APITestCase, SetUpUserMixin):
    """Editors can:
- View assigned articles
- Not view not assigned articles
- Retrieve assigned articles
- Not retrieve not assigned articles
(- Not Post articles)
- Not Patch
    - assigned articles
    - not assigned articles
- Not Delete
    - assigned articles
    - not assigned articles"""

    user: Editor
    assigned_article: LemmaArticle
    not_assigned_article: LemmaArticle

    def setUp(self) -> None:
        self.setUpUser()
        self.not_assigned_article = create_article()
        self.assigned_article = create_and_assign_article(user=self.user)

    def test_list(self):
        """Editors can: - View assigned articles"""
        response = self.client.get('/editor/api/v1/lemma-article/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_articles: List[dict] = response.json()['results']
        self.assertEqual(
            1,
            response_articles.__len__(),
        )
        response_article = response_articles[0]
        self.assertEqual(
            response_article.get('issue_lemma'),
            self.assigned_article.pk,
        )

        self.assertNotEqual(
            response_article.get('issue_lemma'),
            self.not_assigned_article.pk,
        )

    def test_retrieve_assigned_respone(self):
        """Editors can: - Retrieve assigned articles"""
        response = self.client.get(
            f'/editor/api/v1/lemma-article/{self.assigned_article.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_article: dict = response.json()
        self.assertEqual(
            response_article.get('issue_lemma'),
            self.assigned_article.pk,
        )

        self.assertNotEqual(
            response_article.get('issue_lemma'),
            self.not_assigned_article.pk,
        )

    def test_retrieve_not_assigned_respone(self):
        """Editors can: - Not retrieve assigned articles"""
        response = self.client.get(
            f'/editor/api/v1/lemma-article/{self.not_assigned_article.pk}/')
        # This might seem a little unintuitive, but since the user dan not see the article, the user gets a not found.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthorTestCase(EditorTestCase):
    """
Authors can do the same as editors with articles.

Authors can:
- View assigned articles
- Not view not assigned articles
- Retrieve assigned articles
- Not retrieve not assigned articles
(- Not Post articles)
- Not Patch
    - assigned articles
    - not assigned articles
- Not Delete
    - assigned articles
    - not assigned articles"""

    user: Author


class EditorPostCase(SetUpUserMixin, APITestCase):
    """Editors can not post articles"""
    user: Editor
    issue: IssueLemma

    def setUp(self) -> None:
        self.setUpUser()
        self.issue = IssueLemma.objects.create()

    def test_post_article_is_forbidden(self):
        response = self.client.post(
            '/editor/api/v1/lemma-article/',
            data={
                'issue_lemma': self.issue.pk,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuthorPostCase(EditorPostCase):
    """
Editors can not post articles

This is the same as for Editors    
    """
    user: Author
