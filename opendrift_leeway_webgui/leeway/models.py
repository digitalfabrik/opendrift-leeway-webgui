import uuid
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import models

from .utils import LEEWAY_OBJECT_TYPES


# Create your models here.
class LeewaySimulation(models.Model):
    """
    Required information for simulation run
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    longitude = models.FloatField()
    latitude = models.FloatField()
    start_time = models.DateTimeField(default=datetime.now)
    duration = models.IntegerField(default=12)
    object_type = models.IntegerField(choices=LEEWAY_OBJECT_TYPES, default=27)
    simulation_started = models.DateTimeField(null=True)
    simulation_finished = models.DateTimeField(null=True)
    radius = models.IntegerField(default=1000)

    def __str__(self):
        # pylint: disable=no-member
        return f"{self.uuid} {self.user.email}"

    class Meta:
        app_label = "leeway"
