from typing import TYPE_CHECKING

from oebl_editor.permissions import AbstractReadOnlyPermissionViewSetMixin, AbstractUserPermissionViewSetMixin, LemmaArticleVersionPermissions
from rest_framework import viewsets
from rest_framework import permissions
from oebl_editor.serializers import LemmaArticleSerializer, LemmaArticleVersionSerializer, UserArticlePermissionSerializer, UserArticleAssignmentSerializer
from oebl_editor.models import LemmaArticle, LemmaArticleVersion, UserArticlePermission, UserArticleAssignment

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class LemmaArticleViewSet(viewsets.ModelViewSet, AbstractReadOnlyPermissionViewSetMixin):
    
    serializer_class = LemmaArticleSerializer
    
    def get_naive_query_set(self) -> 'QuerySet':
        return LemmaArticle.objects.get_queryset()
        
    
class LemmaArticleVersionViewSet(viewsets.ModelViewSet, AbstractUserPermissionViewSetMixin):
    
    serializer_class = LemmaArticleVersionSerializer
    permission_classes = [permissions.IsAuthenticated, LemmaArticleVersionPermissions]

    def get_naive_query_set(self) -> 'QuerySet':
        return LemmaArticleVersion.objects.get_queryset()
    
    
class UserArticlePermissionViewSet(viewsets.ModelViewSet, AbstractUserPermissionViewSetMixin):
    
    serializer_class = UserArticlePermissionSerializer
    
    def get_naive_query_set(self) -> 'QuerySet':
        return UserArticlePermission.objects.get_queryset()    
    
    
class UserArticleAssignmentViewSet(viewsets.ModelViewSet, AbstractUserPermissionViewSetMixin):
    
    serializer_class = UserArticleAssignmentSerializer
    
    def get_naive_query_set(self) -> 'QuerySet':
        return UserArticleAssignment.objects.get_queryset()
    

        