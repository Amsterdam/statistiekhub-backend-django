import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory
from model_bakery import baker

from referentie_tabellen.referentie_choices import TemporaltypeChoices
from statistiek_hub.admin import TopicSetAdmin
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.topic_set import TopicSet


@pytest.mark.django_db
def test_topic_set_admin_add_form_excludes_deprecated_measure():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make("auth.Group")
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

    request = RequestFactory().get("/admin/statistiek_hub/topicset/add/")
    model_admin = TopicSetAdmin(TopicSet, admin.site)
    measure_field = TopicSet._meta.get_field("measure")
    formfield = model_admin.formfield_for_foreignkey(measure_field, request)
    queryset_ids = set(formfield.queryset.values_list("id", flat=True))

    assert active_measure.id in queryset_ids
    assert deprecated_measure.id not in queryset_ids


@pytest.mark.django_db
def test_topic_set_admin_rejects_edit_and_delete_for_deprecated_measure():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make("auth.Group")
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
    obj = baker.make(TopicSet, topic=baker.make("statistiek_hub.Topic"), measure=measure)
    user = baker.make(User, is_superuser=True, is_staff=True)
    request = RequestFactory().get("/admin/statistiek_hub/topicset/")
    request.user = user
    model_admin = TopicSetAdmin(TopicSet, admin.site)

    assert model_admin.has_change_permission(request, obj) is False
    assert model_admin.has_delete_permission(request, obj) is False


@pytest.mark.django_db
def test_topic_set_admin_bulk_delete_skips_deprecated_measure_relations():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make("auth.Group")
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
    topic = baker.make("statistiek_hub.Topic")
    deprecated_topic_set = baker.make(TopicSet, topic=topic, measure=deprecated_measure)
    active_topic_set = baker.make(TopicSet, topic=topic, measure=active_measure)
    user = baker.make(User, is_superuser=True, is_staff=True)
    request = RequestFactory().post("/admin/statistiek_hub/topicset/")
    request.user = user
    model_admin = TopicSetAdmin(TopicSet, admin.site)

    queryset = TopicSet.objects.filter(id__in=[deprecated_topic_set.id, active_topic_set.id])
    model_admin.delete_queryset(request, queryset)

    assert TopicSet.objects.filter(id=deprecated_topic_set.id).exists()
    assert not TopicSet.objects.filter(id=active_topic_set.id).exists()
