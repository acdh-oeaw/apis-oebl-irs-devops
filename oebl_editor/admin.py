from django.contrib import admin

from .models import (
        LemmaArticle,
        LemmaArticleVersion,
        UserArticleAssignment,
)

admin.site.register(LemmaArticle)
admin.site.register(LemmaArticleVersion)
admin.site.register(UserArticleAssignment)
