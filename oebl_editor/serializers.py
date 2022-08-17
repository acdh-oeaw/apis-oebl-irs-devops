from oebl_editor.models import LemmaArticle, LemmaArticleVersion
from oebl_irs_workflow.models import EditTypes
from rest_framework import serializers


class LemmaArticleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LemmaArticle
        fields = ('issue_lemma', 'published', )
        

class LemmaArticleVersionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LemmaArticleVersion
        fields = ('lemma_article', 'markup', 'date_created', 'date_modified', 'id', )
        read_only_fields = ('date_created', 'date_modified', 'id', )



class IssueLemmaUserAssignmentSerializer(serializers.Serializer):
    """
    Utility class to list EditTypes
    """

    edit_types = serializers.ListField(
        child = serializers.ChoiceField(EditTypes),
        read_only = True,
    )