"""
6 types of user: Super user, editor, author: WRITE; ANNOTATE, COMMENT; VIEW
with 2 types of assignments yes/no -> 12 types of users

one article

4 kind of operations: POST / GET / PATCH / DELETE

which makes 4*superuser + 4*author no assignments, + 4 viewtypes * 4 operations

=> 4 + 4 + 16 => 24 : ok

each has two assertions
    - response status code
    - response body
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Type, Union, Literal
from oebl_editor.models import EditTypes, LemmaArticle
from oebl_editor.tests.utilitites.db_content import create_user, createLemmaArticle
from oebl_irs_workflow.models import AuthorIssueLemmaAssignment, Editor, IrsUser, Author, IssueLemma
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status


@dataclass(init=True, frozen=True, order=False)
class _UserInteractionTestCaseArguments:

    UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']]
    assignment_type: Optional[Union['EditTypes', Literal['EDITOR']]]
    method: Union[Literal['GET'], Literal['POST'], Literal['PATCH'], Literal['DELETE']]
    expectedResponseCode: int
    shouldHaveBody: Optional[bool] = True

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
        
        if self.arguments.assignment_type:
            self.article = self.setUpAssignmentsAndCreateArticle()
        else:
            self.article = createLemmaArticle()
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

        raise RuntimeError(rf'Argument method <{self.arguments.method}> is unkown.')

    def setUpAssignmentsAndCreateArticle(self) -> 'LemmaArticle':
        if self.arguments.assignment_type == 'EDITOR':
                if not hasattr(self.user, 'editor'):
                    raise Exception(rf'Can not set author assignments for user who is no author: {self.user}')
                return createLemmaArticle(issue_kwargs={'editor': self.user.editor})
        else:
            if not hasattr(self.user, 'author'):
                raise Exception(rf'Can not set author assignments for user who is no author: {self.user}')
            article = createLemmaArticle()
            AuthorIssueLemmaAssignment.objects.create(
                issue_lemma=article.issue_lemma, 
                author=self.user.author, 
                edit_type=self.arguments.assignment_type
            )
            return article


    def test_api_response(self):
        self.assertEqual(self.arguments.expectedResponseCode, self.response.status_code)
        if self.arguments.shouldHaveBody:
            self.assertEqual(self.response['Content-Type'], 'application/json')


class SuperUserPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
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
            assignment_type=None,
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
            assignment_type=None,
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
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_204_NO_CONTENT,
            shouldHaveBody=False,
        )


class EditorNoAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorNoAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 0)


class EditorNoAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorNoAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )

class EditorAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 1)


class EditorAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorNoAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorNoAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 0)


class AuthorNoAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )



class AuthorNoAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )



class AuthorWriteAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorWriteAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 1)


class AuthorWriteAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorWriteAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )



class AuthorAnnotateAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorAnnotateAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 1)


class AuthorAnnotateAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorAnnotateAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorCommentAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorCommentAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 1)


class AuthorCommentAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorCommentAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorViewAssignmentPost(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorViewAssignmentGet(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.data['results'].__len__(), 1)


class AuthorViewAssignmentPatch(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorViewAssignmentDelete(_AbstractUserInterctionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> _UserInteractionTestCaseArguments:
        return _UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )