from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import LeewaySimulationForm
from .tasks import run_leeway_simulation

@login_required
def simulation_form(request):
    if request.method == "POST":
        lwform = LeewaySimulationForm(
            request.POST
        )
        lwform.instance.user = request.user
        if lwform.is_valid():
            lwform.save()
            messages.add_message(request, messages.INFO,
                'Request saved. You will receive an e-mail to {} when the simulation is finished. Your request ID is {}.'.format(
                    request.user.email, lwform.instance.uuid
                )
            )
            run_leeway_simulation.apply_async([lwform.instance.uuid])

    context = {'form': LeewaySimulationForm()}
    return render(request, context=context, template_name="leeway-simulation.html")
