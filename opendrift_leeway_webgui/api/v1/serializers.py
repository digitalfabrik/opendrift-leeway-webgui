from rest_framework import serializers

from ...leeway.models import LeewaySimulation
from ...leeway.tasks import run_leeway_simulation


class LeewaySimulationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Leeway Simulations. Inherits from
    `serializers.ModelSerializer`.
    """

    #: Show username instead of id
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        """
        Define model and the corresponding fields
        """

        #: The model class for this serializer
        model = LeewaySimulation

        #: Exclude user field because the username is shown instead
        exclude = ["user"]

        #: Define fields which are shown when retrieving simulations,
        #: but cannot be set when creating new ones
        read_only_fields = [
            "uuid",
            "img",
            "netcdf",
            "traceback",
            "simulation_started",
            "simulation_finished",
        ]

    def create(self, validated_data):
        simulation = LeewaySimulation.objects.create(**validated_data)
        run_leeway_simulation.apply_async([simulation.uuid])
        return simulation
