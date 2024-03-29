from oebl_editor.permissions import AbstractReadOnlyPermissionViewSetMixin, LemmaArticleVersionPermissions
from oebl_editor.queries import create_get_query_set_method_filtered_by_user
from rest_framework import viewsets
from rest_framework import permissions
from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.openapi import OpenApiParameter
from oebl_editor.serializers import LemmaArticleSerializer, LemmaArticleVersionSerializer
from oebl_editor.models import LemmaArticle, LemmaArticleVersion


class LemmaArticleViewSet(AbstractReadOnlyPermissionViewSetMixin, viewsets.ModelViewSet):
    
    serializer_class = LemmaArticleSerializer
    
    get_queryset = create_get_query_set_method_filtered_by_user(LemmaArticle, 'pk')
        
    
@extend_schema_view(
    list = extend_schema(
        parameters=[
            OpenApiParameter('lemma_article', type=int),
        ],
    ),
)
class LemmaArticleVersionViewSet(viewsets.ModelViewSet):
    
    serializer_class = LemmaArticleVersionSerializer
    permission_classes = [permissions.IsAuthenticated, LemmaArticleVersionPermissions]

    get_queryset = create_get_query_set_method_filtered_by_user(LemmaArticleVersion)

    filterset_fields = ['lemma_article', ]
