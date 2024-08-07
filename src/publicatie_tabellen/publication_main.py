import logging

from django.db import connection

from publicatie_tabellen.publish_measure import publishmeasure
from publicatie_tabellen.publish_observation import publishobservation
from publicatie_tabellen.publish_statistic import publishstatistic
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import ObservationCalculated
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


class PublishFunction:
    def __init__(self, model=None) -> None:
        self.model = model
        self.result = None

        self.publish_function()

    def publish_function(self):
        """runs the correct model-function for publication"""
        if self.model:

            match self.model._meta.model_name:
                case "publicationmeasure":
                    self.result = publishmeasure()

                case "publicationstatistic":
                    self.fill_observationcalculated()
                    self.result = publishstatistic()

                case "publicationobservation":
                    self.fill_observationcalculated()
                    self.result = publishobservation()

    def fill_observationcalculated(self):
        """fill model ObservationCalculated with observations calculated by the calculation-query of the measure"""
        # get calculation measures -> select from observations otherwise they can not exist
        qsmeasurecalc = Measure.objects.exclude(calculation="")
        logger.info(f"Number measures calculated : {len(qsmeasurecalc)}")

        truncate(ObservationCalculated)
        for measure in qsmeasurecalc:
            raw_query = f"select (public.calculate_observation ({measure.id}, '{measure.calculation}')).*"

            with connection.cursor() as cursor:
                cursor.execute(raw_query)
                measure_calcobs = cursor.fetchall()

            def _transform_results(results: list) -> list:
                """Transform the query results into
                list of ObservationCalculated objects
                results: list of tuples returned from query"""

                new_item_list = []
                for row in results:
                    new_item_list.append(
                        ObservationCalculated(
                            measure_id=row[4],
                            value=row[3],
                            spatialdimension_id=row[5],
                            temporaldimension_id=row[6],
                        )
                    )
                return new_item_list

            ObservationCalculated.objects.bulk_create(
                _transform_results(measure_calcobs)
            )
        logger.info("records for calculated observations are calculated")
