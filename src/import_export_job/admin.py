# Copyright (C) 2019 o.s. Auto*Mat
from typing import Any

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from . import admin_actions, models


class JobWithStatusMixin:
    @admin.display(description=_("Job status info"))
    def job_status_info(self, obj):
        job_status = cache.get(self.direction + "_job_status_%s" % obj.pk)
        if job_status:
            return job_status
        else:
            return obj.job_status


class ImportJobForm(forms.ModelForm):
    model = forms.ChoiceField(label=_("Name of model to import to"))
    format = forms.ChoiceField(label=_("formats"))

    class Meta:
        model = models.ImportJob
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = [
            (x, x) for x in getattr(settings, "IMPORT_EXPORT_JOB_MODELS", {}).keys()
        ]

        self.fields["format"].choices = self.instance.get_format_choices()


@admin.register(models.ImportJob)
class ImportJobAdmin(JobWithStatusMixin, admin.ModelAdmin):
    direction = "import"
    form = ImportJobForm
    list_display = (
        "model",
        "job_status_info",
        "file_link",
        "errors",
        "change_summary_link",
        "imported",
        "owner",
        "updated_at",
    )
    readonly_fields = (
        "job_status_info",
        "change_summary",
        "imported",
        "errors",
        "owner",
        "updated_at",
        "processing_initiated",
    )
    exclude = ("job_status",)

    list_filter = ("model", "imported")

    actions = (
        admin_actions.run_import_job_action,
        admin_actions.run_import_job_action_dry,
    )

    def file_link(self, obj):
        url = reverse('get_blob', args=[obj.file.name])
        return mark_safe(f'<a href="{url}">{obj.file.name}</a>')

    file_link.short_description = models.ImportJob._meta.get_field('file').verbose_name

    def change_summary_link(self, obj):
        if obj.change_summary:
            url = reverse('get_blob', args=[obj.change_summary.name])
            return mark_safe(f'<a href="{url}">{obj.change_summary.name}</a>')
        return "-"

    change_summary_link.short_description = models.ImportJob._meta.get_field('change_summary').verbose_name

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> list[str] | tuple[Any, ...]:
        if obj:
            return ("file",) + self.readonly_fields
        else:
            return self.readonly_fields
