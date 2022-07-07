# Generated by Django 3.1.14 on 2022-07-07 11:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oebl_irs_workflow', '0003_auto_20220628_1305'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issuelemma',
            name='author',
        ),
        migrations.CreateModel(
            name='AuthorIssueLemmaAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('edit_type', models.CharField(choices=[('VIEW', 'VIEW'), ('COMMENT', 'COMMENT'), ('ANNOTATE', 'ANNOTATE'), ('WRITE', 'WRITE')], max_length=8)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='oebl_irs_workflow.author')),
                ('issue_lemma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='oebl_irs_workflow.issuelemma')),
            ],
        ),
    ]
