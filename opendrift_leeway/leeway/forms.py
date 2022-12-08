from django.forms import ModelForm, CharField
from dms2dec.dms_convert import dms2dec

from .models import LeewaySimulation


class LeewaySimulationForm(ModelForm):
    """
    Add a form for simulations with some tweaks of the default.
    """
    def __init__(self, *args, **kwargs):
        """
        Use CharField for latitude and longitude to allow DMS input
        """
        super().__init__(*args, **kwargs)
        self.fields['longitude'] = CharField(
            help_text='Input in decimal and degrees minutes seconds supported.')
        self.fields['latitude'] = CharField(
            help_text='Input in decimal and degrees minutes seconds supported.')

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Configure form fields and help text.
        """
        model = LeewaySimulation
        fields = ['longitude', 'latitude', 'object_type', 'start_time', 'duration', 'radius']

        help_texts = {
            'duration': 'Length of simulation in hours.',
            'radius': ('Radius for distributing drifting particles around '
                       'the start coordinates in meters.')
        }

    def clean_longitude(self):
        """
        Convert longitude DMS to decimal
        """
        data = self.cleaned_data.get('longitude', '')
        if "°" in data:
            return dms2dec(data)
        return data

    def clean_latitude(self):
        """
        Convert latitude DMS to decimal
        """
        data = self.cleaned_data.get('latitude', '')
        if "°" in data:
            return dms2dec(data)
        return data
