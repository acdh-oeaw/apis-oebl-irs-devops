from django.dispatch import receiver
from django.db.models.signals import post_save
from oebl_editor.models import LemmaArticle, LemmaArticleVersion

from oebl_irs_workflow.models import IssueLemma


@receiver(post_save, sender=IssueLemma)
def create_article(sender, instance, created, **kwargs):
    markup = {"type": "doc", "content": [{"type": "paragraph", "content": [{"text": "test", "type": "text", "marks": [{"type": "comment", "attrs": {"id": None}}]}]}, {"type": "paragraph", "content": [{"text": "test", "type": "text", "marks": [{"type": "comment", "attrs": {"id": None}}]}]}, {"type": "paragraph"}]}
    if created:
        il = LemmaArticle.objects.create(issue_lemma=instance)
        LemmaArticleVersion.objects.create(lemma_article=il, markup=markup)