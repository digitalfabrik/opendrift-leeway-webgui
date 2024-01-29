"""
URL configuration for the leeway application.
See :mod:`~opendrift_leeway_webgui.core.urls` for the other namespaces of this project.

For more information on this file, see :doc:`django:topics/http/urls`.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from .views import (
    IndexRedirectView,
    LeewaySimulationCreateView,
    LeewaySimulationDeleteView,
    LeewaySimulationDetailView,
    LeewaySimulationDocumentation,
    LeewaySimulationListView,
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

# Serve simulation files in debug mode
if settings.DEBUG:
    urlpatterns += [
        path(
            "",
            include(
                (
                    static(
                        settings.SIMULATION_URL,
                        document_root=settings.SIMULATION_OUTPUT,
                    ),
                    "simulation_files",
                )
            ),
        )
    ]
