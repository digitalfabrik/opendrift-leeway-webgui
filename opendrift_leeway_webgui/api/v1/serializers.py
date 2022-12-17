from rest_framework import serializers

from ...leeway.models import LeewaySimulation


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
