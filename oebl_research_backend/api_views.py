from typing_extensions import Required
from numpy import require
from rest_framework.generics import ListCreateAPIView
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import serializers
from .tasks import scrape
from rest_framework.response import Response
from drf_spectacular.utils import inline_serializer, extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from django_filters import rest_framework as filters

from .models import ListEntry, List, Editor, CHOICES_GENDER
from .serializers import ListEntrySerializer, ListSerializer, create_alternative_names_field


class LemmaResearchFilter(filters.FilterSet):
    modified_after = filters.DateTimeFilter(field_name="last_updated", lookup_expr="gt")

    class Meta:
        model = ListEntry
        fields = ["modified_after", "deleted"]


@extend_schema(
    description="""Endpoint that allows to POST a list of lemmas to the research pipeline for processing.
        All additional fields not mentioned in the Schema are stored and retrieved as user specific fields.
        """,
    methods=["PATCH"],
    request=inline_serializer(
        name="LemmaResearchPatchAPIView",
        fields={
            "list": inline_serializer(
                name="LemmaresearchEditorSerializer",
                many=False,
                fields={
                    "id": serializers.PrimaryKeyRelatedField(
                        queryset=List.objects.all(), read_only=False, required=False
                    ),
                    "editor": serializers.PrimaryKeyRelatedField(
                        queryset=Editor.objects.all(), read_only=False, required=False
                    ),
                    "title": serializers.CharField(required=False),
                },
            ),
            "selected": serializers.BooleanField(default=False, required=False),
            "gnd": serializers.ListField(child=serializers.URLField(), required=False),
            "firstName": serializers.CharField(required=False),
            "lastName": serializers.CharField(required=False),
            "alternativeNames": create_alternative_names_field(),
            "dateOfBirth": serializers.DateField(required=False),
            "dateOfDeath": serializers.DateField(required=False),
            "gender": serializers.ChoiceField(CHOICES_GENDER, required=False)
        },
    ),
    responses={
        201: inline_serializer(
            many=False,
            name="ListPatchAPIViewResponse",
            fields={
                "success": serializers.UUIDField(),
                "instance": inline_serializer(
                    many=False,
                    name="ListPatchAPIViewResponseInstance",
                    fields={
                        "list": inline_serializer(
                            name="LemmaresearchEditorSerializer",
                            many=False,
                            fields={
                                "id": serializers.PrimaryKeyRelatedField(
                                    queryset=List.objects.all(),
                                    read_only=False,
                                    required=False,
                                ),
                                "editor": serializers.PrimaryKeyRelatedField(
                                    queryset=Editor.objects.all(),
                                    read_only=False,
                                    required=False,
                                ),
                                "title": serializers.CharField(required=False),
                            },
                        ),
                        "selected": serializers.BooleanField(default=False),
                        "gnd": serializers.ListField(
                            child=serializers.URLField(), required=False
                        ),
                        "firstName": serializers.CharField(required=False),
                        "lastName": serializers.CharField(required=False),
                        "alternativeNames": create_alternative_names_field(),
                        "dateOfBirth": serializers.DateField(required=False),
                        "dateOfDeath": serializers.DateField(required=False),
                        "gender": serializers.ChoiceField(CHOICES_GENDER, required=False),
                        "columns_user": OpenApiTypes.OBJECT,
                        "columns_scrape": OpenApiTypes.OBJECT,
                    },
                ),
            },
        ),
    },
)
@extend_schema(
    description="""Endpoint that allows to POST a list of lemmas to the research pipeline for processing.
        All additional fields not mentioned in the Schema are stored and retrieved as user specific fields.
        """,
    methods=["POST"],
    request=inline_serializer(
        name="ListCreateAPIView",
        fields={
            "listId": serializers.PrimaryKeyRelatedField(
                queryset=List.objects.all(), read_only=False, required=True
            ),
            "lemmas": inline_serializer(
                name="LemmasCreateSerializer",
                fields={
                    "gnd": serializers.ListField(
                        child=serializers.URLField(), required=False
                    ),
                    "selected": serializers.BooleanField(default=False),
                    "firstName": serializers.CharField(required=False),
                    "lastName": serializers.CharField(required=False),
                    "alternativeNames": create_alternative_names_field(),
                    "dateOfBirth": serializers.DateField(required=False),
                    "dateOfDeath": serializers.DateField(required=False),
                    "gender": serializers.ChoiceField(CHOICES_GENDER, required=False)
                },
                many=True,
            ),
        },
    ),
    responses={
        201: inline_serializer(
            many=False,
            name="ListCreateAPIViewResponse",
            fields={"success": serializers.UUIDField()},
        ),
    },
)
class LemmaResearchView(viewsets.ModelViewSet):
    """APIView to process scraping requests

    Args:
        GenericAPIView ([type]): [description]
    """

    queryset = ListEntry.objects.all()
    serializer_class = ListEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = LemmaResearchFilter
    http_method_names = ["get", "post", "head", "options", "delete", "update", "patch"]

    def create(self, request):
        job_id = scrape.delay(request.data, request.user.pk, request.data["listId"])
        return Response({"success": job_id.id})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        if instance._update_scrape_triggered:
            job_id = scrape.delay(
                {
                    "lemmas": [
                        serializer.data,
                    ]
                },
                request.user.pk,
                serializer.data["list"]["id"],
                update=instance.pk,
                gnd_job=serializer.data["gnd"],
            )
            return Response({"success": job_id.id, "instance": serializer.data})
        else:
            return Response({"success": None, "instance": serializer.data})

    def destroy(self, request, *arg, **kwargs):
        ent = ListEntry.objects.filter(pk=kwargs["pk"])
        if ent.count() == 0:
            return Response(status.HTTP_404_NOT_FOUND)
        else:
            for e in ent:
                e.deleted = True
                e.save()
            return Response(status.HTTP_204_NO_CONTENT)


"""     def get(self, request, crawlerid):
        scrape_id = db.scrape.find_one({"celery_id": crawlerid})
        wikidata = db.scrapes_wikidata.find({"scrape_id": str(scrape_id["_id"])})
        wikipedia = db.scrapes_wikipedia.find({"scrape_id": str(scrape_id["_id"])})
        res = dict()
        for ent in wikidata:
            person = db.person.find_one({"_id": ent["person_id"]})
            res[str(ent["person_id"])] = {
                "gnd": person.get("gnd"),
                "query_name": person.get("name"),
                "viaf": ent.get("viaf", None),
                "loc": ent.get("loc", None),
                "wien wiki": ent.get("wienWiki", None),
                "label": ent.get("pLabel", None),
                "geburtstag": ent.get("date_of_birth", None),
                "todestag": ent.get("date_of_death", None),
            }
            wikipedia = db.scrapes_wikipedia.find_one(
                {"scrape_id": str(scrape_id["_id"]), "person_id": ent["person_id"]}
            )
            if wikipedia:
                res[str(ent["person_id"])]["wikipedia_edits"] = wikipedia["edits_count"]
                res[str(ent["person_id"])]["wikipedia_distinct_editors"] = wikipedia[
                    "number_of_editors"
                ]
                res[str(ent["person_id"])]["wikipedia_txt"] = wikipedia["txt"].strip()

        obv = db.scrapes_obv.find({"scrape_id": str(scrape_id["_id"])})
        for ent in obv:
            if str(ent["person_id"]) not in res.keys():
                res[str(ent["person_id"])] = dict()
            if "obv_entries" not in res[str(ent["person_id"])]:
                res[str(ent["person_id"])]["obv_entries"] = []
            res[str(ent["person_id"])]["obv_entries"].append(str(ent["_id"]))
        for pers in res.keys():
            if res[pers].get("obv_entries"):
                res[pers]["obv_count"] = len(res[pers]["obv_entries"])
        resfin = [res[key] for key in res.keys()]

        return Response({"count": len(resfin), "results": resfin}) """


@extend_schema(
    description="""Endpoint that allows to create a Research Lemma List
        """,
    methods=["POST"],
    request=inline_serializer(
        name="CreateResearchListAPIView",
        fields={
            "title": serializers.CharField(required=True),
        },
    ),
)
class ListViewset(viewsets.ModelViewSet):

    queryset = List.objects.all()
    serializer_class = ListSerializer
    filter_fields = ["title", "editor"]
    permission_classes = [IsAuthenticated]
