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


from abc import ABC
from dataclasses import dataclass
from typing import Optional
from oebl_editor.models import EditTypes, LemmaArticle
from oebl_editor.tests.utilitites.db_content import createLemmaArticle
from oebl_irs_workflow.models import AuthorIssueLemmaAssignment, Editor, IrsUser, Author, IssueLemma
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status

from ._abstract_test_prototype import UserInteractionTestCaseArguments, UserInteractionTestCaseProptotype, DatabaseTestData


@dataclass(init=True, frozen=True, order=False)
class ArticleDatabaseTestData(DatabaseTestData):
    issue: 'IssueLemma'
    article: Optional['LemmaArticle'] = None

class UserArticleInteractionTestCaseProptotype(
        UserInteractionTestCaseProptotype,
        ABC,
    ):

    databaseTestData: ArticleDatabaseTestData

    @property
    def slug(self) -> str:
        return '/editor/api/v1/lemma-article/'

    def setUpDataBaseTestData(self):
        # When posting, we only need the Issue Lemma in the database
        if self.arguments.method == 'POST':
            return ArticleDatabaseTestData(
                issue= IssueLemma.objects.create()
            )
        
        article = self.setUpAssignmentsAndCreateArticle()
            
        return ArticleDatabaseTestData(
            issue=article.issue_lemma,
            article=article
        )

    def setUpAssignmentsAndCreateArticle(self) -> 'LemmaArticle':

        if not self.arguments.assignment_type:
            return createLemmaArticle()

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

    def getResponse(self) -> 'Response':
        if self.arguments.method == 'POST':
            return self.client.post(
                self.slug,
                data={
                    'issue_lemma': self.databaseTestData.issue.pk,
                },
                format='json'
            )

        elif self.arguments.method == 'GET':
            return self.client.get(self.slug)
        
        elif self.arguments.method == 'PATCH':
            return self.client.patch(
                self.get_slug_with_pk(self.databaseTestData.article.pk),
                data={
                    'published': True,
                }
            )
        elif self.arguments.method == 'DELETE':
             return self.client.delete(
                self.get_slug_with_pk(self.databaseTestData.article.pk),
            )
        
        else:
            raise RuntimeError(rf'Argument method <{self.arguments.method}> is not supported. Put out.')


class SuperUserPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            method='POST',
            expectedResponseCode=status.HTTP_201_CREATED,
        )

    def test_has_data(self):
        self.assertIsNotNone(self.responseData, 'Posting an Article should return the json of the article')

    def test_data_is_has_pk(self):
        self.assertIsInstance(self.responseData.get('issue_lemma'), int, 'The result of posting an article Lemma, should contain the issue lemmas pk.'),

    def test_data_default_properties(self):
        self.assertFalse(self.responseData.get('published'), "The default value for published should be false."),
        self.assertIsNone(self.responseData.get('current_version', False), "When creating an ArticleLemma, there should be no current version yet."),
        

class SuperUserGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )
     
    def test_has_data(self):
        self.assertIsNotNone(self.responseData, 'Geting an Article should return the json of the article')
        self.assertIn('results', self.responseData, 'The articles should be stored in results')
        results = self.responseData['results']
        self.assertIsInstance(results, list)
        self.assertEqual(results.__len__(), 1)

    def test_data_is_has_pk(self):
        self.assertTrue(
            all((result.get('issue_lemma').__class__ is int for result in self.responseData['results']))
        )


class SuperUserPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            method='PATCH',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_has_data(self):
        self.assertIsNotNone(self.responseData, 'Patching an Article should return the json of the article')

    def test_data_is_has_pk(self):
        self.assertIsInstance(self.responseData.get('issue_lemma'), int, 'The result of patching an article Lemma, should contain the issue lemmas pk.'),

    def test_data_default_properties(self):
        self.assertTrue(self.responseData.get('published'), "The published property, should be changed to True"),
        self.assertIsNone(self.responseData.get('current_version', False), "Current Version should not be changed"),
    
    def test_path_worked(self):
        self.databaseTestData.article.refresh_from_db()
        self.assertTrue(self.databaseTestData.article.published)
     
   
class SuperUserDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_204_NO_CONTENT,
            shouldHaveBody=False,
        )


class EditorNoAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorNoAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 0)


class EditorNoAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorNoAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )

class EditorAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 1)


class EditorAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class EditorAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorNoAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorNoAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 0)


class AuthorNoAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )



class AuthorNoAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )



class AuthorWriteAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorWriteAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 1)


class AuthorWriteAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorWriteAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )



class AuthorAnnotateAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorAnnotateAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 1)


class AuthorAnnotateAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorAnnotateAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorCommentAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorCommentAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 1)


class AuthorCommentAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorCommentAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorViewAssignmentPost(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='POST',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )


class AuthorViewAssignmentGet(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='GET',
            expectedResponseCode=status.HTTP_200_OK,
        )

    def test_data_is_empty(self):
        self.assertEqual(self.responseData['results'].__len__(), 1)


class AuthorViewAssignmentPatch(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='PATCH',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
        
class AuthorViewAssignmentDelete(UserArticleInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserInteractionTestCaseArguments:
        return UserInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )
