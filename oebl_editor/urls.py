from django.urls import path
from django.conf.urls import include

app_name = "oebl_editor"
urlpatterns = [
    path(r"api/v1/", include("oebl_editor.api_urls_v1")),
]