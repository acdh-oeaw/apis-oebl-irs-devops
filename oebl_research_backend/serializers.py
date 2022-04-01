from importlib.metadata import requires
import secrets
import typing
from numpy import require, source
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from typing import List as ListType

from .models import ListEntry, List, SecondaryLiterature, ProfessionGroup

gndType = ListType[str]


def create_no_wrong_properties_validator(
        allowed_properties: typing.Set[str], 
    ) -> typing.Callable[[dict, ], None]:
    def validate_properties(incoming_dict: dict) -> None:
        incoming_properties = set(incoming_dict.keys())
        not_allowed_properties = incoming_properties.difference(allowed_properties)
        if not_allowed_properties:
            raise serializers.ValidationError(detail=rf'Incomming properties {not_allowed_properties} are not permitted, only use {allowed_properties}')
    return validate_properties 


def create_mixed_types_validator(
        allowed_property_types: typing.Set[typing.Type] = {str, }, 
        allowed_value_types: typing.Set[typing.Type] = {str, None}
    ) -> typing.Callable[[dict, ], None]:
    
    def validate_mixed_types(incoming_dict: dict) -> None:
        wrong_value_types = {key: value for key, value in incoming_dict.items() if value.__class__ not in allowed_value_types}
        if wrong_value_types:
            raise serializers.ValidationError(detail=rf'All values must be one of {allowed_value_types}. The following are not: {wrong_value_types}')

        wrong_key_types = {key for key in incoming_dict.keys() if key.__class__ not in allowed_property_types}
        if wrong_key_types:
            raise serializers.ValidationError(detail=rf'All properties must be one of {allowed_property_types}. The following are not: {wrong_key_types}')

    return validate_mixed_types


def create_alternative_names_field(**additional_params: dict) -> serializers.ListField:
    """
    Define the field dynamically.

    Why define? Do not want to type them over and over
    Why define dynamically? 
        - First list field with no source changes `.source = None` to `.source = ''` which leads to an assertion error in ListField
        - And who knows, that kind of horrors await me, if I just pass that object around! ;-)
    """
    return serializers.ListField(
        **additional_params,
        required=False, allow_null=True, default=list,
        child = serializers.DictField(
                    source=None,
                    validators=[
                        create_no_wrong_properties_validator({'firstName', 'lastName'}),
                        create_mixed_types_validator({str, }, {str, None})
                    ]   
                )
        )
                            

def create_secondary_literature_field(**additional_params: dict) -> serializers.ListField:
    """
    Define the field dynamically.

    Why define? Do not want to type them over and over
    Why define dynamically? 
        - First list field with no source changes `.source = None` to `.source = ''` which leads to an assertion error in ListField
        - And who knows, that kind of horrors await me, if I just pass that object around! ;-)
    """
    return serializers.ListField(
        **additional_params,
        required=False, allow_null=True, default=list,
        child = serializers.DictField(
                    source=None,
                    validators=[
                        create_no_wrong_properties_validator({'title', 'pages', 'id'}),
                        create_mixed_types_validator({str, }, {str, int, None})
                    ]   
                )
        )


def create_gideon_legacy_literature_field(**additional_params: dict) -> serializers.ListField:
    """
    Define the field dynamically.

    Why define? Do not want to type them over and over
    Why define dynamically? 
        - First list field with no source changes `.source = None` to `.source = ''` which leads to an assertion error in ListField
        - And who knows, that kind of horrors await me, if I just pass that object around! ;-)
    """
    return serializers.ListField(
        **additional_params,
        required=False, allow_null=True, default=list,
        child = serializers.DictField(
                    source=None,
                    validators=[
                        create_no_wrong_properties_validator({'value', 'id'}),
                        create_mixed_types_validator({str, }, {str, int, None})
                    ]   
                )
        )


def create_zotero_keys_field(**additional_params: dict) -> serializers.ListField:
    """
    Define the field dynamically.

    Why define? Do not want to type them over and over
    Why define dynamically? 
        - First list field with no source changes `.source = None` to `.source = ''` which leads to an assertion error in ListField
        - And who knows, that kind of horrors await me, if I just pass that object around! ;-)
    """
    return serializers.ListField(
        **additional_params,
        required=False, allow_null=True, default=list,
        child = serializers.CharField(
                    source=None,
            )
        )

class EditorSerializer(serializers.Serializer):
    userId = serializers.IntegerField(source="pk")
    email = serializers.EmailField()
    name = serializers.SerializerMethodField(method_name="get_name")

    def get_name(self, object):
        if object.last_name is not None:
            return f"{object.last_name}, {object.first_name}"
        else:
            return object.username


class ListSerializer(serializers.ModelSerializer):
    editor = EditorSerializer(required=False)

    def create(self, validated_data):
        lst = List.objects.create(
            title=validated_data.get("title"), editor_id=self.context["request"].user.pk
        )
        return lst

    class Meta:
        model = List
        fields = "__all__"


class ListSerializerLimited(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = ["id", "title", "editor"]


class ProfessionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionGroup
        fields = ["id", "name"]


class ListEntrySerializer(serializers.ModelSerializer):
    gnd = serializers.SerializerMethodField(method_name="get_gnd")
    firstName = serializers.CharField(source="person.first_name", required=False, allow_null=True)
    lastName = serializers.CharField(source="person.name")
    alternativeNames = create_alternative_names_field(source='person.alternative_names')
    gender = serializers.CharField(source="person.gender", required=False, allow_null=True)
    dateOfBirth = serializers.DateField(source="person.date_of_birth", required=False, allow_null=True)
    dateOfDeath = serializers.DateField(source="person.date_of_death", required=False, allow_null=True)
    bioNote = serializers.CharField(source="person.bio_note", required=False, allow_null=True)
    kinship = serializers.CharField(source="person.kinship", required=False, allow_null=True)
    religion = serializers.CharField(source="person.religion", required=False, allow_null=True)
    list = ListSerializerLimited(required=False, allow_null=True)
    deleted = serializers.BooleanField(default=False)
    secondaryLiterature = create_secondary_literature_field(source='person.secondary_literature')
    gideonLegacyLiterature = create_gideon_legacy_literature_field(source='person.gideon_legacy_literature')
    zoteroKeysBy = create_zotero_keys_field(source='person.zotero_keys_by')
    zoteroKeysAbout = create_zotero_keys_field(source='person.zotero_keys_about')
    professionDetail = serializers.CharField(source='person.profession_detail', required=False, allow_null=True)
    professionGroup = ProfessionGroupSerializer(required=False, allow_null=True)

    def update(self, instance, validated_data):
        instance.selected = validated_data.get("selected", instance.selected)
        instance.columns_scrape = validated_data.get(
            "columns_scrape", instance.columns_scrape
        )
        instance.columns_user = validated_data.get(
            "columns_user", instance.columns_user
        )
        if "list" in self.initial_data.keys():
            if self.initial_data["list"] is None:
                instance.list_id = None
            elif "id" in self.initial_data["list"].keys():
                instance.list_id = self.initial_data["list"]["id"]
            else:
                if "editor" in self.initial_data["list"].keys():
                    self.initial_data["list"]["editor_id"] = self.initial_data[
                        "list"
                    ].pop("editor")
                lst = List.objects.create(**self.initial_data["list"])
                instance.list_id = lst.pk
        instance.save()
        changed = False
        if "gnd" in self.initial_data.keys():
            scrape_triggered = False
            for u in instance.person.uris:
                if "d-nb.info" in u:
                    if u not in [
                        f"https://d-nb.info/gnd/{x}/" for x in self.initial_data["gnd"]
                    ]:
                        instance.person.uris.remove(u)
                        changed = True
            for gnd in self.initial_data["gnd"]:
                if f"https://d-nb.info/gnd/{gnd}/" not in instance.person.uris:
                    instance.person.uris.append(f"https://d-nb.info/gnd/{gnd}/")
                    instance._update_scrape_triggered = True
                    changed = True
        pers_mapping = {
            "firstName": "first_name",
            "lastName": "name",
            "alternativeNames": "alternative_names",
            "dateOfBirth": "date_of_birth",
            "dateOfDeath": "date_of_death",
            "gender": "gender",
            "secondaryLiterature": "secondary_literature",
            "gideonLegacyLiterature": "gideon_legacy_literature",
            "zoteroKeysBy": "zotero_keys_by",
            "zoteroKeysAbout": "zotero_keys_about",
            "professionDetail": "profession_detail",
            "professeionGroup": "profession_group",
            "bioNote": "bio_note",
            "kinship": "kinship",
            "religion": "religion"
        }
        for pers_field, pers_map in pers_mapping.items():
            if pers_field in self.initial_data.keys():
                setattr(instance.person, pers_map, self.initial_data[pers_field])
                changed = True
        if changed:
            instance.person.save()
        return instance

    def get_gnd(self, object) -> gndType:
        if object.person.uris is not None:
            res = []
            for uri in object.person.uris:
                if "d-nb.info" in uri:
                    res.append(uri.split("/")[-2])
            return res
        return []

    class Meta:
        model = ListEntry
        fields = [
            "id",
            "gnd",
            "selected",
            "list",
            "firstName",
            "lastName",
            "alternativeNames",
            "dateOfBirth",
            "dateOfDeath",
            "gender",
            "columns_user",
            "columns_scrape",
            "deleted",
            "last_updated",
            "secondaryLiterature",
            "gideonLegacyLiterature",
            "zoteroKeysBy",
            "zoteroKeysAbout",
            "professionDetail",
            "professionGroup",
            "bioNote",
            "kinship",
            "religion"
        ]
