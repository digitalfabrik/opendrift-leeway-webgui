import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils import LEEWAY_OBJECT_TYPES


def simulation_storage():
    """
    Callable to get the simulation storage
    """
    return FileSystemStorage(
        location=settings.SIMULATION_OUTPUT, base_url=settings.SIMULATION_URL
    )


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
    img = models.FileField(
        null=True, storage=simulation_storage, verbose_name=_("Image file")
    )
    netcdf = models.FileField(
        null=True, storage=simulation_storage, verbose_name=_("NetCDF file")
    )
    traceback = models.TextField(blank=True, verbose_name=_("traceback"))

    @property
    def error(self):
        """
        The last line of the traceback, usually the error message.
        """
        return self.traceback.splitlines()[-1] if self.traceback else None

    def __str__(self):
        # pylint: disable=no-member
        return f"{self.uuid} {self.user.email}"

    class Meta:
        app_label = "leeway"
