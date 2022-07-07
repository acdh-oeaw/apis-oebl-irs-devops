"""On Top Of The Django Permission System, We Have Our Own Bussiness Flow Logic.

The Logic is defined in the serializers modules. Here are the uttility functions.
"""
from abc import ABC
from typing import Literal, Set, Union, TYPE_CHECKING
from rest_framework import permissions
from oebl_editor.queries import check_if_docs_diff_regarding_mark_types, get_last_version
from oebl_editor.models import EditTypes, UserArticlePermission, node_edit_type_mapping
    
    
if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.contrib.auth.models import User
    from rest_framework.request import Request
    from oebl_editor.models import LemmaArticleVersion

    

class LemmaArticleVersionPermissions(permissions.BasePermission):
    """Who can get, post, patch and delete an LemmaArticleVersion
    """
    
    def has_object_permission(self, request: 'Request', view, obj: 'LemmaArticleVersion') -> bool:
        """
        Custom Business Logic For Editor Changes
        
        This is quite long decision tree, with a ĺot of returns: 8. 
        Currently I think, this is the best way to impement this. Here are only the decisions, most of the work is in functions.
        Database calls are only made when needed.
        """
        
        user: 'User' = request.user
        new_version = obj
        method: Union[Literal['GET'], Literal['POST'], Literal['DELETE'], Literal['PATCH']] = request.method
        """This is a little overboard, but allows, to better show the narrowing down of possibillites."""

        # Super users can do anything        
        if user.is_superuser:
            return True
        
        # Nobody else can delete
        if method == 'DELETE':
            return False
        # method: Literal['GET', 'POST', 'PATCH']
                        
        # Get custom permissions
        user_has_this_article_permissions_query_set: 'QuerySet' = UserArticlePermission.objects.filter(
            user = user,
            lemma_article = new_version.lemma_article
        ).all()
        
        # No permisions -> bye bye
        if user_has_this_article_permissions_query_set.__len__() == 0:
            return False
        
        # With GET any permission is ok (because the "least" is VIEW)
        if method == 'GET':
            return True
        #  method: Literal['POST', 'PATCH']
        
        # Have a set of Enums instead of query set of objects, for easier
        user_has_this_article_permissions: Set[EditTypes] = {permission.edit_type for permission in user_has_this_article_permissions_query_set}
                
        # Everything is allowed for write    
        if EditTypes.WRITE in user_has_this_article_permissions:
            return True
        
        if {EditTypes.VIEW} == user_has_this_article_permissions:
            # With only VIEW and method: Literal['POST', 'PATCH'], please leave
            return False
            
        # Remaining Edit Types are ANNOTATE AND COMMENT.
        # Remaining methods are: POST and PATCH. They are treated the same.
        last_version = get_last_version(new_version, update = request.method == 'PATCH')
        
        # It is not possible to write a first version, without "WRITE". Annotation and comments are not stand alone content. They need text.
        if last_version is None:
            return False
        
        # Check which node types, the user is not allowed to change.
        prohibited_node_types = (
            node_type
            for edit_type, node_type
            in node_edit_type_mapping.items()
            if edit_type not in user_has_this_article_permissions
        )
        
        return check_if_docs_diff_regarding_mark_types(prohibited_node_types, new_version, last_version)

    
class AbstractReadOnlyPermissionViewSetMixin(ABC):
    
    def get_permissions(self):
        if self.action in ('list', 'retrieve', ):
            return [permissions.IsAuthenticated(), ]
        else:
            return [permissions.IsAdminUser(), ]
    