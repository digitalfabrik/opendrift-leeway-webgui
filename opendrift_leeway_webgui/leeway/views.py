from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import LeewaySimulation
from .forms import LeewaySimulationForm
from .tasks import run_leeway_simulation

@login_required
def simulation_form(request):
    """
    Form to start new simulation
    """
    if request.method == "POST":
        lwform = LeewaySimulationForm(
            request.POST
        )
        lwform.instance.user = request.user
        if lwform.is_valid():
            lwform.save()
            messages.add_message(
                request,
                messages.INFO,
                ('Request saved. You will receive an e-mail to {} when the simulation is finished. '
                 'Your request ID is {}.').format(
                     request.user.email, lwform.instance.uuid
                 )
            )
            run_leeway_simulation.apply_async([lwform.instance.uuid])

    context = {'form': LeewaySimulationForm()}
    return render(request, context=context, template_name="simulation-form.html")

@login_required
def simulations_list(request):
    """
    List all existing simulations of a user
    """
    return render(
        request,
        context={
            "SIMULATION_URL": settings.SIMULATION_URL,
            "simulations": LeewaySimulation.objects.filter(user=request.user),
        },
        template_name="simulations-list.html"
    )
