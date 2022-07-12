from itertools import zip_longest
from typing import Callable, Generator, Optional, Set, TYPE_CHECKING, Union, Type
from aiohttp import request
from oebl_irs_workflow.models import AuthorIssueLemmaAssignment, IrsUser, IssueLemma
from rest_framework.exceptions import NotFound
from oebl_editor.models import LemmaArticleVersion

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from oebl_editor.markup import AbstractBaseNode, AbstractMarkNode,  EditorDocument, MarkTagName
    from oebl_editor.models import LemmaArticle
    from oebl_editor.views import LemmaArticleViewSet, LemmaArticleVersionViewSet
    from django.contrib.auth.models import User


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
        ).order_by('date_modified')

        # If we do have a date_modified (like with PATCH requests), we should check for the version right before the one, we are querying for.
        if lemma_article_version.date_modified is not None:
            query = query.filter(
                date_modified__lt = lemma_article_version.date_modified,
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
    mark: 'AbstractMarkNode'
    for mark in node.get('marks', []):
        if mark['type'] == tag_name:
            yield mark
    child_node: 'AbstractBaseNode'
    for child_node in  node.get('content', []):
        yield from extract_marks_flat(child_node, tag_name)


def extract_texts_flat(node: 'AbstractBaseNode') -> Generator[str, None, None]:
    """Run recursivly through None and get all text"""
    if node.get('type') == 'text':
        yield node['text']
    for child_node in  node.get('content', []):
        yield from extract_texts_flat(child_node)


def check_if_docs_diff_regaring_text(
            doc1: 'EditorDocument',
            doc2: 'EditorDocument',
    ) -> bool:
    """
    Check if two documents diff regarding text type.

    Doesn't show diffs.

    Very naive!
    """
    for text1, text2 in zip_longest(
            extract_texts_flat(doc1),
            extract_texts_flat(doc2),
            fillvalue=None,
        ):
        if text1 != text2:
            return True

    return False


def check_if_docs_diff_regarding_mark_types(
        mark_types: Set['MarkTagName'],
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
          fillvalue=None,
        ):
            # Something has terribly gone wrong.
            if (old_mark is None) and (new_mark is None):
                raise Exception
            # If mark has changed, it differs
            if old_mark != new_mark:
                return True
            
    return False

        
def create_get_query_set_method_filtered_by_user(
        model: Union[ Type['LemmaArticle'], Type['LemmaArticleVersion'], ],
        lemma_article_key: str = 'lemma_article',
    ) -> Callable[[Union['LemmaArticle', 'LemmaArticleVersion', ], ], 'QuerySet']:
    """Utility method to create get query sets method dynamically, since they are almost the same for all four models"""
    
    def get_queryset(self: Union['LemmaArticleViewSet', 'LemmaArticleVersionViewSet',  ]) -> 'QuerySet':
        user: 'User' = self.request.user

        queryset = model.objects.get_queryset()

        if user.is_superuser:
            return queryset

        if not hasattr(user, 'irsuser'):
            return queryset.none()
        
        irsuser: 'IrsUser' = user.irsuser

        if not (hasattr(irsuser, 'editor') or hasattr(irsuser, 'author')):
            return queryset.none()

        primary_key_subquery: 'QuerySet'

        if hasattr(irsuser, 'author'):
            primary_key_subquery = AuthorIssueLemmaAssignment.objects.filter(author = irsuser.author).values(r'issue_lemma')
        elif hasattr(irsuser, 'editor'):
            primary_key_subquery = IssueLemma.objects.filter(editor=irsuser.editor).values(r'pk')
        else:
            raise RuntimeError(rf'Programming error: User should be super user, editor or author. Logic failed to determine the right user for user {user}')

        filtered_query = queryset.filter(**{
                rf'{lemma_article_key}__in': primary_key_subquery,
        })

        return filtered_query

        
    return get_queryset
    