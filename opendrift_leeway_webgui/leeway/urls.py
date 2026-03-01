"""
URL configuration for the leeway application.
See :mod:`~opendrift_leeway_webgui.core.urls` for the other namespaces of this project.

For more information on this file, see :doc:`django:topics/http/urls`.
"""

from django.urls import include, path

from .views import (
    IndexRedirectView,
    LeewaySimulationCreateView,
    LeewaySimulationDeleteView,
    LeewaySimulationDetailView,
    LeewaySimulationDocumentation,
    LeewaySimulationListView,
    RegistrationView,
    SimulationFileView,
    WebhookCreateView,
    WebhookDeleteView,
    WebhookListView,
    WebhookTestView,
)

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", IndexRedirectView.as_view(), name="index"),
    path(
        "documentation/",
        LeewaySimulationDocumentation.as_view(),
        name="simulation_documentation",
    ),
    path(
        "simulations/",
        include(
            [
                path("", LeewaySimulationListView.as_view(), name="simulation_list"),
                path(
                    "new/", LeewaySimulationCreateView.as_view(), name="simulation_form"
                ),
                path(
                    "<pk>/",
                    LeewaySimulationDetailView.as_view(),
                    name="simulation_detail",
                ),
                path(
                    "<pk>/delete/",
                    LeewaySimulationDeleteView.as_view(),
                    name="simulation_delete",
                ),
            ]
        ),
    ),
]

urlpatterns += [
    path(
        "simulation-files/<path:path>",
        SimulationFileView.as_view(),
        name="simulation_file",
    ),
    path("accounts/register/<str:token>/", RegistrationView.as_view(), name="register"),
    path(
        "webhooks/",
        include(
            [
                path("", WebhookListView.as_view(), name="webhook_list"),
                path("add/", WebhookCreateView.as_view(), name="webhook_create"),
                path(
                    "<pk>/delete/", WebhookDeleteView.as_view(), name="webhook_delete"
                ),
                path("<pk>/test/", WebhookTestView.as_view(), name="webhook_test"),
            ]
        ),
    ),
]
