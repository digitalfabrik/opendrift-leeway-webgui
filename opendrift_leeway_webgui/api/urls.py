"""
URL patterns for the Opendrift Leeway Webgui API
"""

from django.urls import include, path

#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "api"

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("", include("opendrift_leeway_webgui.api.v1.urls", namespace="default")),
    path("v1/", include("opendrift_leeway_webgui.api.v1.urls", namespace="v1")),
]
