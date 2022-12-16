import re
from datetime import datetime

import pytest
from django.core import mail
from django.urls import reverse

from opendrift_leeway_webgui.leeway.models import LeewaySimulation


# pylint: disable=unused-argument
@pytest.mark.django_db(transaction=True)
def test_simulation(admin_client, settings, celery_app, celery_worker):
    """
    Test whether simulation works as expected
    """
    # Send emails to console
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    # Submit form
    form = reverse("simulation_form")
    response = admin_client.post(
        form,
        data={
            "latitude": "33°58'44.3\"",
            "longitude": "11°21'13.4\"",
            "object_type": 27,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": 12,
            "radius": 1000,
        },
    )
    # On success, the user is redirected to the form again
    assert response.status_code == 302
    assert response.headers.get("Location") == form
    # Follow the redirect to receive the message
    response = admin_client.get(form)
    assert (
        "Request saved. You will receive an e-mail to admin@example.com when the simulation is finished."
        in response.content.decode("utf-8")
    )
    # Get the UUID of the simulation
    match = re.search(
        r"Your request ID is ([0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12})\.",
        response.content.decode("utf-8"),
    )
    assert match
    uuid = match[1]
    # Test list view
    simulation_list = reverse("simulation_list")
    response = admin_client.get(simulation_list)
    assert response.status_code == 200
    assert f"<td>{uuid}</td>" in response.content.decode("utf-8")
    # Print the UUID to stdout to enable the teardown method to check the image
    print(uuid)


def _teardown_test_simulation(uuid, settings):
    """
    Additional checks which run after the celery worker is done
    """
    print(f"UUID of the generated simulation: {uuid}")
    simulation = LeewaySimulation.objects.get(uuid=uuid)
    # Assert that the simulation was successful and an images has been generated
    assert simulation.img
    # Test that one message has been sent.
    # pylint: disable=no-member
    assert len(mail.outbox) == 1
    # Verify the email
    result_email = mail.outbox[0]
    assert result_email.from_email == settings.DEFAULT_FROM_EMAIL
    assert result_email.to == ["admin@example.com"]
    assert result_email.bcc == []
    assert result_email.cc == []
    assert result_email.reply_to == []
    assert result_email.subject == "Leeway Drift Simulation Result"
    assert (
        f"Your request with ID {uuid} has been processed. Find the image attached."
        in result_email.body
    )
    assert len(result_email.attachments) == 1
    # pylint: disable=unused-variable
    filename, content, mimetype = result_email.attachments[0]
    assert filename == simulation.img.name
