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

    #: Expose the model's error property (last line of traceback)
    error = serializers.ReadOnlyField()

    #: True once simulation_finished is set
    completed = serializers.SerializerMethodField()

    def get_completed(self, obj):
        """
        :param obj: The simulation instance
        :type obj: ~opendrift_leeway_webgui.leeway.models.LeewaySimulation
        :rtype: bool
        """
        return obj.simulation_finished is not None

    class Meta:
        """
        Define model and the corresponding fields
        """

        #: The model class for this serializer
        model = LeewaySimulation

        #: Exclude user field because the username is shown instead
        exclude = ["user"]

        #: Set example values for drf-spectacular Swagger documentation
        extra_kwargs = {
            "duration": {"default": 12, "help_text": "Length of simulation in hours."},
            "radius": {
                "default": 1000,
                "help_text": "Radius in meters for distributing particles around start coordinates.",
            },
        }

        #: Define fields which are shown when retrieving simulations,
        #: but cannot be set when creating new ones
        read_only_fields = [
            "uuid",
            "img",
            "netcdf",
            "geojson",
            "traceback",
            "simulation_started",
            "simulation_finished",
            "error",
            "completed",
        ]

    def create(self, validated_data):
        simulation = LeewaySimulation.objects.create(**validated_data)
        run_leeway_simulation.apply_async([simulation.uuid])
        return simulation
