from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from typing import List as ListType

from .models import ListEntry, List

gndType = ListType[str]


class EditorSerializer(serializers.Serializer):
    userId = serializers.IntegerField(source="pk")
    email = serializers.EmailField(source="email")
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


class ListEntrySerializer(serializers.ModelSerializer):
    gnd = serializers.SerializerMethodField(method_name="get_gnd")
    firstName = serializers.CharField(source="person.first_name")
    lastName = serializers.CharField(source="person.name")
    dateOfBirth = serializers.DateField(source="person.date_of_birth")
    dateOfDeath = serializers.DateField(source="person.date_of_death")
    list = ListSerializerLimited(required=False, allow_null=True)

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
            "dateOfBirth": "date_of_birth",
            "dateOfDeath": "date_of_death",
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
            "dateOfBirth",
            "dateOfDeath",
            "columns_user",
            "columns_scrape",
        ]
