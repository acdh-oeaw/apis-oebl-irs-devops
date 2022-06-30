from itertools import zip_longest
from typing import Generator, Optional, Set, TYPE_CHECKING
from rest_framework.exceptions import NotFound
from oebl_editor.models import LemmaArticleVersion, UserArticlePermission

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.contrib.auth.models import User
    from oebl_editor.markup import AbstractBaseNode, AbstractMarkNode,  EditorDocument, MarkTagName
    from oebl_editor.models import EditTypes
    


def get_last_version(lemma_article_version: LemmaArticleVersion, update: bool) -> Optional[LemmaArticleVersion]:
    """
    Get the last version of an article lemma version.
    
    For updates this is the version with the same id in the database, for creates, it is the newest one
    """
    query: 'QuerySet' = LemmaArticleVersion.objects.get_queryset()
    
    if update:
        query = query.filter(pk=lemma_article_version.pk)
    else:
        query = query.filter(
        lemma_article = lemma_article_version.lemma_article
        ).order_by(
            field_names=['date_modified'],
        )
        
    last_version = query.first()
    
    if (last_version is None) and update:
        raise NotFound(detail=rf'Did not find ${lemma_article_version}')
    
    return last_version

  
def extract_marks_flat(node: 'AbstractBaseNode', tag_name: 'MarkTagName') -> Generator['AbstractMarkNode', None, None]:
    """Extract all marks from document recursive

    Args:
        node (AbstractBaseNode): A node of the document. This would be usually the document. Lower calls are recursivly by this function.

    Yields:
        Generator[AbstractMarkNode, None, None]: Yields marks
    """
    for mark in node.get('marks', []):
        if mark.type == tag_name:
            yield mark
    for child_node in  node.get('content', []):
        yield from extract_marks_flat(child_node, tag_name)


def check_if_docs_diff_regarding_mark_types(
        mark_types: Set['EditTypes'],
        doc1: 'EditorDocument',
        doc2: 'EditorDocument',
    ) -> bool:
    """
    Check if two docs differe regarding provides mark types.
    
    Doesn't show diffs!
    """
    
    # We check each mark type 
    for mark_type in mark_types:
        for old_mark, new_mark in zip_longest(
          extract_marks_flat(doc2, mark_type),
          extract_marks_flat(doc1, mark_type),
          None,
        ):
            # Something has terribly gone wrong.
            if (old_mark is None) and (new_mark is None):
                raise Exception
            # If mark has changed, it differs
            if old_mark != new_mark:
                return False
            
    return True


def filter_queryset_by_user_permissions(user: 'User', query_set: 'QuerySet') -> 'QuerySet':
    if user.is_superuser:
        return query_set
    return query_set.filter(
            lemma_article__in = UserArticlePermission.objects.filter(user = user, )
        )
    