from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .serializers import LeewaySimulationSerializer


# pylint: disable=too-many-ancestors
class LeewaySimulationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for simulations of the authenticated user, with the option to

    - Create new simulations
    - List all existing simulations
    - Retrieve a single simulation record
    """

    #: Only enable this viewset for authenticated users
    permission_classes = (IsAuthenticated,)

    #: The serializer to use for simulations
    serializer_class = LeewaySimulationSerializer

    #: Use UUID as the lookup field instead of the integer primary key
    lookup_field = "uuid"

    def get_queryset(self):
        """
        Only return the simulations of the current user
        """
        return self.request.user.leewaysimulation_set.all()

    def perform_create(self, serializer):
        """
        Automatically set the user field on creation
        """
        serializer.save(user=self.request.user)
