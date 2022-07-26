from typing import TYPE_CHECKING
from rest_framework import permissions

if TYPE_CHECKING:
    from rest_framework.request import Request
    from django.contrib.auth.models import User
    from oebl_irs_workflow.models import IssueLemma
    from oebl_irs_workflow.api_views import IssueLemmaViewset



class IssueLemmaEditorAssignmentPermissions(permissions.BasePermission):


    def has_permission(self, request: 'Request', view: 'IssueLemmaViewset') -> bool:
        
        user: 'User' = request.user

        # Super user can do it all
        if user.is_superuser:
            return True

        # Only super users can assign editors to issue lemmas.
        if request.method == 'POST':
            return 'editor' not in request.data

        return False


    def has_object_permission(self, request: 'Request', view: 'IssueLemmaViewset', obj: 'IssueLemma'):
        
        user: 'User' = request.user

        # Super user can do it all
        if user.is_superuser:
            return True

        # Only super users can delete an editor assignment
        if request.method == 'DELETE' and obj.editor is not None:
            return False
        
        return True

    