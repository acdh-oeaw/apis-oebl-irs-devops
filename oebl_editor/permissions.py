"""On Top Of The Django Permission System, We Have Our Own Bussiness Flow Logic.

The Logic is defined in the serializers modules. Here are the uttility functions.
"""
from abc import ABC
from typing import Literal, Set, Union, TYPE_CHECKING
from rest_framework import permissions
from rest_framework.exceptions import ValidationError, NotFound

from oebl_editor.models import LemmaArticleVersion
from oebl_irs_workflow.models import Author, AuthorIssueLemmaAssignment, Editor, IrsUser
from oebl_editor.queries import check_if_docs_diff_regarding_mark_types, get_last_version
from oebl_editor.models import EditTypes, LemmaArticle, node_edit_type_mapping

    
if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.contrib.auth.models import User
    from rest_framework.request import Request

    

class LemmaArticleVersionPermissions(permissions.BasePermission):
    """Who can get, post, patch and delete an LemmaArticleVersion
    """

    def has_permission(self, request: 'Request', view):
        user: 'User' = request.user
        # Super user can do everything
        if user.is_superuser:
            return True

        if not hasattr(user, 'irsuser'):
            return False
        
        irsuser: 'IrsUser' = user.irsuser

        if (not hasattr(irsuser, 'author')) and (not hasattr(irsuser, 'editor')):
            return False

        if request.method == 'POST':
            return self.checkPostRequestForEditorsAndAuthors(request.data, irsuser)

        # All others are cool or handled by has_object_permission
        return True


    def has_object_permission(self, request: 'Request', view, obj: 'LemmaArticleVersion') -> bool:
        """
        Custom Business Logic For Editor Changes

        First check for super user, than for either editor or author in distinct methods        
        """

        user: 'User' = request.user
        new_version = obj
        method: Union[Literal['GET'], Literal['DELETE'], Literal['PATCH']] = request.method
        """This is a little overboard, but allows, to better show the narrowing down of possibillites."""
        # Super users can do anything        
        if user.is_superuser:
            return self.checkSuperUserPermissions()

        if not hasattr(user, 'irsuser'):
            return False
        
        irsuser: 'IrsUser' = user.irsuser

        if hasattr(irsuser, 'editor'):
            return self.checkEditorPermissions(user.editor, method, new_version)

        if hasattr(irsuser, 'author'):
            return self.checkAuthorPermissions(user.author, method, new_version)

        return False

    def checkPostRequestForEditorsAndAuthors(self, data: dict, irsuser: 'IrsUser') -> bool:
        # At this point, we have to check content for our business logic,   
        # even if this means, we kind of validate data here … 
        # But if not, we would trigger a 500-error, while checking the permissions.

        markup = data.get('markup')

        if markup is None:
            raise ValidationError('Missing markup')

        lemma_id = data.get('lemma_article')

        if lemma_id is None:
            raise ValidationError('Missing lemma article')

        try:
            lemma_article = LemmaArticle.objects.get(pk=data['lemma_article'])
        except LemmaArticle.DoesNotExist:
            raise NotFound(f'Lemma Article <{lemma_id}> not found')

        new_version = LemmaArticleVersion(
            markup=lemma_id, 
            lemma_article=lemma_article
        )
        
        if hasattr(irsuser, 'editor'):
            return self.checkEditorPermissions(irsuser.editor, 'POST', new_version)
        
        if hasattr(irsuser, 'author'):
            return self.checkAuthorPermissions(irsuser.author, 'POST', new_version)

        return False


    def checkSuperUserPermissions(self) -> bool:
        return True

    def checkEditorPermissions(self, editor: 'Editor', method: Union[Literal['GET'], Literal['POST'], Literal['PATCH'], Literal['DELETE'], ], new_version: 'LemmaArticleVersion') -> bool:
        
        if method == 'DELETE':
            return False
        # Checks if the chain LemmaArticleVersion.LemmaArticle.IssueLemma.Editor is the current editor.
        return editor == new_version.lemma_article.issue_lemma.editor
        

    def checkAuthorPermissions(self, author: 'Author', method: Union[Literal['GET'], Literal['POST'], Literal['PATCH'], Literal['DELETE'], ], new_version: 'LemmaArticleVersion') -> bool:
        
        if method == 'DELETE':
            return False

        # Get custom assignments: user can only handle assigned content.
        user_has_this_article_assignments_query_set: 'QuerySet' = AuthorIssueLemmaAssignment.objects.filter(
            author = author,
            issue_lemma = new_version.lemma_article.issue_lemma
        ).all()
        
        # No assigned content -> bye bye
        if user_has_this_article_assignments_query_set.__len__() == 0:
            return False
        
        # With GET any assignment type is ok (because the "least" is VIEW)
        if method == 'GET':
            return True
        #  method: Literal['POST', 'PATCH']
        
        # Have a set of Enums instead of query set of objects, for easier
        user_has_this_article_assignments: Set[EditTypes] = {assignment.edit_type for assignment in user_has_this_article_assignments_query_set}
                
        # Everything is allowed for write    
        if EditTypes.WRITE in user_has_this_article_assignments:
            return True
        
        if {EditTypes.VIEW} == user_has_this_article_assignments:
            # With only VIEW and method: Literal['POST', 'PATCH'], please leave
            return False
            
        # Remaining Edit Types are ANNOTATE AND COMMENT.
        # Remaining methods are: POST and PATCH. They are treated the same.
        last_version = get_last_version(new_version, update = method == 'PATCH')
        
        # It is not possible to write a first version, without "WRITE". Annotation and comments are not stand alone content. They need text.
        if last_version is None:
            return False
        
        # Check which node types, the user is not allowed to change.
        prohibited_node_types = (
            node_type
            for edit_type, node_type
            in node_edit_type_mapping.items()
            if edit_type not in user_has_this_article_assignments
        )
        
        return check_if_docs_diff_regarding_mark_types(prohibited_node_types, new_version, last_version)

    
class AbstractReadOnlyPermissionViewSetMixin(ABC):
    
    def get_permissions(self):
        if self.action in ('list', 'retrieve', ):
            return [permissions.IsAuthenticated(), ]
        else:
            return [permissions.IsAdminUser(), ]
    