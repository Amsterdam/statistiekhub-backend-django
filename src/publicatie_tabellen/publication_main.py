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

    @classmethod
    def run_all_publish_tables(cls):
        """runs all three publish tables"""

        instance = cls()

        measure_message, measure_succes = publishmeasure()
        if not measure_succes:
            raise Exception(f"Error op publishmeasure: {measure_message}")
        logger.info("publishmeasure table succesfull")

        try:
            instance.fill_observationcalculated()
        except Exception as e:
            raise Exception(f"Error op obs calculated table: {e}")
        logger.info("publishobservationcalculated table succesfull")

        obs_message, obs_succes = publishobservation()
        if not obs_succes:
            raise Exception(f"Error op publishobservations: {obs_message}")
        logger.info("publishobservation table succesfull")

        statistic_message, statistic_succes = publishstatistic()
        if not statistic_succes:
            raise Exception(f"Error op publishstatistic: {statistic_message}")
        logger.info("publishstatistic table succesfull")

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
