from datetime import date

import pytest
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.test import RequestFactory
from model_bakery import baker

from referentie_tabellen.models import SpatialDimensionType, TemporalDimensionType, Unit
from referentie_tabellen.referentie_choices import TemporaltypeChoices
from statistiek_hub.modeladmins.observation_admin import ObservationAdmin
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension


def _make_observation_with_measure_deprecated(*, deprecated: bool) -> Observation:
    unit, _ = Unit.objects.get_or_create(name="aantal")
    team = baker.make(Group)
    measure = baker.make(
        Measure,
        name="OLD_VAR" if deprecated else "NEW_VAR",
        label="Deprecated variable" if deprecated else "Active variable",
        definition="Deprecated variable" if deprecated else "Active variable",
        unit=unit,
        team=team,
        deprecated=deprecated,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )
    spatial_type, _ = SpatialDimensionType.objects.get_or_create(name="WIJK")
    temporal_type, _ = TemporalDimensionType.objects.get_or_create(
        name="Peildatum",
        defaults={"type": TemporaltypeChoices.PEILDATUM},
    )
    spatial, _ = SpatialDimension.objects.get_or_create(
        code="A1",
        type=spatial_type,
        source_date=date(2024, 1, 1),
    )
    temporal, _ = TemporalDimension.objects.get_or_create(
        type=temporal_type,
        startdate=date(2024, 1, 1),
    )
    return baker.make(
        Observation,
        measure=measure,
        spatialdimension=spatial,
        temporaldimension=temporal,
        value=10,
    )


@pytest.mark.django_db
def test_observation_admin_add_form_excludes_deprecated_measure():
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

    request = RequestFactory().get("/admin/statistiek_hub/observation/add/")
    model_admin = ObservationAdmin(Observation, admin.site)
    measure_field = Observation._meta.get_field("measure")
    formfield = model_admin.formfield_for_foreignkey(measure_field, request)
    queryset_ids = set(formfield.queryset.values_list("id", flat=True))

    assert active_measure.id in queryset_ids
    assert deprecated_measure.id not in queryset_ids


@pytest.mark.django_db
def test_observation_admin_edit_keeps_relation_fields_readonly():
    request = RequestFactory().get("/admin/statistiek_hub/observation/1/change/")
    model_admin = ObservationAdmin(Observation, admin.site)

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
    spatial_type = baker.make("referentie_tabellen.SpatialDimensionType", name="WIJK")
    temporal_type = baker.make(
        "referentie_tabellen.TemporalDimensionType",
        name="Peildatum",
        type=TemporaltypeChoices.PEILDATUM,
    )
    spatial = baker.make(
        "statistiek_hub.SpatialDimension",
        code="A1",
        type=spatial_type,
        source_date=date(2024, 1, 1),
    )
    temporal = baker.make(
        "statistiek_hub.TemporalDimension",
        type=temporal_type,
        startdate=date(2024, 1, 1),
    )
    observation = baker.make(
        Observation,
        measure=measure,
        spatialdimension=spatial,
        temporaldimension=temporal,
        value=10,
    )

    readonly_fields = model_admin.get_readonly_fields(request, observation)
    assert set(readonly_fields) == {"measure", "temporaldimension", "spatialdimension"}


@pytest.mark.django_db
def test_observation_admin_change_permission_rejects_deprecated_measure_observation():
    observation = _make_observation_with_measure_deprecated(deprecated=True)
    user = baker.make(User, groups=[observation.measure.team])
    request = RequestFactory().get("/admin/statistiek_hub/observation/")
    request.user = user
    model_admin = ObservationAdmin(Observation, admin.site)

    assert model_admin.has_change_permission(request, observation) is False


@pytest.mark.django_db
def test_observation_admin_change_permission_allows_active_measure_observation():
    observation = _make_observation_with_measure_deprecated(deprecated=False)
    user = baker.make(User, groups=[observation.measure.team])
    request = RequestFactory().get("/admin/statistiek_hub/observation/")
    request.user = user
    model_admin = ObservationAdmin(Observation, admin.site)

    assert model_admin.has_change_permission(request, observation) is True


@pytest.mark.django_db
def test_observation_admin_delete_permission_rejects_deprecated_measure_observation():
    observation = _make_observation_with_measure_deprecated(deprecated=True)
    user = baker.make(User, groups=[observation.measure.team])
    request = RequestFactory().get("/admin/statistiek_hub/observation/")
    request.user = user
    model_admin = ObservationAdmin(Observation, admin.site)

    assert model_admin.has_delete_permission(request, observation) is False


@pytest.mark.django_db
def test_observation_admin_delete_permission_allows_active_measure_observation():
    observation = _make_observation_with_measure_deprecated(deprecated=False)
    user = baker.make(User, groups=[observation.measure.team])
    request = RequestFactory().get("/admin/statistiek_hub/observation/")
    request.user = user
    model_admin = ObservationAdmin(Observation, admin.site)

    assert model_admin.has_delete_permission(request, observation) is True


@pytest.mark.django_db
def test_observation_admin_bulk_delete_skips_deprecated_measure_observations():
    deprecated_observation = _make_observation_with_measure_deprecated(deprecated=True)
    active_observation = _make_observation_with_measure_deprecated(deprecated=False)
    user = baker.make(User, is_superuser=True, is_staff=True)
    request = RequestFactory().post("/admin/statistiek_hub/observation/")
    request.user = user
    model_admin = ObservationAdmin(Observation, admin.site)

    queryset = Observation.objects.filter(id__in=[deprecated_observation.id, active_observation.id])
    model_admin.delete_queryset(request, queryset)

    assert Observation.objects.filter(id=deprecated_observation.id).exists()
    assert not Observation.objects.filter(id=active_observation.id).exists()
