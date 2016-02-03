import configparser
import datetime
import os
import logging
import pathlib

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db.backends.signals import connection_created

from pathlib_revised import Path2 # https://github.com/jedie/pathlib revised/

from PyHardLinkBackup.phlb import BACKUP_RUN_CONFIG_FILENAME, INTERNAL_FILES
from PyHardLinkBackup.phlb.human import dt2naturaltimesince
from PyHardLinkBackup.phlb.config import phlb_config

log = logging.getLogger("phlb.%s" % __name__)


def setup_sqlite(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        pragmas = (
            "PRAGMA journal_mode = MEMORY;",
            "PRAGMA temp_store = MEMORY;",
            "PRAGMA synchronous = OFF;"
        )
        for pragma in pragmas:
            log.info("Execute: '%s'" % pragma)
            cursor.execute(pragma)

connection_created.connect(setup_sqlite)


def build_config_path(backup_path):
    return Path2(
        backup_path, BACKUP_RUN_CONFIG_FILENAME
    )


class BackupName(models.Model):
    name = models.CharField(max_length=1024,
        help_text=_("The name of the backup directory")
    )
    def __str__(self):
        return self.name


class SourcePath(models.Model):
    path = models.CharField(max_length=1024,
        help_text=_("Source path of the backup.")
    )
    def __str__(self):
        return self.path


class BackupRunManager(models.Manager):
    def get_from_config_file(self, backup_path):
        if not backup_path.is_dir():
            raise NotADirectoryError("Backup path %r not found!" % backup_path.path)

        config_path = build_config_path(backup_path)
        if not config_path.is_file():
            raise FileNotFoundError(
                "Config file %r not found!\nIs the given path a created Backup?" % config_path.path
            )

        config = configparser.ConfigParser()
        config.read(config_path.path)

        sections = config.sections()
        if "BACKUP_RUN" not in sections:
            raise KeyError(".ini section 'BACKUP_RUN' not found in: %s" % repr(sections))

        try:
            backup_run_pk = config.getint("BACKUP_RUN", "primary_key")
        except (KeyError, ValueError) as err:
            with config_path.open("r") as f:
                content = f.read().strip()
            raise KeyError(
                "%s in %s\nconfig content:\n%s" % (err, config_path.path, content)
            )

        backup_run = self.get_queryset().get(pk=backup_run_pk)

        if backup_path != backup_run.path_part():
            msg = (
                "Backup path mismatch:\n"
                "From database: %s\n"
                "Current path: %s\n"
                "Maybe the config file pointed to a wrong database entry?!?\n"
                "Used config file: %s"
            ) % (
                backup_run.path_part(), backup_path, config_path
            )
            log.error(msg)
            raise AssertionError(msg)

        return backup_run

    def create(self, name, source_path, backup_datetime):
        backup_name, created = BackupName.objects.get_or_create(name=name)
        source_path, created = SourcePath.objects.get_or_create(path=source_path)
        backup_run = super(BackupRunManager, self).create(
            name = backup_name,
            source_path = source_path,
            backup_datetime=backup_datetime,
        )
        return backup_run


class BackupRun(models.Model):
    """
    One Backup run prefix: start time + backup name
    """
    name = models.ForeignKey(BackupName)
    backup_datetime = models.DateTimeField(auto_now=False, auto_now_add=False, unique=True,
        help_text=_("backup_datetime of a started backup. Used in all path as prefix.")
    )
    source_path = models.ForeignKey(SourcePath)
    end_datetime = models.DateTimeField(auto_now=False, auto_now_add=False,
        blank=True, null=True,
        help_text=_("Moment of completion")
    )

    objects = BackupRunManager()

    def path_part(self):
        return Path2(
            phlb_config.backup_path,
            self.name.name,
            self.backup_datetime.strftime(phlb_config.sub_dir_formatter)
        )

    def get_config_path(self):
        return build_config_path(self.path_part())

    def make_config(self):
        config = configparser.ConfigParser()
        config["BACKUP_RUN"] = {"primary_key": str(self.pk)}
        return config

    def write_config(self):
        if self.pk is None:
            raise RuntimeError("Save is needed before write config!")

        config_path = self.get_config_path()
        if not config_path.parent.is_dir():
            raise NotADirectoryError("Path %r doesn't exists!" % config_path.parent.path)

        config = self.make_config()
        with config_path.open('w') as configfile:
            config.write(configfile)
        log.info("BackupRun config written: %s" % config_path)

    def finished(self):
        self.end_datetime = datetime.datetime.now()

    def save(self, *args, **kwargs):
        super(BackupRun, self).save(*args, **kwargs)
        self.write_config()

    def __str__(self):
        return "<BackupRun %s %s>" % (
            self.name,
            dt2naturaltimesince(self.backup_datetime),
        )

    class Meta:
        ordering = ["-backup_datetime"]
        get_latest_by = "backup_datetime"


class BackupDir(models.Model):
    """
    Unique sub path of backup files.
    """
    directory = models.CharField(max_length=1024, unique=True,
        help_text=_("The path in the backup without datetime and filename")
    )

    def path_part(self):
        return Path2(self.directory)

    def __str__(self):
        return self.path_part().path


class BackupFilename(models.Model):
    """
    Unique Filename.
    """
    filename = models.CharField(max_length=1024, unique=True,
        help_text=_("Filename of one file in backup")
    )

    def save(self, *args, **kwargs):
        # e.g: Test if 'phlb_config.ini' should be added
        assert self.filename not in INTERNAL_FILES # TODO: Add unittest
        super(BackupFilename, self).save(*args, **kwargs)

    def path_part(self):
        return Path2(self.filename)

    def __str__(self):
        return self.path_part().path


class ContentInfo(models.Model):
    hash_hexdigest = models.CharField(
        max_length=128, unique=True,
        help_text=_("Hash (hexdigest) of the file content")
    )
    file_size = models.PositiveIntegerField(
        help_text=_("The file size in Bytes")
    )

    def __str__(self):
        return "Hash: %s...%s File Size: %i Bytes" % (
            self.hash_hexdigest[:4], self.hash_hexdigest[-4:], self.file_size
        )


class BackupEntryManager(models.Manager):
    def create(self, backup_run, backup_entry_path, hash_hexdigest):
        backup_path = backup_run.path_part()
        rel_path = backup_entry_path.relative_to(backup_path)
        directory = rel_path.parent

        filename = backup_entry_path.name
        file_stat = backup_entry_path.stat()

        log.debug(
            "Save: %r %r %r %r %r",
            backup_run, directory, filename, hash_hexdigest, file_stat
        )
        directory, created = BackupDir.objects.get_or_create(directory=directory)
        filename, created = BackupFilename.objects.get_or_create(filename=filename)
        content_info, created = ContentInfo.objects.get_or_create(
            hash_hexdigest=hash_hexdigest, file_size=file_stat.st_size
        )

        backup_entry = super(BackupEntryManager, self).create(
            backup_run=backup_run,
            directory=directory,
            filename=filename,
            content_info=content_info,
            file_mtime_ns = file_stat.st_mtime_ns,
        )
        path = backup_entry.get_backup_path()
        assert path.is_file(), "File not exists: %s" % path
        assert path.stat().st_mtime_ns == backup_entry.file_mtime_ns
        return backup_entry


class BackupEntry(models.Model):
    backup_run = models.ForeignKey(BackupRun)
    directory = models.ForeignKey(BackupDir)
    filename = models.ForeignKey(BackupFilename)
    content_info = models.ForeignKey(ContentInfo)
    file_mtime_ns = models.PositiveIntegerField(
        help_text=_("Time of most recent content modification expressed in nanoseconds as an integer.")
    )
    no_link_source=models.BooleanField(default=False,
        help_text=_("Can this file be used as a hardlink source? (Will be set if a os.link() failed.)")
    )

    objects = BackupEntryManager()

    def get_backup_path(self):
        return Path2(
            self.backup_run.path_part(),
            self.directory.path_part(),
            self.filename.path_part(),
        )

    def __str__(self):
        return "%s %s mtime:%s" % (
            self.get_backup_path(), self.content_info, self.file_mtime_ns
        )

    class Meta:
        ordering = ["-backup_run__backup_datetime"]
        get_latest_by = "file_mtime_ns"
