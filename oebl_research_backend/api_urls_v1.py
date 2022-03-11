from django.urls import path
from rest_framework import routers

from .api_views import LemmaResearchView, ListViewset
from .autocompletes import ProfessionGroupAutocomplete

app_name = "oebl_research_backend"


router = routers.DefaultRouter()
router.register(r"listresearch", ListViewset)
router.register(r"lemmaresearch", LemmaResearchView)

urlpatterns = router.urls

urlpatterns += [
    path('autocompletes/professiongroup/',
    ProfessionGroupAutocomplete.as_view(),
    name='profession-group-autocomplete'
    )
]
