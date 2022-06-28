from django.contrib import admin

from .models import (
        LemmaArticle,
        LemmaArticleVersion,
        UserArticlePermission,
        UserArticleAssignment,
)

admin.site.register(LemmaArticle)
admin.site.register(LemmaArticleVersion)
admin.site.register(UserArticlePermission)
admin.site.register(UserArticleAssignment)
