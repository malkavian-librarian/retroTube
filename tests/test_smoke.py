import pytest
from django.apps import apps
from django.urls import reverse


@pytest.mark.django_db
def test_homepage_returns_200(client):
    response = client.get(reverse("healthcheck"))
    assert response.status_code == 200


def test_project_apps_are_registered():
    expected = {"retros", "boards", "voting", "actions", "realtime"}
    installed = {app_config.name for app_config in apps.get_app_configs()}
    assert expected.issubset(installed)
