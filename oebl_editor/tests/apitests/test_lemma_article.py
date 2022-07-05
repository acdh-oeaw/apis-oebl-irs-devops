"""
6 types of user: Super user, editor, author: WRITE; ANNOTATE, COMMENT; VIEW
with 2 types of permission yes/no -> 12 types of users

one article

4 kind of operations: POST / GET / PATCH / DELETE

which makes 12*4 = 48 tests

each has two assertions
    - response status code
    - response body
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional, Type, Union, Literal, Tuple
from oebl_editor.models import EditTypes, UserArticlePermission
from oebl_editor.tests.utilitites.db_content import create_user, createLemmaArticle
from oebl_irs_workflow.models import Editor, IrsUser, Author, IssueLemma
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status


@dataclass(init=True, frozen=True, order=False)
class _UserInteractionTestCaseArguments:

    UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']]
    permission: Optional['EditTypes']
    method: Union[Literal['GET'], Literal['POST'], Literal['PATCH'], Literal['DELETE']]
    expectedResponseCode: int

class _AbstractUserInterctionTestCaseProptotype(
    ABC, 
    # APITestCase  #  it is a mixin, and this confused the testing framework, but I keep that here, so I can use with IDE
    ):

    slug = '/editor/api/v1/lemma-article/'
    
    @property
    @abstractmethod
    def arguments(self) -> _UserInteractionTestCaseArguments:
        raise NotImplemented

    def setUp(self) -> None:
        username = self.arguments.UserModel.__class__.__name__
        password = 'password'
        self.user = create_user(self.arguments.UserModel, username=username, password=password)
        self.client.login(username=username, password=password)
        if self.arguments.method == 'POST':
            self.response = self.setUpPOST()
        else:
            self.response = self.setUpWithArticle()
        
        try:
            self.data = self.response.json()
        except:
            self.data = None

    def setUpPOST(self) -> 'Response':
        issue_lemma: 'IssueLemma' = IssueLemma.objects.create()
        return self.client.post(
            self.slug,
            data={
                'issue_lemma': issue_lemma.pk
            },
            format='json'
        )

    def setUpWithArticle(self) -> 'Response':
        self.article = createLemmaArticle()
        if self.arguments.permission:
            UserArticlePermission.objects.create(lemma_article=self.article, user=self.user, edit_type=self.arguments.permission)
        
        if self.arguments.method == 'GET':
            return self.client.get(self.slug)
        if self.arguments.method == 'DELETE':
            return self.client.delete(
                rf'{self.slug}{self.article.pk}/',
                data={
                    'issue_lemma': self.article.pk,
                }
            )
        if self.arguments.method == 'PATCH':
            return self.client.patch(
                rf'{self.slug}{self.article.pk}/',
                data={
                    'published': True,
                }
            )

    def test_api_response(self):
        self.assertEqual(self.arguments.expectedResponseCode, self.response.status_code)
        if self.arguments.method == 'DELETE':
            return
        self.assertEqual(self.response['Content-Type'], 'application/json')


class SuperUserPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            permission=None,
            method='POST',
            expectedResponseCode=status.HTTP_201_CREATED,
        )

    def test_has_data(self):
        self.assertIsNotNone(self.data, 'Posting an Article should return the json of the article')

    def test_data_is_has_pk(self):
        self.assertIsInstance(self.data.get('issue_lemma'), int, 'The result of posting an article Lemma, should contain the issue lemmas pk.'),

    def test_data_default_properties(self):
        self.assertFalse(self.data.get('published'), "The default value for published should be false."),
        self.assertIsNone(self.data.get('current_version', False), "When creating an ArticleLemma, there should be no current version yet."),
        

class SuperUserGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            permission=None,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )
     
    def test_has_data(self):
        self.assertIsNotNone(self.data, 'Geting an Article should return the json of the article')
        self.assertIn('results', self.data, 'The articles should be stored in results')
        results = self.data['results']
        self.assertIsInstance(results, list)
        self.assertEqual(results.__len__(), 1)

    def test_data_is_has_pk(self):
        self.assertTrue(
            all((result.get('issue_lemma').__class__ is int for result in self.data['results']))
        )


class SuperUserPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            permission=None,
            method='PATCH',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_has_data(self):
        self.assertIsNotNone(self.data, 'Patching an Article should return the json of the article')

    def test_data_is_has_pk(self):
        self.assertIsInstance(self.data.get('issue_lemma'), int, 'The result of patching an article Lemma, should contain the issue lemmas pk.'),

    def test_data_default_properties(self):
        self.assertTrue(self.data.get('published'), "The published property, should be changed to True"),
        self.assertIsNone(self.data.get('current_version', False), "Current Version should not be changed"),
    
    def test_path_worked(self):
        self.article.refresh_from_db()
        self.assertTrue(self.article.published)
     
   
class SuperUserDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            permission=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_204_NO_CONTENT,
        )
