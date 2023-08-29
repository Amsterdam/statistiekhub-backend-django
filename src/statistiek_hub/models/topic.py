from django.db import models


class Topic(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "topic"
