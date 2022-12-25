from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import LeewaySimulationForm
from .models import LeewaySimulation
from .tasks import run_leeway_simulation


class IndexRedirectView(RedirectView):
    """
    Redirect the index to the form view
    """

    #: The name of the URL pattern to redirect to
    pattern_name = settings.LOGIN_REDIRECT_URL


class LeewaySimulationCreateView(LoginRequiredMixin, CreateView):
    """
    The view for rendering and submitting the simulation form
    """

    #: The model for this form view
    model = LeewaySimulation

    #: The form class which should be used
    form_class = LeewaySimulationForm

    #: The URL to redirect to after successful form submission
    success_url = reverse_lazy("simulation_form")

    def form_invalid(self, form):
        """
        When the form is invalid, show an error message
        """
        messages.error(
            self.request, ("An error occurred. Simulation could not be started.")
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        """
        When the form is valid, set the current user and save the simulation
        """
        # Start leeway simulation in background
        run_leeway_simulation.apply_async([form.instance.uuid])
        # Set the current user because it's not handled by the form fields
        form.instance.user = self.request.user
        messages.success(
            self.request,
            (
                f"Request saved. You will receive an e-mail to {self.request.user.email} when "
                f"the simulation is finished.\nYour request ID is {form.instance.uuid}."
            ),
        )
        return super().form_valid(form)


# pylint: disable=too-many-ancestors
class LeewaySimulationListView(LoginRequiredMixin, ListView):
    """
    View for rendering the simulations list
    """

    #: The model for this list view
    model = LeewaySimulation

    #: The name of the template context variable
    context_object_name = "simulations"

    def get_queryset(self):
        """
        Only return simulations of the current user
        """
        return super().get_queryset().filter(user=self.request.user)


class LeewaySimulationDetailView(LoginRequiredMixin, DetailView):
    """
    View for rendering the simulation details
    """

    #: The model for this detail view
    model = LeewaySimulation
