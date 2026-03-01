import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.crypto import get_random_string
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
    name = models.CharField(max_length=255, blank=True, verbose_name=_("Name"))
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
    geojson = models.FileField(
        null=True,
        storage=simulation_storage,
        verbose_name=_("GeoJSON of simulated trajectories"),
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
        return f"{self.name or self.uuid} {self.user.email}"

    class Meta:
        app_label = "leeway"


class InvitationToken(models.Model):
    """
    A single-use invitation token that grants access to the registration form.
    Tokens are automatically generated 32-character alphanumeric strings.
    """

    #: The token value — auto-generated, never editable
    token = models.CharField(max_length=32, unique=True, editable=False)

    #: When this token was created
    created_at = models.DateTimeField(auto_now_add=True)

    #: The user who registered with this token, or null if unused
    used_by = models.OneToOneField(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invitation_token",
        verbose_name=_("Used by"),
    )

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(32)
        super().save(*args, **kwargs)

    @property
    def is_used(self):
        """
        Whether this token has already been consumed by a registration.
        """
        return self.used_by_id is not None

    def __str__(self):
        status = "used" if self.is_used else "unused"
        return f"{self.token} ({status})"

    class Meta:
        app_label = "leeway"
