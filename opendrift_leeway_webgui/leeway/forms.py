"""
Forms for the web GUI
"""
from django.forms import CharField, ModelForm, TextInput

from .models import LeewaySimulation
from .utils import normalize_dms2dec


class LeewaySimulationForm(ModelForm):
    """
    Add a form for simulations with some tweaks of the default.
    """

    # Override coordinates fields to allow text input instead of float numbers
    longitude = CharField(
        help_text="(E/W) Input in decimal and degrees minutes seconds supported.",
        widget=TextInput(attrs={"placeholder": "12° 26' 42.684\""}),
    )
    latitude = CharField(
        help_text="(N/S) Input in decimal and degrees minutes seconds supported.",
        widget=TextInput(attrs={"placeholder": "34° 47' 49.1166\""}),
    )

    class Meta:
        """
        Configure form fields and help text.
        """

        model = LeewaySimulation
        fields = [
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
            "start_time": "All times are UTC. Only simulations +/- 4 days from now are possible.",
        }

    def clean_longitude(self):
        """
        Convert longitude DMS to decimal
        """
        return normalize_dms2dec(self.cleaned_data.get("longitude", ""))

    def clean_latitude(self):
        """
        Convert latitude DMS to decimal
        """
        return normalize_dms2dec(self.cleaned_data.get("latitude", ""))
