"""
URL patterns for the first version of the Opendrift Leeway Webgui API
"""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "v1"

#: Router for dynamic url patterns
router = DefaultRouter()
router.register("simulations", views.LeewaySimulationViewSet, "simulations")

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("knox.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api:v1:schema"),
        name="swagger-ui",
    ),
]
