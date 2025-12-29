import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
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


class LeewaySimulationDocumentation(TemplateView):
    """
    Display end user documentation for using the tool
    """

    template_name = "leeway/leewaysimulation_documentation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["SERVER_EMAIL"] = settings.SERVER_EMAIL
        return context


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


class LeewaySimulationDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for rendering the simulation details
    """

    model = LeewaySimulation
    success_url = reverse_lazy("simulation_list")

    def get(self, request, *args, **kwargs):
        if self.get_object().user == request.user:
            self.get_object().delete()
            return HttpResponseRedirect("/simulations")
        return HttpResponseForbidden("Cannot delete other's simulations")


class SimulationFileView(LoginRequiredMixin, View):
    """
    Serve simulation output files (PNG, NetCDF) with login and ownership protection.

    The filename stem must match the UUID of an existing simulation owned by the
    requesting user. Any other request is rejected with 403 or 404.
    """

    def get(self, request, path):
        """
        Serve the requested simulation file if the user owns it.
        """
        file_path = Path(settings.SIMULATION_OUTPUT) / path

        # Only allow a flat filename — no directory traversal
        if Path(path).parent != Path("."):
            raise Http404

        if not file_path.is_file():
            raise Http404

        # Extract UUID from filename stem and verify ownership
        uuid_str = file_path.stem
        try:
            simulation = LeewaySimulation.objects.get(uuid=uuid_str)
        except (LeewaySimulation.DoesNotExist, ValueError):
            raise Http404

        if simulation.user != request.user:
            return HttpResponseForbidden("You do not have permission to access this file.")

        content_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(file_path.open("rb"), content_type=content_type or "application/octet-stream")
