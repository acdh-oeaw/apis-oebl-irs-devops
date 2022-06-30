

from datetime import datetime, timedelta
from typing import Generator
from oebl_editor.models import LemmaArticleVersion, LemmaArticle
from oebl_editor.tests.utilitites.markup import create_a_document
from oebl_irs_workflow.models import IssueLemma


def createLemmaArticle() -> LemmaArticle:
    
    issue = IssueLemma()
    issue.save()
    
    article = LemmaArticle(
        issue_lemma = issue,
    )
    
    article.save()
    return article


class VersionGenerator:

    date_created_1 = datetime(2000, 12, 12, 12, 12, 12)
    date_created_2 = date_created_1 + timedelta(minutes=30)

    @classmethod
    def add_two_versions_to_article(cls, article: LemmaArticle) -> Generator[LemmaArticleVersion, None, None]:
        for date in (cls.date_created_1, cls.date_created_2):
            version = LemmaArticleVersion(
                lemma_article = article,
                date_created = date,
                date_modified = date,
                markup = create_a_document(),
            )
            
            version.save()
            yield version
    
    