from drf_spectacular.utils import extend_schema, inline_serializer
from knox.views import LoginView as KnoxLoginView
from rest_framework import mixins, serializers, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .serializers import LeewaySimulationSerializer


class LoginView(KnoxLoginView):
    """
    Obtain an API token with username and password via HTTP Basic authentication
    """

    #: Allow obtaining a token with username and password or an existing session
    authentication_classes = (BasicAuthentication, SessionAuthentication)

    @extend_schema(
        summary="Obtain an API token",
        description=(
            "Authenticate with your username and password via HTTP Basic "
            "authentication (header `Authorization: Basic <base64(username:password)>`) "
            "to obtain a new API token. No request body is required.\n\n"
            "Use the returned token in subsequent requests with the header "
            "`Authorization: Token <token>`.\n\n"
            "Example: `curl -X POST -u username:password "
            "https://leeway.tuerantuer.org/api/v1/auth/login/`"
        ),
        request=None,
        responses=inline_serializer(
            name="LoginResponse",
            fields={
                "expiry": serializers.DateTimeField(allow_null=True),
                "token": serializers.CharField(),
            },
        ),
        tags=["auth"],
    )
    def post(self, request, format=None):  # pylint: disable=redefined-builtin
        return super().post(request, format=format)


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
