from rest_framework import routers
from .views import LemmaArticleViewSet, LemmaArticleVersionViewSet, UserArticleAssignmentViewSet

router = routers.DefaultRouter()
app_name = 'oebl_editor'

router.register(r'lemma-article', LemmaArticleViewSet, 'lemma-article')
router.register(r'lemma-article-version', LemmaArticleVersionViewSet, 'lemma-article-version')
router.register(r'user-article-assignment', UserArticleAssignmentViewSet, 'user-article-assignment')

urlpatterns = router.urls
