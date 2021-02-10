# Generated by Django 3.1.5 on 2021-02-08 16:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oebl_irs_workflow', '0001_initial'),
        ('oebl_research_backend', '0002_listentry_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='irs_person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='oebl_irs_workflow.lemma'),
        ),
    ]
