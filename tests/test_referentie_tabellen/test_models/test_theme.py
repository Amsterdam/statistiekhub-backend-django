import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from referentie_tabellen.models import Theme


@pytest.mark.django_db
class TestThemeGroupRequired:
    @pytest.fixture
    def groups(self):
        return [
            Group.objects.get_or_create(name="group_1"),
            Group.objects.get_or_create(name="group_2"),
            Group.objects.get_or_create(name="group_3"),
            Group.objects.get_or_create(name="modifier_not_allowed"),
            Group.objects.get_or_create(name="maintainer_not_allowed"),
            Group.objects.get_or_create(name="maintainers"),
        ]

    @pytest.mark.parametrize(
        "group_name",
        [
            "group_1",
            "group_2",
            "group_3",
        ],
    )
    def test_group_valid_group(self, group_name, groups):
        group = Group.objects.get(name=group_name)
        theme = baker.make(Theme, group=group)

        theme.full_clean()
        theme.save()

        assert theme.group.id == group.id

    @pytest.mark.parametrize(
        "group_name",
        [
            "modifier_not_allowed",
            "maintainer_not_allowed",
            "maintainers",
        ],
    )
    def test_group_invalid_group_prefix(self, group_name, groups):
        group = Group.objects.get(name=group_name)

        with pytest.raises(ValidationError) as exc_info:
            baker.make(Theme, group=group)

        assert "group" in exc_info.value.message_dict

    def test_group_cannot_none(self):
        with pytest.raises(ValidationError) as exc_info:
            baker.make(Theme, group=None)

        assert "group" in exc_info.value.message_dict
        assert exc_info.value.message_dict["group"][0] == "This field cannot be null."

    @pytest.mark.parametrize(
        "valid_name,invalid_name",
        [
            ("group_1", "modifier_not_allowed"),
            ("group_2", "maintainer_not_allowed"),
            ("group_3", "maintainers"),
        ],
    )
    def test_group_update_validation(self, valid_name, invalid_name, groups):
        valid_group = Group.objects.get(name=valid_name)
        invalid_group = Group.objects.get(name=invalid_name)

        theme = baker.make(Theme, group=valid_group)

        theme.full_clean()
        theme.save()

        theme.group = invalid_group
        with pytest.raises(ValidationError) as exc_info:
            theme.full_clean()

        assert "group" in exc_info.value.message_dict
