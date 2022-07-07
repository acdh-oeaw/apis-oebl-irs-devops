

from datetime import datetime, timedelta
from typing import List, Optional, Type, Union
from oebl_editor.models import LemmaArticleVersion, LemmaArticle
from oebl_editor.tests.utilitites.markup import create_a_document
from oebl_irs_workflow.models import Author, Editor, IrsUser, IssueLemma
from django.contrib.auth.models import User

def createLemmaArticle(article_kwargs: Optional[dict] = None, issue_kwargs: Optional[dict] = None) -> LemmaArticle:
    
    article_kwargs = {} if article_kwargs is None else article_kwargs
    issue_kwargs = {} if issue_kwargs is None else issue_kwargs

    issue = IssueLemma.objects.create(**issue_kwargs)
    
    article = LemmaArticle.objects.create(
        issue_lemma = issue,
        **article_kwargs
    )
    
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


def create_user(
    UserModel: Union[Type['Editor'], Type['IrsUser'], Type['Author']],
        username: str,
        password: str,
    ) -> Union['Editor', 'IrsUser', 'Author']:
    user: 'User'
    if UserModel is IrsUser:
        user = IrsUser.objects.create_superuser(username=username)
    else:
        user = UserModel.objects.create(username=username)
    
    user.set_password(password)
    user.save()
    return user
