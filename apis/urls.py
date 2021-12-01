from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from apis_core.apis_entities.api_views import GetEntityGeneric
from oebl_irs_workflow.api_views import UserProfileViewset


if "theme" in settings.INSTALLED_APPS:
    urlpatterns = [
        url(r"^apis/", include("apis_core.urls", namespace="apis")),
        #url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        path(
            r"entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
        ),
        url(r"^", include("theme.urls", namespace="theme")),
        url(r"^admin/", admin.site.urls),
        url(r"^info/", include("infos.urls", namespace="info")),
        url(r"^webpage/", include("webpage.urls", namespace="webpage")),
    ]
if "paas_theme" in settings.INSTALLED_APPS:
    urlpatterns = [
        url(r"^apis/", include("apis_core.urls", namespace="apis")),
        #url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        path(
            r"entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
        ),
        url(r"^", include("paas_theme.urls", namespace="theme")),
        url(r"^admin/", admin.site.urls),
        url(r"^info/", include("infos.urls", namespace="info")),
        url(r"^webpage/", include("webpage.urls", namespace="webpage")),
    ]
else:
    urlpatterns = [
        path("me/", UserProfileViewset.as_view({"get": "list"})),
        url(r"^apis/", include("apis_core.urls", namespace="apis")),
        #url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        path(
            r"entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
        ),
        url(r"^admin/", admin.site.urls),
        url(r"^info/", include("infos.urls", namespace="info")),
        url(r"^", include("webpage.urls", namespace="webpage")),
    ]

if "transkribus" in settings.INSTALLED_APPS:
    urlpatterns = urlpatterns + [
        url(r"^transkribus/", include("transkribus.urls")),
    ]

if "apis_bibsonomy" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(r"^bibsonomy/", include("apis_bibsonomy.urls", namespace="bibsonomy"))
    )

if "oebl_irs_workflow" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(
            r"^workflow/",
            include("oebl_irs_workflow.urls", namespace="oebl_irs_workflow"),
        )
    )


if "oebl_research_backend" in settings.INSTALLED_APPS:
    urlpatterns.append(
        url(
            r"^research/",
            include("oebl_research_backend.urls", namespace="oebl_research_backend"),
        )
    )

urlpatterns = urlpatterns + [
    url(r'^auth/', include('djoser.urls')),
    url(r'^auth/', include('djoser.urls.authtoken')),
]

handler404 = "webpage.views.handler404"
