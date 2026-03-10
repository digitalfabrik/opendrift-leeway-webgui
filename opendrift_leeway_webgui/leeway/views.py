import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from .forms import LeewaySimulationForm, RegistrationForm, WebhookForm
from .models import InvitationToken, LeewaySimulation, Webhook
from .tasks import deliver_webhook, run_leeway_simulation


class IndexRedirectView(RedirectView):
    """
    Redirect the index to the form view
    """

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

    model = LeewaySimulation
    form_class = LeewaySimulationForm
    success_url = reverse_lazy("simulation_form")

    def form_invalid(self, form):
        """
        When the form is invalid, show an error message
        """
        messages.error(self.request, ("An error occurred. Simulation could not be started."))
        return super().form_invalid(form)

    def form_valid(self, form):
        """
        When the form is valid, set the current user and save the simulation
        """
        run_leeway_simulation.apply_async([form.instance.uuid])
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

    model = LeewaySimulation
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

    form_class = RegistrationForm
    template_name = "registration/register.html"

    def _get_unused_token(self):
        """
        Return the unused :class:`~.models.InvitationToken` for the URL kwarg, or raise 404.
        """
        token = InvitationToken.objects.filter(token=self.kwargs["token"], used_by__isnull=True).first()
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


class WebhookListView(LoginRequiredMixin, ListView):
    """
    List the current user's webhooks and provide an inline form for adding new ones.
    """

    model = Webhook
    context_object_name = "webhooks"

    def get_queryset(self):
        """
        Only return webhooks belonging to the current user.
        """
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Inject a blank :class:`~.forms.WebhookForm` for the inline add form.
        """
        context = super().get_context_data(**kwargs)
        context["form"] = WebhookForm()
        return context


class WebhookCreateView(LoginRequiredMixin, CreateView):
    """
    Handle the webhook creation form POST and assign the webhook to the current user.
    """

    model = Webhook
    form_class = WebhookForm
    success_url = reverse_lazy("webhook_list")

    def form_valid(self, form):
        """
        Set the current user before saving.
        """
        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        On invalid input re-render the list page with errors.
        """
        webhooks = Webhook.objects.filter(user=self.request.user)
        return self.render_to_response(self.get_context_data(form=form, webhooks=webhooks))

    def get_template_names(self):
        return ["leeway/webhook_list.html"]


class WebhookDeleteView(LoginRequiredMixin, DeleteView):
    """
    Confirm and delete a webhook owned by the current user.
    """

    model = Webhook
    success_url = reverse_lazy("webhook_list")

    def get_queryset(self):
        """
        Scope deletions to the current user's webhooks.
        """
        return super().get_queryset().filter(user=self.request.user)


class WebhookTestView(LoginRequiredMixin, View):
    """
    Queue a test webhook delivery for the given webhook using the all-zeroes UUID.
    """

    TEST_UUID = "00000000-0000-0000-0000-000000000000"

    def post(self, request, pk):
        """
        Dispatch a test delivery task and redirect back to the webhook list.
        """
        webhook = Webhook.objects.filter(pk=pk, user=request.user).first()
        if webhook is None:
            raise Http404
        deliver_webhook.apply_async([webhook.pk, self.TEST_UUID])
        messages.success(request, f"Test delivery queued for {webhook.url}.")
        return redirect("webhook_list")


class SimulationFileView(LoginRequiredMixin, View):
    """
    Serve simulation output files (PNG, NetCDF) with login and ownership protection.

    The filename stem must match the UUID of an existing simulation owned by the
    requesting user. Any other request is rejected with 403 or 404.
    """

    ALLOWED_EXTENSIONS = {".png", ".nc", ".geojson"}

    def get(self, request, path):
        """
        Serve the requested simulation file if the user owns it.
        """
        if "\x00" in path:
            raise Http404

        if Path(path).name != path:
            raise Http404

        if Path(path).suffix not in self.ALLOWED_EXTENSIONS:
            raise Http404

        base_dir = Path(settings.SIMULATION_OUTPUT).resolve()
        file_path = (base_dir / path).resolve()

        try:
            file_path.relative_to(base_dir)
        except ValueError as exc:
            raise Http404 from exc

        if not file_path.is_file():
            raise Http404

        uuid_str = file_path.stem
        try:
            simulation = LeewaySimulation.objects.get(uuid=uuid_str)
        except (LeewaySimulation.DoesNotExist, ValueError) as exc:
            raise Http404 from exc

        if simulation.user != request.user:
            return HttpResponseForbidden("You do not have permission to access this file.")

        content_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(
            file_path.open("rb"),
            content_type=content_type or "application/octet-stream",
        )
