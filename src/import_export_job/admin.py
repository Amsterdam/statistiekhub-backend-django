# Copyright (C) 2019 o.s. Auto*Mat
import logging
from typing import Any

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from import_export_job import admin_actions, models

logger = logging.getLogger(__name__)

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
        self.user = kwargs.pop('user')
        self.import_job_models = getattr(settings, "IMPORT_EXPORT_JOB_MODELS", {})

        self.modifier = self.user.is_superuser
        if self.user.groups.filter(name='modifier_statistiekhub_tabellen').exists():
            self.modifier = True

        super().__init__(*args, **kwargs)

        self.fields["model"].choices = self._get_model_choices()
        self.fields["format"].choices = self.instance.get_format_choices()

    def _get_model_choices(self) -> list:
        _import_job_models = self.import_job_models.copy()
        if not self.modifier:
            logger.info(f"user not in modifier-group")
            _import_job_models.pop("SpatialDimension")
            _import_job_models.pop("TemporalDimension")
            
        return [(x, x) for x in _import_job_models.keys()]


@admin.register(models.ImportJob)
class ImportJobAdmin(JobWithStatusMixin, admin.ModelAdmin):
    direction = "import"
    form = ImportJobForm

    def get_form(self, request, *args, **kwargs):
        Form = super().get_form(request, *args, **kwargs)

        class AdminFormWithUser(Form):
            def __new__(cls, *args, **kwargs):
                kwargs['user'] = request.user
                return Form(*args, **kwargs)

        return AdminFormWithUser

    list_display = (
        "id",
        "model",
        "job_status_info",
        "file_link",
        "errors",
        "change_summary_link",
        "created_by_full_name",
        "imported",
        "created_at",
    )
    readonly_fields = (
        "job_status_info",
        "change_summary",
        "imported",
        "errors",       
        "updated_at",
        "created_at",
        "processing_initiated",
    )
    exclude = ("job_status", 'created_by',)

    list_filter = ("model", "imported")

    def file_link(self, obj):
        url = reverse('get_blob', args=[obj.file.name])
        return mark_safe(f'<a href="{url}" target="_blank" >{obj.file.name}</a>')

    file_link.short_description = models.ImportJob._meta.get_field('file').verbose_name

    def change_summary_link(self, obj):
        if obj.change_summary:
            url = reverse('get_blob', args=[obj.change_summary.name])
            return mark_safe(f'<a href="{url}" target="_blank" >{obj.change_summary.name}</a>')
        return "-"

    change_summary_link.short_description = models.ImportJob._meta.get_field('change_summary').verbose_name

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> list[str] | tuple[Any, ...]:
        if obj:
            return ("file",) + self.readonly_fields
        else:
            return self.readonly_fields

    actions = (
        admin_actions.run_import_job_action,
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set the user when the object is created
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def created_by_full_name(self, obj):
        return obj.created_by.get_full_name()