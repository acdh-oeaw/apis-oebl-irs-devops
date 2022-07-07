from oebl_editor.permissions import AbstractReadOnlyPermissionViewSetMixin, LemmaArticleVersionPermissions
from oebl_editor.queries import create_get_query_set_method_filtered_by_user
from rest_framework import viewsets
from rest_framework import permissions
from oebl_editor.serializers import LemmaArticleSerializer, LemmaArticleVersionSerializer, UserArticlePermissionSerializer
from oebl_editor.models import LemmaArticle, LemmaArticleVersion, UserArticlePermission


class LemmaArticleViewSet(AbstractReadOnlyPermissionViewSetMixin, viewsets.ModelViewSet):
    
    serializer_class = LemmaArticleSerializer
    
    get_queryset = create_get_query_set_method_filtered_by_user(LemmaArticle, 'pk')
        
    
class LemmaArticleVersionViewSet(viewsets.ModelViewSet):
    
    serializer_class = LemmaArticleVersionSerializer
    permission_classes = [permissions.IsAuthenticated, LemmaArticleVersionPermissions]

    get_queryset = create_get_query_set_method_filtered_by_user(LemmaArticleVersion)

    
    
class UserArticlePermissionViewSet(AbstractReadOnlyPermissionViewSetMixin, viewsets.ModelViewSet):
    
    serializer_class = UserArticlePermissionSerializer
    
    get_queryset = create_get_query_set_method_filtered_by_user(UserArticlePermission)
   