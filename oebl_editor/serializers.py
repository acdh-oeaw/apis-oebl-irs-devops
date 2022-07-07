from oebl_editor.models import LemmaArticle, LemmaArticleVersion, UserArticleAssignment
from rest_framework import serializers


class LemmaArticleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LemmaArticle
        fields = ('issue_lemma', 'published', 'current_version', )
        

class LemmaArticleVersionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LemmaArticleVersion
        fields = ('lemma_article', 'markup', 'date_created', 'date_modified', )
        read_only_fields = ('date_created', 'date_modified', )
        

userArticleEdityTypeMappingFields = ('lemma_article', 'user', 'edit_type', )
        
        
class UserArticleAssignmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserArticleAssignment
        fields = userArticleEdityTypeMappingFields
