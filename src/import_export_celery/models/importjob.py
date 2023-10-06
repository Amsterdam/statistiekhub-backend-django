# Copyright (C) 2019 o.s. Auto*Mat

import logging

from author.decorators import with_author
from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ..utils import DEFAULT_FORMATS

from ..fields import ImportExportFileField
from ..tasks import run_import_job

logger = logging.getLogger(__name__)


@with_author
class ImportJob(models.Model):
    file = ImportExportFileField(
        verbose_name=_("File to be imported"),
        upload_to="django-import-export-celery-import-jobs",
        blank=False,
        null=False,
        max_length=255,
    )

    processing_initiated = models.DateTimeField(
        verbose_name=_("Started processing the file"),
        null=True,
        blank=True,
        default=None,
    )

    imported = models.DateTimeField(
        verbose_name=_("Import completed"),
        null=True,
        blank=True,
        default=None,
    )

    format = models.CharField(
        verbose_name=_("Format of file to be imported"),
        max_length=255,
    )

    change_summary = ImportExportFileField(
        verbose_name=_("Summary of changes made by this import"),
        upload_to="django-import-export-celery-import-change-summaries",
        blank=True,
        null=True,
    )

    errors = models.TextField(
        verbose_name=_("Errors"),
        default="",
        blank=True,
    )

    model = models.CharField(
        verbose_name=_("Name of model to import to"),
        max_length=160,
    )

    job_status = models.CharField(
        verbose_name=_("Status of the job"),
        max_length=160,
        blank=True,
    )

    class Meta:
        verbose_name = _("Import job")
        verbose_name_plural = _("Import jobs")

    @staticmethod
    def get_format_choices():
        """returns choices of available import formats"""
        formats = DEFAULT_FORMATS
        return [
            (f.CONTENT_TYPE, f().get_title())
            for f in formats
        ]


@receiver(post_save, sender=ImportJob)
def importjob_post_save(sender, instance, **kwargs):
    if not instance.processing_initiated:
        instance.processing_initiated = timezone.now()
        instance.save()
        transaction.on_commit(
            lambda: run_import_job.delay(
                instance.pk,
                dry_run=getattr(settings, "IMPORT_DRY_RUN_FIRST_TIME", True),
            )
        )


@receiver(post_delete, sender=ImportJob)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes files related to the import job
    """
    if instance.file:
        try:
            instance.file.delete()
        except Exception as e:
            logger.error(
                "Some error occurred while deleting ImportJob file: {0}".format(e)
            )

        # remove summary file if exists
        if instance.change_summary:
            try:
                instance.change_summary.delete()
            except Exception as e:
                logger.error(
                    "Some error occurred while deleting ImportJob change_summary file: {0}".format(
                        e
                    )
                )

        ImportJob.objects.filter(id=instance.id).delete()
