# Generated by Django 3.1.14 on 2022-07-07 11:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oebl_editor', '0003_auto_20220705_1136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userarticlepermission',
            name='lemma_article',
        ),
        migrations.RemoveField(
            model_name='userarticlepermission',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserArticleAssignment',
        ),
        migrations.DeleteModel(
            name='UserArticlePermission',
        ),
    ]
