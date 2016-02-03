# coding: utf-8

from django.db import migrations, models


def migrate_names(apps, schema_editor):
    BackupName = apps.get_model("backup_app", "BackupName")
    BackupRun = apps.get_model("backup_app", "BackupRun")
    backup_names = set()
    for backup_run in BackupRun.objects.all():
        backup_name, created = BackupName.objects.get_or_create(name=backup_run.name_old)
        backup_run.name=backup_name
        backup_run.save()
        backup_names.add(backup_name.name)
    print("\nMigrate backup names: %s" % ", ".join(backup_names))


class Migration(migrations.Migration):
    dependencies = [
        ('backup_app', '0004_BackupRun_ini_file_20160203_1415'),
    ]
    operations = [
        migrations.CreateModel(
            name='BackupName',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024, help_text='The name of the backup directory')),
            ],
        ),
        migrations.RenameField(
            model_name='BackupRun',
            old_name='name',
            new_name='name_old',
        ),
        migrations.AddField(
            model_name='BackupRun',
            name='name',
            field=models.ForeignKey(to='backup_app.BackupName', default=0),
            preserve_default=False,
        ),
        migrations.RunPython(migrate_names),
        migrations.RemoveField(
            model_name='BackupRun',
            name='name_old',
        ),
    ]
