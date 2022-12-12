from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic.base import TemplateView

from . import views

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
