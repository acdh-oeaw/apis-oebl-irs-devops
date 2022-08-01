from typing import TYPE_CHECKING, Optional, Union, Literal, Tuple
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from oebl_irs_workflow.models import Author, Editor
from oebl_irs_workflow.models import IssueLemma, AuthorIssueLemmaAssignment

if TYPE_CHECKING:
    from rest_framework.request import Request
    from django.contrib.auth.models import User
    from oebl_irs_workflow.api_views import IssueLemmaViewset, AuthorIssueLemmaAssignmentViewSet
    from oebl_irs_workflow.models import IrsUser



class IssueLemmaEditorAssignmentPermissions(permissions.BasePermission):


    def has_permission(self, request: 'Request', view: 'IssueLemmaViewset') -> bool:
        
        user: 'User' = request.user

        # Super user can do it all
        if user.is_superuser:
            return True

        # Only super users can assign editors to issue lemmas.
        if request.method == 'POST':
            return 'editor' not in request.data

        # Only super users can query, editors not themselves.
        if request.method == 'GET' and 'editor' in request.GET:
            editor_param: str = request.GET['editor']
            # No validation here
            if not editor_param.isdigit():
                return False
            return request.user.pk == int(editor_param)

        return True


    def has_object_permission(self, request: 'Request', view: 'IssueLemmaViewset', obj: 'IssueLemma'):
        
        user: 'User' = request.user

        # Super user can do it all
        if user.is_superuser:
            return True

        # Only super users can delete an editor assignment.
        if request.method == 'DELETE' and obj.editor is not None:
            return False

        # Only super users can change an editor assignment.
        if request.method in ('PATCH', 'PUT', ):
            old_editor_id: Optional[int] = getattr(obj.editor, 'pk', None)
            new_editor_id: Optional[int] = request.data.get('editor', None)
            return old_editor_id == new_editor_id
        
        return True


def extract_permission_relevant_user_type(user: 'User') -> Union['Author', 'Editor']:
    
    irsuser: 'IrsUser' = user.irsuser
    if hasattr(irsuser, 'editor'):
        return irsuser.editor
    if hasattr(irsuser, 'author'):
        return irsuser.author
    raise PermissionDenied('Only authors and editors are allowed')


class AuthorIssueLemmaAssignmentPermissions(permissions.BasePermission): 
    """
    The rules in has_permission and has_object_permission overlap a little and are a little confuse.
    I will go on in developing the app, and hopefully come back after and refacor that. 
    But time is limited.
    """

    
    def has_permission(self, request: 'Request', view: 'AuthorIssueLemmaAssignmentViewSet') -> bool:
        
        user: 'User' = request.user

        # Super user can do it all
        if user.is_superuser:
            return True

        # These are handled by querysets and has_object_permission. Post and query ?issue_lemma need to be handled here.
        is_post = request.method == 'POST'
        is_issue_lemma_query = (request.method == 'GET') and ('issue_lemma' in request.GET)
        if not is_post and not is_issue_lemma_query:
            return True

        permission_relevant_user = extract_permission_relevant_user_type(user)
        
        if is_post:
            # Authors can't add content.
            if permission_relevant_user.__class__ is Author:
                return False

            permission_relevant_user: 'Editor'
        
            return self.editor_has_object_permission_including_post_requests(permission_relevant_user, request, assignment=None)

        elif is_issue_lemma_query:
            return self.has_permissions_for_issue_lemma_query(permission_relevant_user, int(request.GET['issue_lemma']))

        else:
            # (╥_╥)
            return RuntimeError('Bad programming! Logic Error!')
        

    def has_object_permission(
            self, 
            request: 'Request', 
            view: 'AuthorIssueLemmaAssignmentViewSet', 
            obj: 'AuthorIssueLemmaAssignment'
        ) -> bool:
        
        user: 'User' = request.user

        # Super user can do it all
        if user.is_superuser:
            return True

        method: Union[Literal['DELETE'], Literal['PATCH'], Literal['PUT'], Literal['GET']] = request.method

        permission_relevant_user = extract_permission_relevant_user_type(user)

        # Authors can't change content.
        if permission_relevant_user.__class__ is Author:
            if method == 'GET':
                return permission_relevant_user == obj.author
            # Authors can't change content.
            else:
                return False

        permission_relevant_user: 'Editor'

        return self.editor_has_object_permission_including_post_requests(permission_relevant_user, request, obj)


    def editor_has_object_permission_including_post_requests(
            self, 
            editor: 'Editor',
            request: 'Request',  
            assignment: Optional['AuthorIssueLemmaAssignment']
        ) -> bool:
        """
        Checks if editor is assigned to the issue lemma of an author issue assignment

        If assignment is not provided an method is post, will look up issue lemma in the post request, 
        else throw an TypeError
        """
        
        if editor.__class__ is not Editor:
            raise TypeError('Bad programming. Type guards do not work.')

        if assignment is not None:
           issue_lemma = assignment.issue_lemma
        elif request.method == 'POST':
            issue_lemma = IssueLemma.objects.get(pk=request.data['issue_lemma'])
        # ༼☯﹏☯༽        
        else:
            raise TypeError('Bad programming. Type guards do not work.')

        return issue_lemma.editor == editor

    def has_permissions_for_issue_lemma_query(self, user: Union[Editor, Author], issue_lemma_id: int) -> bool:
        if user.__class__ is Editor:
            return IssueLemma.objects.get(pk=issue_lemma_id).editor == user
        elif user.__class__ is Author:
            return AuthorIssueLemmaAssignment.objects.filter(issue_lemma=issue_lemma_id, author=user).exists()
        else:
            # (༎ຶ⌑༎ຶ)
            raise TypeError('Bad programming. Type guards do not work.')

        
        

