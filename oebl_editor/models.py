from django.db import models

from oebl_irs_workflow.models import IrsUser, IssueLemma


class LemmaArticle(models.Model):
    """Represents an article in an issue about a lemma (person).
    """

    issue_lemma = models.OneToOneField(
        IssueLemma,
        # When the issue lemma is deleted, the article has no meaning.
        on_delete=models.CASCADE,
        primary_key=True,  # The issue lemma is the primary way of identifying LemmaArticle
        null=False,  # Just to be clear :-)
    )

    published = models.BooleanField(null=False, default=False)
    current_version = models.OneToOneField(
        'LemmaArticleVersion',
        on_delete=models.CASCADE,
        null=True,  # An article can not be empty at cre<tion time
    )


class LemmaArticleVersion(models.Model):
    """Represents a version of an artical at a time"""
    lemma_article = models.ForeignKey(
        IssueLemma,
        # When the issue lemma is deleted, the article has no meaning.
        on_delete=models.CASCADE,
        unique=False,   # One article can have multiple versions.
        null=False,     # A version of an article must have an article.
    )

    date_created = models.DateTimeField(auto_created=True)
    date_modified = models.DateTimeField(auto_created=True, auto_now=True)

    markup = models.JSONField(null=False)
    """This markup will be using the frontends editor markup to json translation from https://tiptap.dev/api/editor#get-json ,
    using a lot of additional plugins that generate different annotations like comments and linked data.
    """


class Permission(models.TextChoices):

    """Custom permision system for LemmaArticles"""
    VIEW = ('VIEW', 'VIEW')
    COMMENT = ('COMMENT', 'COMMENT')
    ANNOTATE = ('ANNOTATE', 'ANNOTATE')
    WRITE = ('WRITE', 'WRITE')
    """With `WRITE` including all other permission"""


class AbstractUserArticlePermissionMapping(models.Model):

    """Map permissions to users and articles."""
    class Meta:
        abstract = True
        
    lemma_article = models.ForeignKey(
        IssueLemma,
        # When the issue lemma is deleted, the permission has no meaning.
        on_delete=models.CASCADE,
        unique=False,   # One article can have multiple user permissions.
        null=False,
    )

    user = models.ForeignKey(
        IrsUser,
        # When the useris deleted, the permission has no meaning.
        on_delete=models.CASCADE,
        unique=False,   # One user can have multiple article permissions.
        null=False,
    )

    permission = models.CharField(
        choices=Permission.choices,
        null=False,
        max_length=max((choice_tuple[1].__len__() for choice_tuple in Permission.choices))
    )


class UserArticlePermission(AbstractUserArticlePermissionMapping):
    """Manage custom article permission for users."""
    pass


class UserArticleAssignment(AbstractUserArticlePermissionMapping):
    """Manage user assignments for users"""
    pass
