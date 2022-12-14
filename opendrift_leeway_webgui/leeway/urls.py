"""
URL configuration for the leeway application.
See :mod:`~opendrift_leeway_webgui.core.urls` for the other namespaces of this project.

For more information on this file, see :doc:`django:topics/http/urls`.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic.detail import DetailView

from . import views
from .models import LeewaySimulation

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", views.simulation_form, name="home"),  # new
    path(
        "list/",
        include(
            [
                path("", views.simulations_list, name="simulations_list"),
                path(
                    "<pk>",
                    login_required(DetailView.as_view(model=LeewaySimulation)),
                    name="simulation_error",
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
