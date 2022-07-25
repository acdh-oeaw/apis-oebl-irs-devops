"""On Top Of The Django Permission System, We Have Our Own Bussiness Flow Logic.

The Logic is defined in the serializers modules. Here are the uttility functions.
"""
from abc import ABC
from typing import TYPE_CHECKING, Optional, Union
from rest_framework import permissions
from rest_framework.exceptions import NotFound, ValidationError

from oebl_editor.models import LemmaArticleVersion
from oebl_irs_workflow.models import AuthorIssueLemmaAssignment, Author, Editor, IrsUser
from oebl_editor.models import LemmaArticle


if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from rest_framework.request import Request
    from oebl_editor.views import LemmaArticleVersionViewSet


class LemmaArticleVersionPermissions(permissions.BasePermission):
    """Who can get, post, patch and delete an LemmaArticleVersion
    """

    def extract_relevant_user_object(self, request: 'Request') -> Optional[Union['User', 'Editor', 'Author', ]]:
        user: 'User' = request.user
        if user.is_superuser:
            return user
        if not hasattr(user, 'irsuser'):
            return None
        irsuser: 'IrsUser' = user.irsuser
        if hasattr(irsuser, 'author'):
            return irsuser.author
        if hasattr(irsuser, 'editor'):
            return irsuser.editor
        return None



    def has_permission(self, request: 'Request', view: 'LemmaArticleVersionViewSet') -> bool:
        user = self.extract_relevant_user_object(request)
        if user is None:
            return False
        if user.is_superuser:
            return True
        # Filter out DELETE and exotic request types
        if request.method not in ('GET', 'PATCH', 'PUT', 'POST', ):
            return False
        # All this user types can get data, 
        # but the data is limited through query sets in the view
        if request.method == 'GET':
            return True
        # These are handled in has_object_permission
        if request.method in ('PATCH', 'PUT',):
            return True  
        
        # Unfortunatly this is not the case for POST requests.
        if request.method == 'POST':
            return self.has_object_permission_for_post_requests(request, user)

        return False

    def has_object_permission_for_post_requests(self, request: 'Request', user: Union['Editor', 'Author', ]):
        
        lemma_article_id = request.data.get('lemma_article')

        if lemma_article_id is None:
            raise ValidationError('field "lemma_article" is required')

        if user.__class__ is Author:
            return self.check_author_assignments(user, lemma_article_id)

        elif user.__class__ is Editor:
            try:
                article = LemmaArticle.objects.get(pk=lemma_article_id)

            except LemmaArticle.DoesNotExist:
                raise NotFound(
                    f'No article found for id <{article}>')

            return self.check_editor_assignment(user, article)

        else:
            raise RuntimeError(
                'Programming logic error. ' 
                f'The type of user is restricted to Editor or Author here, but is {user.__class__}'
            )


    def has_object_permission(self, request: 'Request', view, obj: 'LemmaArticleVersion') -> bool:
        user = self.extract_relevant_user_object(request)
        # Only Superuser, Editor and Author have permissions
        if user is None:
            return False
        # Super users can do anything
        if user.is_superuser:
            return True
        # Nobody else can delete
        if request.method == 'DELETE':
            return False
        # Retrieve actions are handled via query sets -> 404, if not assigned
        if request.method == 'GET':
            return True

        # All others need to have assignments, based on their user type:
        user_is_assigned: bool

        if user.__class__ is Author:
            user_is_assigned = self.check_author_assignments(user, obj.lemma_article.pk)
        elif user.__class__ is Editor:
            user_is_assigned = self.check_editor_assignment(user, obj.lemma_article)
        else:
            raise RuntimeError(
                'Programming logic error. ' 
                f'The type of user is restricted to Editor or Author here, but is {user.__class__}'
            )

        # If not assigned, no further checks
        if user_is_assigned is False:
            return False

        # If assigned: Check if patch/put are for the latest versions. If not: Prohibited.
        return self.check_if_is_latest_version(obj)

    
    def check_if_is_latest_version(self, version: 'LemmaArticleVersion'):
        # All others can only handle the latest versions
        newer_versions = LemmaArticleVersion.objects.filter(
            lemma_article=version.lemma_article,
            date_created__gt=version.date_created,
        )

        return not newer_versions.exists()

    def check_author_assignments(self, author: 'Author', lemma_article_id: int) -> bool:
       # Check custom assignments: user can only handle assigned content.
        return AuthorIssueLemmaAssignment.objects.filter(
            author=author,
            issue_lemma=lemma_article_id  # which is identical to issue_lemma_id
        ).exists()

    def check_editor_assignment(self, editor: 'Editor', article: LemmaArticle) -> bool:
        return editor == article.issue_lemma.editor


class AbstractReadOnlyPermissionViewSetMixin(ABC):

    def get_permissions(self):
        if self.action in ('list', 'retrieve', ):
            return [permissions.IsAuthenticated(), ]
        else:
            return [permissions.IsAdminUser(), ]
