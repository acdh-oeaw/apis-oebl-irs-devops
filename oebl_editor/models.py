from typing import Dict, TYPE_CHECKING
from django.db import models

from oebl_irs_workflow.models import IrsUser, IssueLemma

if TYPE_CHECKING:
    from oebl_editor.markup import EditorDocument, MarkTagName


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
        null=True,  # An article can not be empty at creation time
    )


class LemmaArticleVersion(models.Model):
    """Represents a version of an artical at a time"""
    lemma_article = models.ForeignKey(
        LemmaArticle,
        # When the issue lemma is deleted, the article has no meaning.
        on_delete=models.CASCADE,
        unique=False,   # One article can have multiple versions.
        null=False,     # A version of an article must have an article.
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    markup: 'EditorDocument' = models.JSONField(null=False)
    """This markup will be using the frontend's editor markup to json translation from https://tiptap.dev/api/editor#get-json ,
    using a lot of additional plugins that generate different annotations like comments and linked data.
    """


class EditTypes(models.TextChoices):
    """Custom edit type system for LemmaArticles"""
    VIEW = ('VIEW', 'VIEW')
    COMMENT = ('COMMENT', 'COMMENT')
    ANNOTATE = ('ANNOTATE', 'ANNOTATE')
    WRITE = ('WRITE', 'WRITE')
    """With `WRITE` including all other types"""
    
    
node_edit_type_mapping: Dict[
            EditTypes,
            'MarkTagName',
        ] = {
        EditTypes.COMMENT: 'comment',
        EditTypes.ANNOTATE: 'annotation'
}
"""This maps the edit types in the database to node types in the markdown"""     


class AbstractUserArticleEditTypeMapping(models.Model):
    """Map permissions to users and articles."""
    class Meta:
        abstract = True
        
    lemma_article = models.ForeignKey(
        LemmaArticle,
        # When the issue lemma is deleted, the assignment has no meaning.
        on_delete=models.CASCADE,
        unique=False,   # One article can have multiple user assignments.
        null=False,
    )

    user = models.ForeignKey(
        IrsUser,
        # When the useris deleted, the assignment has no meaning.
        on_delete=models.CASCADE,
        unique=False,   # One user can have multiple article assignments.
        null=False,
    )

    edit_type = models.CharField(
        choices=EditTypes.choices,
        null=False,
        max_length=max((choice_tuple[1].__len__() for choice_tuple in EditTypes.choices))
    )


class UserArticleAssignment(AbstractUserArticleEditTypeMapping):
    """Manage article assignments for users."""
    pass

