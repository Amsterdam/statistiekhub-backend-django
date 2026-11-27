import pytest
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.test import RequestFactory
from model_bakery import baker

from statistiek_hub.modeladmins.measure_admin import MeasureAdmin
from statistiek_hub.models.measure import Measure


@pytest.mark.django_db
def test_measure_admin_deprecated_object_has_only_deprecated_fields_editable():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    measure = baker.make(
        Measure,
        name="DEP_VAR",
        unit=unit,
        team=baker.make(Group),
        deprecated=True,
    )

    request = RequestFactory().get("/admin/statistiek_hub/measure/1/change/")
    model_admin = MeasureAdmin(Measure, admin.site)
    readonly_fields = set(model_admin.get_readonly_fields(request, obj=measure))

    assert "label" in readonly_fields
    assert "unit" in readonly_fields
    assert "deprecated_reason" not in readonly_fields
    assert "deprecated_date" not in readonly_fields
    assert "deprecated" not in readonly_fields


@pytest.mark.django_db
def test_measure_admin_non_deprecated_object_keeps_default_readonly_fields():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    measure = baker.make(
        Measure,
        name="ACTIVE_VAR",
        unit=unit,
        team=baker.make(Group),
        deprecated=False,
    )

    request = RequestFactory().get("/admin/statistiek_hub/measure/1/change/")
    model_admin = MeasureAdmin(Measure, admin.site)

    assert model_admin.get_readonly_fields(request, obj=measure) == ["name"]


@pytest.mark.django_db
def test_measure_admin_delete_permission_rejects_deprecated_measure():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)
    measure = baker.make(
        Measure,
        name="OLD_VAR",
        unit=unit,
        team=team,
        deprecated=True,
    )
    user = baker.make(User, groups=[team])
    request = RequestFactory().get("/admin/statistiek_hub/measure/")
    request.user = user

    model_admin = MeasureAdmin(Measure, admin.site)

    assert model_admin.has_delete_permission(request, measure) is False


@pytest.mark.django_db
def test_measure_admin_bulk_delete_skips_deprecated_measures():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)
    deprecated_measure = baker.make(
        Measure,
        name="OLD_VAR",
        unit=unit,
        team=team,
        deprecated=True,
    )
    active_measure = baker.make(
        Measure,
        name="NEW_VAR",
        unit=unit,
        team=team,
        deprecated=False,
    )
    user = baker.make(User, is_superuser=True, is_staff=True)
    request = RequestFactory().post("/admin/statistiek_hub/measure/")
    request.user = user
    model_admin = MeasureAdmin(Measure, admin.site)

    queryset = Measure.objects.filter(id__in=[deprecated_measure.id, active_measure.id])
    model_admin.delete_queryset(request, queryset)

    assert Measure.objects.filter(id=deprecated_measure.id).exists()
    assert not Measure.objects.filter(id=active_measure.id).exists()
