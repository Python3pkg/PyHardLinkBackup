# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime

def migrate_end_datetime(apps, schema_editor):
    SourcePath = apps.get_model("backup_app", "SourcePath")
    source_path = SourcePath(path="migrated")
    source_path.save()
    BackupRun = apps.get_model("backup_app", "BackupRun")
    for backup_run in BackupRun.objects.all():
        if backup_run.completed:
            backup_run.source_path = source_path
            backup_run.end_datetime = backup_run.backup_datetime
            backup_run.save()


class Migration(migrations.Migration):

    dependencies = [
        ('backup_app', '0006_BackupNames_20160203_2007'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourcePath',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('path', models.CharField(max_length=1024, help_text="Source path of the backup.")),
            ],
        ),
        migrations.AddField(
            model_name='BackupRun',
            name='source_path',
            field=models.ForeignKey(to='backup_app.SourcePath', default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='backuprun',
            name='end_datetime',
            field=models.DateTimeField(help_text='Moment of completion', blank=True, null=True),
        ),
        migrations.RunPython(migrate_end_datetime),
        migrations.RemoveField(
            model_name='backuprun',
            name='completed',
        ),
    ]
