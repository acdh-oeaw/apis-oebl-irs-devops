# Generated by Django 3.1.14 on 2022-06-28 11:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oebl_irs_workflow', '0002_lemmaarticle_lemmaarticleversion_userarticleassignment_userarticlepermission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lemmaarticleversion',
            name='lemma_article',
        ),
        migrations.RemoveField(
            model_name='userarticleassignment',
            name='lemma_article',
        ),
        migrations.RemoveField(
            model_name='userarticleassignment',
            name='user',
        ),
        migrations.RemoveField(
            model_name='userarticlepermission',
            name='lemma_article',
        ),
        migrations.RemoveField(
            model_name='userarticlepermission',
            name='user',
        ),
        migrations.DeleteModel(
            name='LemmaArticle',
        ),
        migrations.DeleteModel(
            name='LemmaArticleVersion',
        ),
        migrations.DeleteModel(
            name='UserArticleAssignment',
        ),
        migrations.DeleteModel(
            name='UserArticlePermission',
        ),
    ]
