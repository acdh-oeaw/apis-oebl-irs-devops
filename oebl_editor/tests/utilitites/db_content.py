

from datetime import datetime, timedelta
from typing import List
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

    def __init__(self) -> None:    
        self.timedelta_between_dates = timedelta(minutes=30)
        self.first_date = datetime(2000, 12, 12, 12, 12, 12)
        self.dates: List[datetime] = []
        self.versions: List[LemmaArticleVersion]

    def add_versions_to_article(self, article: LemmaArticle, n: int):
        self.dates = []
        self.versions = []
        date = self.first_date
        for _ in range(n):
            version = LemmaArticleVersion(
                lemma_article = article,
                date_created = date,
                date_modified = date,
                markup = create_a_document(),
            )
            version.save()
            date += self.timedelta_between_dates
            self.versions.append(version)
            self.dates.append(date)    
    