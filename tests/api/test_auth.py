import base64

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("url", ["/api/auth/login/", "/api/v1/auth/login/"])
def test_login_with_basic_auth(url):
    get_user_model().objects.create_user(username="alice", password="secret")
    client = APIClient()

    credentials = base64.b64encode(b"alice:secret").decode()
    response = client.post(url, HTTP_AUTHORIZATION=f"Basic {credentials}")
    assert response.status_code == 200
    token = response.json()["token"]

    client = APIClient()
    response = client.get("/api/v1/simulations/", HTTP_AUTHORIZATION=f"Token {token}")
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_login_with_wrong_password():
    get_user_model().objects.create_user(username="alice", password="secret")
    credentials = base64.b64encode(b"alice:wrong").decode()
    response = APIClient().post("/api/v1/auth/login/", HTTP_AUTHORIZATION=f"Basic {credentials}")
    assert response.status_code == 401
