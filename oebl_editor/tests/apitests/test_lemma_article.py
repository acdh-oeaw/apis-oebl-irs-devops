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
from oebl_editor.models import EditTypes
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
    checkResultAssertions: List[
        Tuple[
            Callable[
                [dict], # Servers response json
                bool, # success
            ],  # Assertion callback for assertTrue
            str,  # assertion message
        ]
    ]




class _AbstractUserInterctionTestCaseProptotype(
    ABC, 
    # APITestCase  #  it is a mixin, and this confused the testing framework, but I keep that here, so I can use with IDE
    ):
    
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
            return
        else:
            self.response = self.setUpWithArticle()
            return

    def setUpPOST(self) -> 'Response':
        issue_lemma: 'IssueLemma' = IssueLemma.objects.create()
        return self.client.post(
            '/editor/api/v1/lemma-article/',
            data={
                'issue_lemma': issue_lemma.pk
            },
            format='json'
        )

    def test_api_response(self):
        self.assertEqual(self.response['Content-Type'], 'application/json')
        self.assertEqual(self.arguments.expectedResponseCode, self.response.status_code)
        if self.arguments.checkResultAssertions.__len__() == 0:
            return
        data = self.response.json()
        for assertTrue, message in self.arguments.checkResultAssertions:
            self.assertTrue(assertTrue(data), message)


class SuperUserPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            permission=None,
            method='POST',
            expectedResponseCode=status.HTTP_201_CREATED,
            checkResultAssertions=[
                (lambda data: data.__len__() > 0, 'Posting an Article should return the json of the article'),
                (lambda data: data.get('issue_lemma').__class__ is int, 'The result of posting an article Lemma, should contain the issue lemmas pk.'),
                (lambda data: data.get('published') == False, "The default value for published should be false."),
                (lambda data: data.get('current_version') == None, "When creating an ArticleLemma, there should be no current version yet."),
            ]
        )



     