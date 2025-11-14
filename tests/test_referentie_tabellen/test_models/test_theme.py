import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from referentie_tabellen.models import Theme


@pytest.mark.django_db
class TestThemeGroupPrefix:
    @pytest.fixture
    def groups(self):
        return [
            Group.objects.get_or_create(name="theme_group_1"),
            Group.objects.get_or_create(name="theme_group_2"),
            Group.objects.get_or_create(name="theme_group_3"),
            Group.objects.get_or_create(name="group_4"),
            Group.objects.get_or_create(name="group_5"),
            Group.objects.get_or_create(name="wrong_prefix_group_6"),
        ]

    @pytest.mark.parametrize(
        "group_name",
        [
            "theme_group_1",
            "theme_group_2",
            "theme_group_3",
        ],
    )
    def test_group_valid_group_prefix(self, group_name, groups):
        group = Group.objects.get(name=group_name)

        theme = baker.make(Theme, group=None)
        theme.group = group

        theme.full_clean()
        theme.save()

        assert theme.group == group
        assert theme.group.name.startswith(Theme.group_prefix)

    @pytest.mark.parametrize(
        "group_name",
        [
            "group_4",
            "group_5",
            "wrong_prefix_group_6",
        ],
    )
    def test_group_invalid_group_prefix(self, group_name, groups):
        group = Group.objects.get(name=group_name)

        theme = baker.make(Theme, group=None)
        theme.group = group

        with pytest.raises(ValidationError) as exc_info:
            theme.full_clean()

        assert "group" in exc_info.value.message_dict
        assert not group.name.startswith(Theme.group_prefix)

    def test_group_null_group(self):
        theme = baker.make(Theme, group=None)

        theme.full_clean()
        theme.save()

        assert theme.group is None

    def test_group_blank_group(self):
        theme = baker.make(Theme)

        theme.full_clean()
        theme.save()

        assert theme.group is None

    @pytest.mark.parametrize(
        "valid_name,invalid_name",
        [
            ("theme_group_1", "group_4"),
            ("theme_group_2", "group_5"),
            ("theme_group_3", "wrong_prefix_group_6"),
        ],
    )
    def test_group_group_update_validation(self, valid_name, invalid_name, groups):
        valid_group = Group.objects.get(name=valid_name)
        invalid_group = Group.objects.get(name=invalid_name)

        theme = baker.make(Theme, group=None)

        theme.group = valid_group
        theme.full_clean()
        theme.save()

        theme.group = invalid_group
        with pytest.raises(ValidationError) as exc_info:
            theme.full_clean()

        assert "group" in exc_info.value.message_dict
