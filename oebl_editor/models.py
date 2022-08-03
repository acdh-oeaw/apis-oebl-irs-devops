from typing import Dict, TYPE_CHECKING
from django.db import models

from oebl_irs_workflow.models import EditTypes, IssueLemma

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
    
    
node_edit_type_mapping: Dict[
            EditTypes,
            'MarkTagName',
        ] = {
        EditTypes.COMMENT: 'comment',
        EditTypes.ANNOTATE: 'annotation'
}
"""This maps the edit types in the database to node types in the markdown"""     




