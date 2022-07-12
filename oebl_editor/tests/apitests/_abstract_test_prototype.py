
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, Type, Literal, Optional, TYPE_CHECKING

from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework import status


from oebl_editor.tests.utilitites.db_content import create_user

if TYPE_CHECKING:
    from oebl_irs_workflow.models import Editor, IrsUser, Author, EditTypes


@dataclass(init=True, frozen=True, order=False)
class UserInteractionTestCaseArguments:

    UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']] = 'IrsUser'
    assignment_type: Optional[Union['EditTypes', Literal['EDITOR']]] = None
    method: Union[
        Literal['POST'], Literal['PATCH'], Literal['DELETE'],
        Literal['GET'], # with no id param
        Literal['Retrieve'], # Get with id param, named after the django viewset method. 
        ] = 'GET'
    expectedResponseCode: int = status.HTTP_200_OK
    shouldHaveBody: Optional[bool] = True


@dataclass(init=True, frozen=True, order=False)
class DatabaseTestData(ABC):
    """Empty container for real subclasses"""
    pass

class UserInteractionTestCaseProptotype(
        ABC, 
        # APITestCase  #  it is a mixin, and this confused the testing framework, but I keep that here, so I can use with IDE
    ):

    @property
    @abstractmethod
    def arguments(self) -> UserInteractionTestCaseArguments:
        raise NotImplemented

    @property
    @abstractmethod
    def slug(self) -> str:
        raise NotImplemented

    def get_slug_with_pk(self, pk: int):
        parts = (part.strip(r'/') for part in (self.slug, str(pk)))
        middle = r'/'.join(parts)
        return rf'/{middle}/'

    user: Union['IrsUser', 'Editor', 'Author']
    databaseTestData: DatabaseTestData
    response: 'Response'
    responseData: Optional[dict]

    def setUp(self):
        self.user = self.setUpUser()
        self.databaseTestData = self.setUpDataBaseTestData()
        self.response = self.getResponse()
        try:
            self.responseData = self.response.json()
        except:
            self.responseData = None

    def setUpUser(self):
        username = self.arguments.UserModel.__class__.__name__
        password = 'password'
        user = create_user(self.arguments.UserModel, username=username, password=password)
        self.client.login(username=username, password=password)
        return user


    @abstractmethod
    def setUpDataBaseTestData(self):
        raise NotImplemented

    @abstractmethod
    def getResponse(self):
        raise NotImplemented

    def test_api_response(self):
        self.assertEqual(self.arguments.expectedResponseCode, self.response.status_code)
        if self.arguments.shouldHaveBody:
            self.assertEqual(self.response['Content-Type'], 'application/json')
   