from django.contrib.auth.models import User
from typing import Dict, Tuple, List
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.utils import inline_serializer
from rest_framework import serializers
from rest_framework.response import Response

from .models import (
    Author,
    Editor,
    Issue,
    IssueLemma,
    LemmaStatus,
    Lemma,
    LemmaNote,
    LemmaLabel,
)
from oebl_research_backend.models import ListEntry as researchlemmas

Array = List[int]


class UserDetailSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="pk")
    role = serializers.SerializerMethodField(method_name="get_role")

    def get_role(self, object):
        if object.is_superuser:
            return "admin"
        elif "ChefredakteurIn" in [x.name for x in object.groups.all()]:
            return "ChefredakteurIn"
        else:
            return object.__class__.__name__

    class Meta:
        model = User
        exclude = ["password", "id"]


class UserSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="pk")
    name = serializers.SerializerMethodField(method_name="get_name")

    def get_name(self, object):
        if object.last_name is not None:
            return f"{object.last_name}, {object.first_name}"
        else:
            return object.username

    class Meta:
        model = User
        fields = ["userId", "email", "name"]


class AuthorSerializer(UserSerializer):
    class Meta:
        model = Author
        fields = ["userId", "email", "name", "address"]


class EditorSerializer(UserSerializer):
    class Meta:
        model = Editor
        fields = ["userId", "email", "name"]


class LemmaSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="name")
    dateOfBirth = serializers.SerializerMethodField("get_date_of_birth")
    dateOfDeath = serializers.SerializerMethodField("get_date_of_death")

    @extend_schema_field(OpenApiTypes.STR)
    def get_date_of_birth(self, obj):
        if obj.start_date is not None:
            return obj.start_date.isoformat()
        else:
            return obj.start_date_written

    @extend_schema_field(OpenApiTypes.STR)
    def get_date_of_death(self, obj):
        if obj.end_date is not None:
            return obj.end_date.isoformat()
        else:
            return obj.end_date_written

    class Meta:
        model = Lemma
        fields = ["id", "firstName", "lastName", "dateOfBirth", "dateOfDeath", "info"]


class LemmaStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LemmaStatus
        fields = "__all__"


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = "__all__"


class LemmaNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LemmaNote
        fields = "__all__"


class LemmaLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LemmaLabel
        fields = "__all__"


class IssueLemmaSerializerOpenApi(serializers.ModelSerializer):
    issue = IssueSerializer()
    lemma = LemmaSerializer()
    editor = EditorSerializer()
    status = LemmaStatusSerializer()

    class Meta:
        model = IssueLemma
        exclude = ["serialization"]


class IssueLemmaSerializer(serializers.ModelSerializer):
    """
    TODO: This class really needs some refactorization. 
        - It is unclear, what the "serialization" field is for,
        - why extened schema field?
        - update and create are very simular, spaghetti, and not very pythonic.
    I do not do it now, because, we have no tests and I don't have no time.
    """
    notes = serializers.SerializerMethodField(method_name="get_notes")
    serialization = serializers.SerializerMethodField(method_name="get_serialization")
    lemma = LemmaSerializer()

    authors = serializers.SerializerMethodField(method_name='get_assigned_authors')

    def get_assigned_authors(self, issue_lemma: 'IssueLemma') -> List[int]:
        return [
            assignment.author_id
            for assignment 
            in issue_lemma.authorissuelemmaassignment_set.all()
        ]


    @extend_schema_field(IssueLemmaSerializerOpenApi(many=True))
    def get_serialization(self, object):
        if object.serialization:
            if len(object.serialization) > 10:
                return object.serialization[-10:]
        else:
            return object.serialization

    def get_notes(self, object) -> Array:
        res = LemmaNote.objects.filter(lemma=object.lemma)
        return list(res.values_list("pk", flat=True))

    def update(self, instance, validated_data):
        if "lemma" in validated_data.keys():
            if isinstance(validated_data["lemma"], int):
                lemma = validated_data["lemma"]
            elif "id" in self.initial_data["lemma"].keys():
                lemma = Lemma.objects.get(pk=self.initial_data["lemma"]["id"])
                for k, v in self.initial_data["lemma"].items():
                    setattr(lemma, k, v)
                lemma.save()
                lemma = lemma.pk
            else:
                lemma = Lemma.objects.create(**validated_data["lemma"])
                lemma = lemma.pk
            instance.lemma_id = lemma
        for k, v in validated_data.items():
            if k == "lemma":
                continue
            elif k == "labels":
                instance.labels.set(v)
            else:
                setattr(instance, k, v)
        instance.save()
        return instance

    def create(self, validated_data):
        instance = IssueLemma()
        if isinstance(validated_data["lemma"], int):
            lemma = validated_data["lemma"]
        if "id" in validated_data["lemma"].keys():
            lemma = Lemma.objects.get(pk=validated_data["lemma"]["id"])
            for k, v in validated_data["lemma"].items():
                setattr(lemma, k, v)
            lemma = lemma.pk
        else:
            lemma = Lemma.objects.create(**validated_data["lemma"])
            lemma = lemma.pk
        instance.lemma_id = lemma
        for k, v in validated_data.items():
            if k == "lemma":
                continue
            setattr(instance, k, v)
        instance.save()
        return instance

    class Meta:
        model = IssueLemma
        fields = "__all__"
        read_only_fields = ["serialization"]
