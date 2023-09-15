# Copyright (C) 2019 o.s. Auto*Mat

from django.conf import settings
from django.utils import timezone

from author.decorators import with_author

from django.db import models, transaction
from django.dispatch import receiver

from django.db.models.signals import post_save, post_delete
from django.utils.translation import gettext_lazy as _

from import_export.formats.base_formats import DEFAULT_FORMATS

from ..fields import ImportExportFileField
from ..tasks import run_import_job

import logging

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
        return [
            (f.CONTENT_TYPE, f().get_title())
            for f in DEFAULT_FORMATS
            if f().can_import()
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
                    "Some error occurred while deleting ImportJob change_summary file: {0}".format(e))
                                
        ImportJob.objects.filter(id=instance.id).delete()


# @receiver(models.signals.pre_save, sender=ImportJob)
# def auto_delete_file_on_change(sender, instance, **kwargs):
#     """
#     Deletes old file from filesystem
#     when corresponding `ImportJob` object is updated
#     with new file.
#     """
#     # first time save -> exit
#     # if not instance._state.adding:
#     #     return False

#     try:
#         old_file = ImportJob.objects.get(pk=instance.pk).change_summary
#     except ImportJob.DoesNotExist:
#         return False

#     new_file = instance.change_summary

#     print(f'----------------------------in presave: {old_file} {new_file}')

#     if not old_file == new_file and old_file != None:
#         try:
#             instance.change_summary.delete()
#         except Exception as e:
#             logger.error(
#                 "Some error occurred while deleting ImportJob change_summary file: {0}".format(e))
