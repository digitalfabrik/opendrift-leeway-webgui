"""
URL configuration for the leeway application.
See :mod:`~opendrift_leeway_webgui.core.urls` for the other namespaces of this project.

For more information on this file, see :doc:`django:topics/http/urls`.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from . import views

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", views.simulation_form, name="home"),  # new
    path("simulations/list/", views.simulations_list, name="simulations_list"),
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
