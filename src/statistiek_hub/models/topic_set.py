from django.db import models

from .measure import Measure
from .topic import Topic


class TopicSet(models.Model):
    id = models.BigAutoField(primary_key=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.topic}:{self.measure}"

    class Meta:
        managed = True
        db_table = "topicset"
        unique_together = [["topic", "measure"]]
