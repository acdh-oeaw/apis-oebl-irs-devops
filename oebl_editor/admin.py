from django.contrib import admin

from .models import (
        LemmaArticle,
        LemmaArticleVersion,
        UserArticlePermission,
)

admin.site.register(LemmaArticle)
admin.site.register(LemmaArticleVersion)
admin.site.register(UserArticlePermission)
