from django.db import models

from .measure import Measure
from .topic import Topic


class TopicSet(models.Model):
    class Meta:
        unique_together = [["topic", "measure"]]

    id = models.BigAutoField(primary_key=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.topic}:{self.measure}"
