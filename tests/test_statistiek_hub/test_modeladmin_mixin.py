import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission, User
from django.test import RequestFactory
from model_bakery import baker

from referentie_tabellen.models import Theme
from statistiek_hub.modeladmins.admin_mixins import CheckPermissionUserMixin
from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure


@pytest.fixture
def fill_db()-> dict:
    group = baker.make(Group)
    user = baker.make(User, groups=[group])

    theme = baker.make(Theme, name="THEME1", group=group)
    measure = baker.make(Measure, theme=theme)

    return {
        "user": user,
        "measure": measure,
    }


class DummyAdmin(CheckPermissionUserMixin, admin.ModelAdmin):  
    pass


@pytest.mark.django_db
def test_get_user_groups_caching():
    group = baker.make(Group)
    user = baker.make(User, groups=[group])

    request = RequestFactory().get('/')
    request.user = user

    mixin = CheckPermissionUserMixin()
    groups_first = mixin._get_user_groups(request)
    groups_second = mixin._get_user_groups(request)

    assert list(groups_first) == list(groups_second)
    assert hasattr(request, '_cached_user_groups')

    group.delete()
    user.delete()


@pytest.mark.django_db
def test_has_permission_with_theme_group(fill_db):
    fixture = fill_db

    request = RequestFactory().get('/')
    request.user = fixture["user"]

    obj = fixture["measure"]

    admin_instance = DummyAdmin(model=Measure, admin_site=AdminSite())
    assert admin_instance.has_change_permission(request, obj) is True
    assert admin_instance.has_delete_permission(request, obj) is True


@pytest.mark.django_db
def test_has_permission_with_measure_group(fill_db):
    fixture = fill_db

    request = RequestFactory().get('/')
    request.user = fixture["user"]

    obj = baker.make(Filter, measure=fixture["measure"])

    mixin = CheckPermissionUserMixin()
    assert mixin.has_change_permission(request, obj) is True
    assert mixin.has_delete_permission(request, obj) is True
    obj.delete()


@pytest.mark.django_db
def test_has_permission_denied(fill_db):
    fixture = fill_db

    non_group = baker.make(Group)
    non_theme = baker.make(Theme, name="THEME2", group=non_group)
    measure=fixture["measure"]
    measure.theme=non_theme
    assert measure.theme.name == "THEME2"
    obj = baker.make(Filter, measure=measure)

    request = RequestFactory().get('/')
    request.user = fixture["user"]

    mixin = CheckPermissionUserMixin()
    assert mixin.has_change_permission(request, obj) is False
    assert mixin.has_delete_permission(request, obj) is False


@pytest.mark.django_db
def test_no_obj(fill_db):
    fixture = fill_db

    user = fixture["user"]

    permission = Permission.objects.get(codename='delete_filter')
    user.user_permissions.add(permission)

    request = RequestFactory().get('/')
    request.user = fixture["user"]

    admin_instance = DummyAdmin(model=Filter, admin_site=AdminSite())
    assert admin_instance.has_change_permission(request) is False
    assert admin_instance.has_delete_permission(request) is True    