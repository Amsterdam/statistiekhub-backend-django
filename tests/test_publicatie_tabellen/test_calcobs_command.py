from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.management import call_command


class TestCalcObsCommand:
    @pytest.mark.django_db
    def test_calc_obs_failure(self, caplog):
        """
        Check the flow when an error is raised
        """

        with patch('publicatie_tabellen.publication_main.PublishFunction.fill_observationcalculated', side_effect=Exception("Failure message")):
            try:
                call_command("calcobs")
            except Exception as e:
                assert "Failure message" in str(e)
