from datetime import datetime, timedelta
from typing import Callable, List, Optional, Union

from oebl_editor.models import LemmaArticleVersion, LemmaArticle
from oebl_irs_workflow.models import Author, AuthorIssueLemmaAssignment, EditTypes, Editor, IssueLemma


def create_article(article_kwargs: Optional[dict] = None, issue_kwargs: Optional[dict] = None) -> LemmaArticle:

    article_kwargs = {} if article_kwargs is None else article_kwargs
    issue_kwargs = {} if issue_kwargs is None else issue_kwargs

    issue = IssueLemma.objects.create(**issue_kwargs)

    article = LemmaArticle.objects.create(
        issue_lemma=issue,
        **article_kwargs
    )

    return article


class VersionGenerator:

    def __init__(self) -> None:
        self.timedelta_between_dates = timedelta(minutes=30)
        self.first_date = datetime(2000, 12, 12, 12, 12, 12)
        self.dates: List[datetime] = []
        self.versions: List[LemmaArticleVersion]

    def add_versions_to_article(self, article: LemmaArticle, n: int, markup_generator: Callable[[], dict] = dict) -> 'VersionGenerator':
        self.dates = []
        self.versions = []
        date = self.first_date
        for _ in range(n):
            version = LemmaArticleVersion(
                lemma_article=article,
                date_created=date,
                date_modified=date,
                markup=markup_generator(),
            )
            version.save()
            date += self.timedelta_between_dates
            self.versions.append(version)
            self.dates.append(date)
        return self


def create_and_assign_article(user: Union['Editor', 'Author'], edit_type: EditTypes = EditTypes.WRITE):
    if user.__class__ is Editor:
        return create_article(issue_kwargs={'editor': user.editor})
    elif user.__class__ is Author:
        article = create_article()
        AuthorIssueLemmaAssignment.objects.create(
            issue_lemma=article.issue_lemma,
            author=user,
            edit_type=edit_type,
        )
        return article
    else:
        raise RuntimeError
