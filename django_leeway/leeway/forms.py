from django.forms import ModelForm
from leeway.models import LeewaySimulation

class LeewaySimulationForm(ModelForm):
    class Meta:
        model = LeewaySimulation
        fields = ['longitude', 'latitude', 'object_type', 'start_time', 'duration']
