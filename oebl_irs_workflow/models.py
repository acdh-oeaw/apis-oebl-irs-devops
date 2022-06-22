from apis_core.apis_entities.models import Person
from django.contrib.auth.models import User
from django.db import models
from django.db.models import DEFERRED
from django.forms.models import model_to_dict
from django.contrib import admin


CHOICES_STAGE = (
    ("ausgeschrieben", "ausgeschrieben"),
    ("autordurchsicht", "autordurchsicht"),
    ("eingelangt", "eingelangt"),
    ("endredaktion", "endredaktion"),
    ("gruppenredaktion", "gruppenredaktion"),
    ("verteilt", "verteilt"),
    ("zugesagt", "zugesagt"),
)

CHOICES_BIOUSER = (("aut", "AutorIn"), ("red", "RedakteurIn"), ("kor", "Korrektorat"))


class Contract(models.Model):
    contract = models.FilePathField()
    issued = models.DateField()
    lemma = models.ForeignKey("Lemma", on_delete=models.CASCADE)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)


class IrsUser(User):
    """Model to inherit from Django User model"""

    pass


class Editor(IrsUser):
    """Model for members of the editorial team"""

    pass


class Author(IrsUser):
    """Model for authors of biographies"""

    address = models.TextField(null=True, blank=True)


class Issue(models.Model):
    """Model holding Issues. Issues are a collection of Bios that will be published
    at a certain date. Pre digital-only, that was a volume.
    """

    name = models.CharField(max_length=255)
    pubDate = models.DateField(verbose_name="Publication Date", blank=True, null=True)
    statuses_allowed = models.ManyToManyField("LemmaStatus")


class LemmaNote(models.Model):
    """Model holding information on Notes that have been created by users on a Lemma."""

    created = models.DateTimeField(auto_now=True)
    text = models.TextField()
    user = models.ForeignKey("IrsUser", on_delete=models.CASCADE)
    lemma = models.ForeignKey("Lemma", on_delete=models.CASCADE)


class LemmaLabel(models.Model):
    """Model holding labels attached to Lemmas"""

    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255, default="white")


class LemmaStatus(models.Model):
    """Model holding the Status of the Lemma"""

    name = models.CharField(max_length=255)


class Lemma(Person):
    """Model holding the information on the Lemma. This class is inheritating the APIS
    Person class
    """

    info = models.TextField(null=True, blank=True)


class IssueLemma(models.Model):
    """Connects the lemma to all the other information. Rather than modifying the object
    a new one is created on all data changes. This allows for a complete revision history.
    """

    order = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now=True)
    issue = models.ForeignKey("Issue", on_delete=models.SET_NULL, null=True)
    status = models.ForeignKey(
        "LemmaStatus", on_delete=models.SET_NULL, null=True, blank=True
    )
    lemma = models.ForeignKey("Lemma", on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(
        "Author", on_delete=models.SET_NULL, null=True, blank=True
    )
    editor = models.ForeignKey(
        "Editor", on_delete=models.SET_NULL, null=True, blank=True
    )
    labels = models.ManyToManyField("LemmaLabel", blank=True)
    serialization = models.JSONField(null=True, blank=True)

    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        if not self._state.adding:
            created = self._loaded_values["created"]
            if self._loaded_values["issue_id"] is not None:
                issue = model_to_dict(
                    Issue.objects.get(pk=self._loaded_values["issue_id"])
                )
                if issue["pubDate"]:
                    issue["pubDate"] = issue["pubDate"].isoformat()
                if issue["statuses_allowed"]:
                    issue["statuses_allowed"] = [
                        x.pk for x in issue["statuses_allowed"]
                    ]
            else:
                issue = None
            if self._loaded_values["status_id"] is not None:
                status = model_to_dict(
                    LemmaStatus.objects.get(pk=self._loaded_values["status_id"])
                )
            else:
                status = None
            if self._loaded_values["lemma_id"] is not None:
                lemma = model_to_dict(
                    Lemma.objects.get(pk=self._loaded_values["lemma_id"]),
                    fields=[
                        "id",
                        "first_name",
                        "name",
                        "start_date_written",
                        "end_date_written",
                        "info",
                        "collection",
                    ],
                )
                if lemma["collection"]:
                    lemma["collection"] = [x.pk for x in lemma["collection"]]
            else:
                lemma = None
            if self._loaded_values["author_id"] is not None:
                author = model_to_dict(
                    Author.objects.get(pk=self._loaded_values["author_id"]),
                    fields=["id", "username", "first_name", "last_name", "email"],
                )
            else:
                author = None
            if self._loaded_values["editor_id"] is not None:
                editor = model_to_dict(
                    Editor.objects.get(pk=self._loaded_values["editor_id"]),
                    fields=["id", "username", "first_name", "last_name", "email"],
                )
            else:
                editor = None
            res = {
                "created": created.isoformat(),
                "issue": issue,
                "status": status,
                "lemma": lemma,
                "author": author,
                "editor": editor,
            }
            if self.serialization is not None:
                self.serialization.append(res)
            else:
                self.serialization = [
                    res,
                ]
            ret = super().save(*args, **kwargs)
        else:
            ret = super().save(*args, **kwargs)
        return ret


class LemmaArticle(models.Model):
    """Represents an article in an issue about a lemma (person).
    """
    issue_lemma = models.OneToOneField(
        IssueLemma, 
        on_delete=models.CASCADE,  # When the issue lemma is deleted, the article has no meaning.
        primary_key=True,  # The issue lemma is the primary way of identifying LemmaArticle
        null=False,  # Just to be clear :-)
    )
    
    published = models.BooleanField(null=False, default=False)
    current_version = models.OneToOneField(
        'LemmaArticleVersion',
        on_delete=models.CASCADE,
        null=False,  # An article can not be empty. The current version contains the data
    )
    
    
class LemmaArticleVersion(models.Model):
    """Represents a version of an artical at a time"""
    lemma_article = models.ForeignKey(
        IssueLemma,
        on_delete=models.CASCADE,  # When the issue lemma is deleted, the article has no meaning.
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
        on_delete=models.CASCADE,  # When the issue lemma is deleted, the permission has no meaning.
        unique=False,   # One article can have multiple user permissions.
        null=False,
    )
    
    user = models.ForeignKey(
        IrsUser,
        on_delete=models.CASCADE,  # When the useris deleted, the permission has no meaning.
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

    
    