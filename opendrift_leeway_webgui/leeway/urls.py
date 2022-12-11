from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('', views.simulation_form, name='home'), # new
    path('simulations/list/', views.simulations_list, name='simulations_list')
]
