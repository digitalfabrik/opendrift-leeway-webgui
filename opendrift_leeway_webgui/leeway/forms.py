"""
Forms for the web GUI
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import (
    ChoiceField,
    DecimalField,
    FloatField,
    ModelForm,
    Select,
    TextInput,
)

from .models import LeewaySimulation, Webhook


def _assemble_decimal(deg, minutes, sec):
    """
    Assemble a decimal degree value from components.

    If *deg* has a fractional part, *minutes* and *sec* are ignored.
    If *minutes* has a fractional part, *sec* is ignored.

    :param deg: Absolute degrees (non-negative Decimal)
    :type deg: ~decimal.Decimal
    :param minutes: Minutes component (Decimal)
    :type minutes: ~decimal.Decimal
    :param sec: Seconds component (Decimal)
    :type sec: ~decimal.Decimal
    :rtype: ~decimal.Decimal
    """
    if deg % 1 != 0:
        return deg
    if minutes % 1 != 0:
        return deg + minutes / 60
    return deg + minutes / 60 + sec / 3600


class LeewaySimulationForm(ModelForm):
    """
    Add a form for simulations with some tweaks of the default.

    Latitude and longitude are each split into four sub-fields
    (degrees, minutes, seconds, direction) and assembled into a single
    decimal value in the ``clean_latitude`` / ``clean_longitude`` methods.
    """

    #: Direction choices for latitude
    LAT_DIR_CHOICES = [("N", "N"), ("S", "S")]
    #: Direction choices for longitude
    LON_DIR_CHOICES = [("E", "E"), ("W", "W")]

    # --- Latitude sub-fields ---
    latitude_deg = DecimalField(
        label="Latitude",
        min_value=Decimal("0"),
        max_value=Decimal("90"),
        widget=TextInput(attrs={"placeholder": "34", "class": "coord-deg coord-lat"}),
    )
    latitude_min = DecimalField(
        label="",
        required=False,
        min_value=Decimal("0"),
        max_value=Decimal("59.9999999"),
        initial=Decimal("0"),
        widget=TextInput(attrs={"placeholder": "47", "class": "coord-min coord-lat"}),
    )
    latitude_sec = DecimalField(
        label="",
        required=False,
        min_value=Decimal("0"),
        max_value=Decimal("59.9999999"),
        initial=Decimal("0"),
        widget=TextInput(attrs={"placeholder": "49.1", "class": "coord-sec coord-lat"}),
    )
    latitude_dir = ChoiceField(
        label="",
        choices=LAT_DIR_CHOICES,
        widget=Select(attrs={"class": "coord-dir coord-lat"}),
    )

    # --- Longitude sub-fields ---
    longitude_deg = DecimalField(
        label="Longitude",
        min_value=Decimal("0"),
        max_value=Decimal("180"),
        widget=TextInput(attrs={"placeholder": "12", "class": "coord-deg coord-lon"}),
    )
    longitude_min = DecimalField(
        label="",
        required=False,
        min_value=Decimal("0"),
        max_value=Decimal("59.9999999"),
        initial=Decimal("0"),
        widget=TextInput(attrs={"placeholder": "26", "class": "coord-min coord-lon"}),
    )
    longitude_sec = DecimalField(
        label="",
        required=False,
        min_value=Decimal("0"),
        max_value=Decimal("59.9999999"),
        initial=Decimal("0"),
        widget=TextInput(attrs={"placeholder": "42.7", "class": "coord-sec coord-lon"}),
    )
    longitude_dir = ChoiceField(
        label="",
        choices=LON_DIR_CHOICES,
        widget=Select(attrs={"class": "coord-dir coord-lon"}),
    )

    # Declared after all sub-fields so that clean_latitude / clean_longitude
    # run after the sub-fields are already present in cleaned_data.
    # required=False avoids a duplicate "This field is required." message when
    # a sub-field already reported an error and clean_* returns None.
    latitude = FloatField(required=False)
    longitude = FloatField(required=False)

    class Meta:
        """
        Configure form fields and help text.
        """

        model = LeewaySimulation
        fields = [
            "name",
            "latitude",
            "longitude",
            "object_type",
            "start_time",
            "duration",
            "radius",
        ]
        help_texts = {
            "duration": "Length of simulation in hours.",
            "radius": (
                "Radius for distributing drifting particles around "
                "the start coordinates in meters."
            ),
            "start_time": "All times are UTC. Only simulations +/- 5 days from now are possible.",
        }

    def _clean_coordinate(self, prefix, max_deg):
        """
        Assemble and validate a coordinate from its sub-fields.

        :param prefix: Field name prefix, either ``"latitude"`` or ``"longitude"``
        :type prefix: str
        :param max_deg: Maximum allowed absolute degree value (90 or 180)
        :type max_deg: int
        :rtype: float
        """
        data = self.cleaned_data
        deg = data.get(f"{prefix}_deg")
        minutes = data.get(f"{prefix}_min") or Decimal("0")
        sec = data.get(f"{prefix}_sec") or Decimal("0")
        direction = data.get(f"{prefix}_dir", "N")

        if deg is None:
            # deg field validation already raised an error; avoid a duplicate message
            return None

        decimal_value = _assemble_decimal(deg, minutes, sec)

        if decimal_value > max_deg:
            raise ValidationError(
                f"Value {decimal_value} exceeds the maximum of {max_deg}°."
            )

        if direction in ("S", "W"):
            decimal_value = -decimal_value

        return float(decimal_value)

    def clean(self):
        """
        Assemble latitude and longitude decimals from their sub-fields.

        Runs after all individual field validations, so all sub-field values
        are guaranteed to be present in ``cleaned_data``.
        """
        cleaned = super().clean()
        cleaned["latitude"] = self._clean_coordinate("latitude", 90)
        cleaned["longitude"] = self._clean_coordinate("longitude", 180)
        return cleaned


class WebhookForm(ModelForm):
    """
    Form for creating a new webhook.
    """

    class Meta:
        """
        Configure form fields.
        """

        model = Webhook
        fields = ["url"]


# pylint: disable=too-many-ancestors
class RegistrationForm(UserCreationForm):
    """
    Registration form for new users arriving via an invitation token link.
    Collects username, first name, last name, email address, and password.
    """

    class Meta:
        """
        Configure form fields.
        """

        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]
