import typing
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models.deletion import SET_NULL
from oebl_irs_workflow.models import Lemma as ResearchPerson, Editor
from django.conf import settings
import os


CHOICES_GENDER = (
    ('männlich', "männlich"),
    ('weiblich', "weiblich"),
    ('divers', 'divers'),
)

CHOICES_DATE_MODIFIER = (
    ('ca.', 'ca.'),
    ('nach', 'nach'),
    ('vor', 'vor'),
    ('um', 'um')
)


def get_attachements_path(instance: 'ListEntry', filename: str) -> str:
    """returns the path for a given file

    Args:
        instance ([ListEntry]): ListEntry class that contains the file
        filename ([str]): filename

    Returns:
        str: Path to be used for storing the file
    """    
    fn = filename.split('.')
    path = settings.get('MEDIA_ROOT')
    enum = False
    if os.path.isfile(os.path.join(path, f"researchtool/attachements/research_lemma_{instance.id}/{filename}")):
        enum = 0
        while os.path.isfile(os.path.join(path, f"researchtool/attachements/research_lemma_{instance.id}/{fn[0]}_{enum}.{fn[1]}")):
            enum += 1
    return f"researchtool/attachements/research_lemma_{instance.id}/{fn[0]}{'_'+enum if enum else ''}.{fn[1]}"


class ProfessionGroup(models.Model):
    name = models.CharField(max_length=255)


class FullName(typing.TypedDict):
    """For defining the structure in the django json field. Just as a hint …"""
    first_name: typing.Optional[str]
    last_name: typing.Optional[str]


class IRSPerson(models.Model):
    irs_person = models.ForeignKey(
        ResearchPerson, on_delete=models.SET_NULL, blank=True, null=True
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    alternative_names: typing.List[FullName] = models.JSONField(default=list, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    date_of_birth_modifier = models.CharField(max_length=5, null=True, blank=True, choices=CHOICES_DATE_MODIFIER)
    date_of_death = models.DateField(blank=True, null=True)
    date_of_death_modifier = models.CharField(max_length=5, null=True, blank=True, choices=CHOICES_DATE_MODIFIER)
    profession_group = models.ForeignKey(ProfessionGroup, blank=True, null=True, on_delete=SET_NULL)
    profession_detail = models.CharField(max_length=255, null=True, blank=True)
    bio_note = models.TextField(blank=True, null=True)
    religion = models.CharField(max_length=255, blank=True, null=True)
    title_of_nobility = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True, choices=CHOICES_GENDER)
    uris = ArrayField(models.URLField(), null=True, blank=True)

    def __str__(self):
        return f"{self.name}, {self.first_name}"


class List(models.Model):
    title = models.CharField(max_length=255)
    editor = models.ForeignKey(Editor, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.title} ({str(self.editor)})"


class ListEntry(models.Model):
    person = models.ForeignKey(IRSPerson, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True)
    source_id = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    selected = models.BooleanField(default=False)
    list = models.ForeignKey(List, on_delete=models.SET_NULL, null=True, blank=True)
    columns_scrape = models.JSONField(null=True, blank=True)
    columns_user = models.JSONField(null=True, blank=True)
    scrape = models.JSONField(null=True, blank=True)
    deleted = models.BooleanField(default=False)
    attachements = ArrayField(models.FileField(get_attachements_path), null=True, blank=True)
    works = ArrayField(models.URLField(), null=True, blank=True)
    references = ArrayField(models.URLField(), null=True, blank=True)
    _update_scrape_triggered = False

    def __str__(self):
        return f"{str(self.person)} - scrape {str(self.last_updated)}"

    def get_dict(self):
        res = {}
        res["name"] = getattr(self.person, "name", None)
        res["first_name"] = getattr(self.person, "first_name", None)
        res["start_date"] = getattr(self.person, "date_of_birth", None)
        res["end_date"] = getattr(self.person, "date_of_death", None)
        return res
