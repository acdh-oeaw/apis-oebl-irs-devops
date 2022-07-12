

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Optional
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework import status

from oebl_editor import markup
from oebl_editor.models import LemmaArticle, LemmaArticleVersion
from oebl_editor.tests.utilitites.markup import example_markup
from oebl_editor.tests.apitests._abstract_test_prototype import UserInteractionTestCaseArguments
from oebl_editor.tests.apitests.test_lemma_article import ArticleDatabaseTestData, UserArticleInteractionTestCaseProptotype
from oebl_irs_workflow.models import Author, EditTypes, Editor, IrsUser

# -----------------------
# Arguments And Test Data
# -----------------------

@dataclass(init=True, frozen=True, order=False)
class UserArticleVersionInteractionTestCaseArguments(UserInteractionTestCaseArguments):
    update: bool = False
    """If the test updates an existing version, or creates a new one"""
    edit_type: Optional[EditTypes] = None
    """What kind of changes are going to be made"""


@dataclass(init=True, frozen=True, order=False)
class ArticleVersionDatabaseTestData(ArticleDatabaseTestData):
    article: 'LemmaArticle'
    article_version_1: Optional['LemmaArticleVersion'] = None
    article_version_2: Optional['LemmaArticleVersion'] = None

# ---------------
# Test Prototypes
# ---------------


class UserArticleVersionInteractionTestCaseProptotype(UserArticleInteractionTestCaseProptotype, ABC):

    @property
    @abstractmethod
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        raise NotImplementedError

    databaseTestData: ArticleVersionDatabaseTestData

    @property
    def slug(self) -> str:
        return '/editor/api/v1/lemma-article-version/'

    @property
    def version_2_markup(self) -> 'markup.EditorDocument':
        if self.arguments.edit_type is None:
            return example_markup.get_original_version()
        if self.arguments.edit_type == EditTypes.VIEW:
            return example_markup.get_original_version()
        if self.arguments.edit_type == EditTypes.ANNOTATE:
            return example_markup.get_changed_annotations()
        if self.arguments.edit_type == EditTypes.COMMENT:
            return example_markup.get_changed_comment()
        if self.arguments.edit_type == EditTypes.WRITE:
            return example_markup.get_changed_text()
        raise NotImplementedError(rf'Edit Type <{self.arguments.edit_type}> is not impemented.')


    @property
    def target_version(self) -> 'LemmaArticleVersion':
        target_version: 'LemmaArticleVersion'
        if self.arguments.method == 'POST':
            return LemmaArticleVersion.objects.filter(pk=self.responseData['id']).first()
        elif self.arguments.update:
            target_version = self.databaseTestData.article_version_1
        else:
            target_version = self.databaseTestData.article_version_2
        if target_version is None:
            raise RuntimeError(
                rf'Missconfigured Test <{self.arguments.update=} led to None target version')
        return target_version

    def setUpDataBaseTestData(self) -> 'ArticleVersionDatabaseTestData':
        
        # We don't call  super, since on POST we need an base article,
        # contrary to the parent class.
        article = self.setUpAssignmentsAndCreateArticle()
        if self.arguments.method == 'POST':
            return ArticleVersionDatabaseTestData(article=article, issue=article.issue_lemma)
        version_1 = LemmaArticleVersion.objects.create(
            lemma_article = article,
            markup=example_markup.get_original_version()
        )

        if self.arguments.update:
            return ArticleVersionDatabaseTestData(
                issue=article.issue_lemma,
                article=article,
                article_version_1=version_1,
            )
        
        version_2 = LemmaArticleVersion.objects.create(
            lemma_article = article,
            markup = self.version_2_markup,
        )

        return ArticleVersionDatabaseTestData(
                issue=article.issue_lemma,
                article=article,
                article_version_1=version_1,
                article_version_2=version_2,
            )

    def getResponse(self) -> 'Response':
        # Logic gets a little more complex then with articles,
        # so splitting it in methods
        if self.arguments.method == 'POST':
            return self.getResponsePOST()
        if self.arguments.method == 'GET':
            return self.getResponseGET()
        if self.arguments.method == 'Retrieve':
            return self.getResponseGET(pk=self.target_version.pk)
        if self.arguments.method == 'PATCH':
            return self.getResponsePATCH()
        if self.arguments.method == 'DELETE':
            return self.getResponseDELETE()

        raise NotImplementedError(rf'Method <{self.arguments.method}> is not implemented. Put?')


    def getResponsePOST(self) -> 'Response':
        return self.client.post(
            self.slug,
            data={
                'lemma_article': self.databaseTestData.article.pk,
                'markup': self.version_2_markup,  # which is the "original version, on no edit type
            },
            format='json',
        )

    
    def getResponseGET(self, pk: Optional[int] = None) -> 'Response':
        return self.client.get(
            self.slug if pk is None else self.get_slug_with_pk(pk), 
            format='json'
        )

    
    def getResponsePATCH(self) -> 'Response':
        return self.client.patch(
            self.get_slug_with_pk(self.target_version.pk),
            data={
                'markup': self.version_2_markup,
            },
            format='json',
        ) 

    
    def getResponseDELETE(self) -> 'Response':
        return self.client.delete(
            self.get_slug_with_pk(self.databaseTestData.article_version_1.pk),
            format='json',
        )



class SuccessfullPostOrPatchPrototype:

    def test_response_data(self):
        self.assertIsNotNone(
            self.responseData,
            rf'<{self.arguments.method}> a ArticleVersion should return the json of the content.'
        )
        self.assertEqual(
            self.responseData.get('lemma_article'), 
            self.databaseTestData.article.pk,
            rf'<{self.arguments.method}> a ArticleVersion should contain the correct article\'s primary key.'
        )
        self.assertDictEqual(
            self.responseData.get('markup'),
            example_markup.get_original_version() if self.arguments.method == 'POST' else self.version_2_markup,
        )

    def test_database_data(self):
        self.target_version.refresh_from_db()
        self.assertDictEqual(
            self.target_version.markup,
            self.version_2_markup,
        )


class SuccessfullGetPrototype(UserArticleVersionInteractionTestCaseProptotype):

    def test_response_data(self):
        expected_result: List['markup.EditorDocument']
        if  (not self.user.is_superuser) and (self.arguments.assignment_type is None):
            expected_result = []
        else:
            expected_result = [
                self.databaseTestData.article_version_1.markup,
                self.databaseTestData.article_version_2.markup,
            ]
            
        self.assertListEqual(
            [version['markup'] for version in self.responseData['results']],
            expected_result,
            "Result should be empty for not assigned 'Not-Super-Users' and contain both versions for all other"
        )


class SuccessfullRetrievePrototype(UserArticleVersionInteractionTestCaseProptotype):

    def test_response_data(self):    
        self.assertDictEqual(
            self.responseData['markup'],  # Testing for markup, since it is a dict :-)
            self.target_version.markup,
            "This should return the same markup"
        )


# ----------------
# Super User Tests
# ----------------


class SuperUserPostTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            expectedResponseCode=status.HTTP_201_CREATED,
            method='POST',
            shouldHaveBody=True
        )


class SuperUserGetTestCase(SuccessfullGetPrototype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='GET',
            shouldHaveBody=True
        )


class SuperUserRetrieveTestCase(SuccessfullRetrievePrototype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='Retrieve',
            shouldHaveBody=True
        )

class SuperUserPatchWRITETypeTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='PATCH',
            shouldHaveBody=True,
            edit_type=EditTypes.WRITE,
        )


class SuperUserPatchANNOTATETypeTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='PATCH',
            shouldHaveBody=True,
            edit_type=EditTypes.ANNOTATE,
        )


class SuperUserPatchCOMMENTTypeTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='PATCH',
            shouldHaveBody=True,
            edit_type=EditTypes.COMMENT,
        )


class SuperUserDeleteTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=IrsUser,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_204_NO_CONTENT,
            shouldHaveBody=False,
        )



# --------------------------
# Editor Tests: Not Assigned
# --------------------------


class EditorNotAssignedPostTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            method='POST',
            shouldHaveBody=False
        )


class EditorNotAssignedGetTestCase(SuccessfullGetPrototype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='GET',
            shouldHaveBody=True
        )


class EditorNotAssignedRetrieveTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,
            method='Retrieve',
            shouldHaveBody=False
        )

class EditorNotAssignedPatchWRITETypeTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, editor can not see -> 404
            method='PATCH',
            shouldHaveBody=False,
            edit_type=EditTypes.WRITE,
        )


class EditorNotAssignedPatchANNOTATETypeTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, editor can not see -> 404
            method='PATCH',
            shouldHaveBody=False,
            edit_type=EditTypes.ANNOTATE,
        )


class EditorNotAssignedPatchCOMMENTTypeTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, editor can not see -> 404
            method='PATCH',
            shouldHaveBody=False,
            edit_type=EditTypes.COMMENT,
        )


class EditorNotAssignedDeleteTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, editor can not see -> 404
            shouldHaveBody=False,
        )


# --------------------------
# Editor Tests: Assigned
# --------------------------



class EditorAssignedPostTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            expectedResponseCode=status.HTTP_201_CREATED,
            method='POST',
            shouldHaveBody=True
        )


class EditorAssignedGetTestCase(SuccessfullGetPrototype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            expectedResponseCode=status.HTTP_200_OK,
            method='GET',
            shouldHaveBody=True
        )


class EditorAssignedRetrieveTestCase(SuccessfullRetrievePrototype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            expectedResponseCode=status.HTTP_200_OK,
            method='Retrieve',
            shouldHaveBody=True
        )


class EditorAssignedPatchWRITETypeTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            expectedResponseCode=status.HTTP_200_OK,
            method='PATCH',
            shouldHaveBody=True,
            edit_type=EditTypes.WRITE,
        )


class EditorAssignedPatchANNOTATETypeTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            expectedResponseCode=status.HTTP_200_OK,
            method='PATCH',
            shouldHaveBody=True,
            edit_type=EditTypes.ANNOTATE,
        )


class EditorAssignedPatchCOMMENTTypeTestCase(SuccessfullPostOrPatchPrototype, UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            expectedResponseCode=status.HTTP_200_OK,
            method='PATCH',
            shouldHaveBody=True,
            edit_type=EditTypes.COMMENT,
        )


class EditorAssignedDeleteTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Editor,
            assignment_type='EDITOR',
            method='DELETE',
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
        )




# --------------------------
# Author Tests: Not Assigned
# --------------------------


class AuthorNotAssignedPostTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            method='POST',
            shouldHaveBody=False
        )


class AuthorNotAssignedGetTestCase(SuccessfullGetPrototype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            expectedResponseCode=status.HTTP_200_OK,
            method='GET',
            shouldHaveBody=True
        )


class AuthorNotAssignedRetrieveTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,
            method='Retrieve',
            shouldHaveBody=False
        )

class AuthorNotAssignedPatchWRITETypeTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, Author can not see -> 404
            method='PATCH',
            shouldHaveBody=False,
            edit_type=EditTypes.WRITE,
        )


class AuthorNotAssignedPatchANNOTATETypeTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, Author can not see -> 404
            method='PATCH',
            shouldHaveBody=False,
            edit_type=EditTypes.ANNOTATE,
        )


class AuthorNotAssignedPatchCOMMENTTypeTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):
    
    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, Author can not see -> 404
            method='PATCH',
            shouldHaveBody=False,
            edit_type=EditTypes.COMMENT,
        )


class AuthorNotAssignedDeleteTestCase(UserArticleVersionInteractionTestCaseProptotype, APITestCase):

    @property
    def arguments(self) -> UserArticleVersionInteractionTestCaseArguments:
        return UserArticleVersionInteractionTestCaseArguments(
            UserModel=Author,
            assignment_type=None,
            method='DELETE',
            expectedResponseCode=status.HTTP_404_NOT_FOUND,  # Patches an version, Author can not see -> 404
            shouldHaveBody=False,
        )


# --------------------------
# Author Tests: Assigned
# --------------------------


@dataclass(init=True, frozen=True, order=False)
class AuthorPostsArticleVersionTestCaseArguments(UserArticleVersionInteractionTestCaseArguments):
    is_first_post: bool = True
    method: Literal['POST'] = 'POST'


class AuthorPostTestPrototype(UserArticleVersionInteractionTestCaseProptotype, ABC):

    @property
    @abstractmethod
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        raise NotImplemented

    def setUpDataBaseTestData(self) -> 'ArticleVersionDatabaseTestData':
        test_data = super().setUpDataBaseTestData()

        if self.arguments.is_first_post:
            return test_data

        version_1 = LemmaArticleVersion.objects.create(
            lemma_article = test_data.article,
            markup=example_markup.get_original_version()
        )

        return ArticleVersionDatabaseTestData(
            issue=test_data.issue,
            article=test_data.article,
            article_version_1=version_1,
        )



# ********************************************************************
# Authors with write assignemnt can post first and suceeding versions.
# ********************************************************************
        

class AuthorAssignedWriteFirstPostTestCase(SuccessfullPostOrPatchPrototype, AuthorPostTestPrototype, APITestCase):
    
    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            expectedResponseCode=status.HTTP_201_CREATED,
            shouldHaveBody=True,
            is_first_post=True,
        )


class AuthorAssignedWriteSecondPostTestCase(SuccessfullPostOrPatchPrototype, AuthorPostTestPrototype, APITestCase):
    
    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.WRITE,
            expectedResponseCode=status.HTTP_201_CREATED,
            shouldHaveBody=True,
            is_first_post=False,
        )


# **************************************************************************
# Authors with view assignment can neither post first nor suceeding versions.
# ***************************************************************************


class AuthorAssignedViewFirstPostCase(AuthorPostTestPrototype, APITestCase):

    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
            is_first_post=True,
        )


class AuthorAssignedViewSecondPostCase(AuthorPostTestPrototype, APITestCase):

    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.VIEW,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
            is_first_post=False,
        )



# *********************************************************************
# Authors with annotate or comment assignment not post first versions.
# *********************************************************************


class AuthorAssignedCommentFirstPostCase(AuthorPostTestPrototype, APITestCase):

    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.COMMENT,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
            is_first_post=True,
        )


class AuthorAssignedAnnotateFirstPostCase(AuthorPostTestPrototype, APITestCase):

    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
            is_first_post=True,
        )



# **********************************************************************************************
# Authors with annotate or comment assignment can post suceeding versions in their own edit type:
# 
# A = Annotate, C = Comment, W = Write
# 
#       A   C   W
# -------------------      
#   A   +   X   X
#   C   X   +   X
# 
# **********************************************************************************************

# Let's the the permitted ones before: 

## Author Annotate Permitted

class AuthorAssignedAnnotateSecondPostCommentCase(AuthorPostTestPrototype, APITestCase):
    """An author assigned to annotate posts changes in comments"""
    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            edit_type=EditTypes.COMMENT,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
            is_first_post=False,
        )


class AuthorAssignedAnnotateSecondPostWriteCase(AuthorPostTestPrototype, APITestCase):
    """An author assigned to annotate posts changes in text"""

    @property
    def arguments(self) -> AuthorPostsArticleVersionTestCaseArguments:
        return AuthorPostsArticleVersionTestCaseArguments(
            UserModel=Author,
            assignment_type=EditTypes.ANNOTATE,
            edit_type=EditTypes.WRITE,
            expectedResponseCode=status.HTTP_403_FORBIDDEN,
            shouldHaveBody=False,
            is_first_post=False,
        )



