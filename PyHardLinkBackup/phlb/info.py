import datetime

import django
from django.db.models import Sum
from django.utils.timesince import timesince

from PyHardLinkBackup.backup_app.models import BackupName, BackupRun, \
    BackupEntry, SourcePath
from PyHardLinkBackup.phlb.human import dt2naturaltimesince, ns2naturaltimesince, \
    human_filesize, dt2string, human_time


def backup_info(backup_name):
    backup_name = BackupName.objects.get(name=backup_name)
    backup_runs = BackupRun.objects.filter(name=backup_name)

    yield ""
    yield "Existing sources paths are:"
    source_paths = SourcePath.objects.filter(backuprun__name=backup_name).distinct()
    for source_path in source_paths:
        path = source_path.path
        if path == "migrated":
            yield "\t<unknown path because of migration>"
        else:
            yield "\t%s" % path
    yield ""

    backup_count = backup_runs.count()
    yield "For '%s' exist %i backups." % (backup_name, backup_count)

    latest_backup = backup_runs[0]
    yield "Information from latest Backup:"
    yield from backup_run_info(latest_backup)


def backup_run_info(backup_run):
    yield "Source path:"
    source_path = backup_run.source_path.path
    if source_path == "migrated":
        yield "path is unknown path because of migration."
    else:
        yield "%s" % source_path
    yield ""

    yield "Backup path:"
    yield "%s" % backup_run.path_part() # Don't yield Path2() instance ;)
    yield ""

    yield "Backup start time: %s" % dt2naturaltimesince(backup_run.backup_datetime)

    if backup_run.end_datetime is None:
        yield "WARNING: Backup is incomplete!"
    else:
        yield "Backup end time: %s" % dt2string(backup_run.end_datetime)
        duration = backup_run.end_datetime - backup_run.backup_datetime
        yield "backup duration: %s" % human_time(duration)

    backup_files = BackupEntry.objects.filter(backup_run=backup_run)
    file_count = backup_files.count()
    yield "Backup contains %i files." % file_count

    total_size = backup_files.aggregate(
        total_size=Sum("content_info__file_size")
    )["total_size"]
    yield "Total file size: %s" % human_filesize(total_size)

    try:
        latest_entry = backup_files.latest()
    except BackupEntry.DoesNotExist:
        yield "Warning: Latest backup run contains no files?!?"
    else:
        latest_mtime_ns = latest_entry.file_mtime_ns
        yield "Latest file modified time: %s" % ns2naturaltimesince(latest_mtime_ns)





if __name__ == '__main__':
    django.setup()

    print("-"*79)
    for line in backup_info(backup_name="src"):
        print(line)
    print("-"*79)
