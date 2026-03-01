import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from .forms import LeewaySimulationForm, RegistrationForm
from .models import InvitationToken, LeewaySimulation
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

    def get_queryset(self):
        """
        Only return simulations of the current user to prevent deleting other users' simulations
        """
        return super().get_queryset().filter(user=self.request.user)


class RegistrationView(CreateView):
    """
    Public registration form for new users arriving via an invitation token link.

    The token is embedded in the URL. If it does not exist or has already been
    used, a 404 is raised. On successful registration the token is consumed and
    the new user is logged in automatically.
    """

    #: The form class for user creation
    form_class = RegistrationForm

    #: Template rendered for GET and invalid POST
    template_name = "registration/register.html"

    def _get_unused_token(self):
        """
        Return the unused :class:`~.models.InvitationToken` for the URL kwarg, or raise 404.
        """
        token = InvitationToken.objects.filter(
            token=self.kwargs["token"], used_by__isnull=True
        ).first()
        if token is None:
            raise Http404
        return token

    def get(self, request, *args, **kwargs):
        """
        Render the registration form, or 404 if the token is invalid/used.
        """
        self._get_unused_token()
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Save the new user, consume the token, and log the user in.
        """
        invitation = self._get_unused_token()
        user = form.save()
        invitation.used_by = user
        invitation.save()
        auth.login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirect to the simulation form after successful registration.
        """
        return reverse_lazy("simulation_form")


class SimulationFileView(LoginRequiredMixin, View):
    """
    Serve simulation output files (PNG, NetCDF) with login and ownership protection.

    The filename stem must match the UUID of an existing simulation owned by the
    requesting user. Any other request is rejected with 403 or 404.
    """

    #: Only these extensions are ever written by the simulation task
    ALLOWED_EXTENSIONS = {".png", ".nc", ".geojson"}

    def get(self, request, path):
        """
        Serve the requested simulation file if the user owns it.
        """
        # Reject null bytes
        if "\x00" in path:
            raise Http404

        # Reject anything that is not a bare filename (no directory component)
        if Path(path).name != path:
            raise Http404

        # Reject disallowed extensions
        if Path(path).suffix not in self.ALLOWED_EXTENSIONS:
            raise Http404

        base_dir = Path(settings.SIMULATION_OUTPUT).resolve()
        file_path = (base_dir / path).resolve()

        # Defence in depth: ensure the resolved path is still inside base_dir
        # (catches symlink escapes and any edge cases not caught above)
        try:
            file_path.relative_to(base_dir)
        except ValueError as exc:
            raise Http404 from exc

        if not file_path.is_file():
            raise Http404

        # Extract UUID from filename stem and verify ownership
        uuid_str = file_path.stem
        try:
            simulation = LeewaySimulation.objects.get(uuid=uuid_str)
        except (LeewaySimulation.DoesNotExist, ValueError) as exc:
            raise Http404 from exc

        if simulation.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this file."
            )

        content_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(
            file_path.open("rb"),
            content_type=content_type or "application/octet-stream",
        )
