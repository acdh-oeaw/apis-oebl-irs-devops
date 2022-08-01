from django.contrib import admin

from .models import (
        LemmaArticle,
        LemmaArticleVersion,
)

admin.site.register(LemmaArticle)
admin.site.register(LemmaArticleVersion)
