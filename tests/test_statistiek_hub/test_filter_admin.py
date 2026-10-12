import pytest
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.test import RequestFactory
from model_bakery import baker

from referentie_tabellen.referentie_choices import TemporaltypeChoices
from statistiek_hub.modeladmins.filter_admin import FilterAdmin
from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure


@pytest.mark.django_db
def test_filter_admin_add_form_excludes_deprecated_measure():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)
    deprecated_measure = baker.make(
        Measure,
        name="OLD_VAR",
        label="Deprecated variable",
        definition="Deprecated variable",
        unit=unit,
        team=team,
        deprecated=True,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )
    active_measure = baker.make(
        Measure,
        name="NEW_VAR",
        label="Active variable",
        definition="Active variable",
        unit=unit,
        team=team,
        deprecated=False,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )

    request = RequestFactory().get("/admin/statistiek_hub/filter/add/")
    model_admin = FilterAdmin(Filter, admin.site)
    measure_field = Filter._meta.get_field("measure")
    formfield = model_admin.formfield_for_foreignkey(measure_field, request)
    queryset_ids = set(formfield.queryset.values_list("id", flat=True))

    assert active_measure.id in queryset_ids
    assert deprecated_measure.id not in queryset_ids


@pytest.mark.django_db
def test_filter_admin_rejects_edit_and_delete_for_deprecated_measure():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)
    measure = baker.make(
        Measure,
        name="OLD_VAR",
        label="Deprecated variable",
        definition="Deprecated variable",
        unit=unit,
        team=team,
        deprecated=True,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )
    obj = baker.make(Filter, measure=measure, rule="x > 0")
    user = baker.make(User, groups=[team])
    request = RequestFactory().get("/admin/statistiek_hub/filter/")
    request.user = user
    model_admin = FilterAdmin(Filter, admin.site)

    assert model_admin.has_change_permission(request, obj) is False
    assert model_admin.has_delete_permission(request, obj) is False


@pytest.mark.django_db
def test_filter_admin_bulk_delete_skips_deprecated_measure_filters():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)
    deprecated_measure = baker.make(
        Measure,
        name="OLD_VAR",
        label="Deprecated variable",
        definition="Deprecated variable",
        unit=unit,
        team=team,
        deprecated=True,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )
    active_measure = baker.make(
        Measure,
        name="NEW_VAR",
        label="Active variable",
        definition="Active variable",
        unit=unit,
        team=team,
        deprecated=False,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )
    deprecated_filter = baker.make(Filter, measure=deprecated_measure, rule="x > 0")
    active_filter = baker.make(Filter, measure=active_measure, rule="x > 0")
    user = baker.make(User, is_superuser=True, is_staff=True)
    request = RequestFactory().post("/admin/statistiek_hub/filter/")
    request.user = user
    model_admin = FilterAdmin(Filter, admin.site)

    queryset = Filter.objects.filter(measure_id__in=[deprecated_filter.measure_id, active_filter.measure_id])
    model_admin.delete_queryset(request, queryset)

    assert Filter.objects.filter(pk=deprecated_filter.pk).exists()
    assert not Filter.objects.filter(pk=active_filter.pk).exists()
