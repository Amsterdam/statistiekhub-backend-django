# Copyright (C) 2019 o.s. Auto*Mat
from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.http.request import HttpRequest
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
            (x, x) for x in getattr(settings, "IMPORT_EXPORT_CELERY_MODELS", {}).keys()
        ]

        self.fields["format"].choices = self.instance.get_format_choices()
        # self.fields["format"].widget = forms.Select(
        #     choices=self.instance.get_format_choices()
        # )
        


@admin.register(models.ImportJob)
class ImportJobAdmin(JobWithStatusMixin, admin.ModelAdmin):
    direction = "import"
    form = ImportJobForm
    list_display = (
        "model",
        "job_status_info",
        "file",
        "errors",
        "change_summary",
        "imported",
        "author",
        "updated_by",
    )
    readonly_fields = (
        "job_status_info",
        "change_summary",
        "imported",
        "errors",
        "author",
        "updated_by",
        "processing_initiated",
    )
    exclude = ("job_status",)

    list_filter = ("model", "imported")

    actions = (
        admin_actions.run_import_job_action,
        admin_actions.run_import_job_action_dry,
    )


    def has_change_permission(self, request: HttpRequest, obj = None) -> bool:
        return False


class ExportJobForm(forms.ModelForm):
    class Meta:
        model = models.ExportJob
        exclude = ("site_of_origin",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource"].widget = forms.Select(
            choices=self.instance.get_resource_choices()
        )
        self.fields["format"].widget = forms.Select(
            choices=self.instance.get_format_choices()
        )


#@admin.register(models.ExportJob)
class ExportJobAdmin(JobWithStatusMixin, admin.ModelAdmin):
    direction = "export"
    form = ExportJobForm
    list_display = (
        "model",
        "app_label",
        "file",
        "job_status_info",
        "author",
        "updated_by",
    )
    readonly_fields = (
        "job_status_info",
        "author",
        "updated_by",
        "app_label",
        "model",
        "file",
        "processing_initiated",
    )
    exclude = ("job_status",)

    list_filter = ("model",)

    def has_add_permission(self, request, obj=None):
        return False

    actions = (admin_actions.run_export_job_action,)
