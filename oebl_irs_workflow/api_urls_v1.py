from rest_framework import routers
from django.urls import path

from .api_views import (
    AuthorViewset,
    EditorViewset,
    IssueViewset,
    IssueLemmaViewset,
    LemmaStatusViewset,
    LemmaNoteViewset,
    LemmaViewset,
    LemmaLabelViewset,
    ResearchLemma2WorkflowLemma,
)

app_name = "oebl_irs_workflow"

router = routers.DefaultRouter()
router.register(r"authors", AuthorViewset)
router.register(r"editors", EditorViewset)
router.register(r"issue-lemma", IssueLemmaViewset)
router.register(r"issues", IssueViewset)
router.register(r"lemma", LemmaViewset)
router.register(r"lemma-status", LemmaStatusViewset)
router.register(r"lemma-note", LemmaNoteViewset)
router.register(r"lemma-label", LemmaLabelViewset)

urlpatterns = router.urls

urlpatterns += [path(r"research2workflow/", ResearchLemma2WorkflowLemma.as_view())]
