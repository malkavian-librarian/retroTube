import uuid

import pytest
from django.urls import reverse

from retros.models import Retro
from retros.services import check_pin, create_retro


@pytest.mark.django_db
def test_create_retro_persists_fields_with_hashed_pin():
    retro = create_retro(
        name="Sprint 12 Retro",
        description="End of sprint retro",
        participant_limit=8,
        raw_pin="1234",
    )

    saved = Retro.objects.get(pk=retro.pk)
    assert saved.name == "Sprint 12 Retro"
    assert saved.description == "End of sprint retro"
    assert saved.participant_limit == 8
    assert saved.pin_hash != "1234"
    assert "1234" not in saved.pin_hash


@pytest.mark.django_db
def test_check_pin_matches_only_the_correct_pin():
    retro = create_retro(name="Retro", raw_pin="4242")

    assert check_pin(retro, "4242") is True
    assert check_pin(retro, "0000") is False


@pytest.mark.django_db
def test_create_retro_without_optional_fields_succeeds():
    retro = create_retro(name="Retro", description="", participant_limit=None, raw_pin="1111")

    assert retro.pk is not None
    assert retro.description == ""
    assert retro.participant_limit is None


@pytest.mark.django_db
def test_pin_hash_is_salted_not_deterministic():
    retro_a = create_retro(name="Retro A", raw_pin="1234")
    retro_b = create_retro(name="Retro B", raw_pin="1234")

    assert retro_a.pin_hash != retro_b.pin_hash


@pytest.mark.django_db
def test_default_phase_is_writing():
    retro = create_retro(name="Retro", raw_pin="1234")

    assert retro.phase == Retro.Phase.WRITING


@pytest.mark.django_db
def test_valid_create_retro_submission_creates_retro_and_redirects(client):
    response = client.post(
        reverse("retro_create"),
        {
            "name": "Sprint 12 Retro",
            "description": "End of sprint retro",
            "participant_limit": "8",
            "pin": "1234",
        },
    )

    assert Retro.objects.count() == 1
    retro = Retro.objects.get()
    assert retro.name == "Sprint 12 Retro"
    assert retro.description == "End of sprint retro"
    assert retro.participant_limit == 8
    assert check_pin(retro, "1234") is True
    assert response.status_code == 302
    assert response["Location"] == reverse("retro_detail", kwargs={"pk": retro.pk})


@pytest.mark.django_db
def test_create_retro_without_name_creates_no_retro_and_shows_error(client):
    response = client.post(reverse("retro_create"), {"name": "", "pin": "1234"})

    assert Retro.objects.count() == 0
    assert response.status_code == 200
    assert "name" in response.context["form"].errors


@pytest.mark.django_db
def test_create_retro_without_pin_creates_no_retro_and_shows_error(client):
    response = client.post(reverse("retro_create"), {"name": "Retro", "pin": ""})

    assert Retro.objects.count() == 0
    assert response.status_code == 200
    assert "pin" in response.context["form"].errors


@pytest.mark.django_db
@pytest.mark.parametrize("participant_limit", ["0", "-1"])
def test_create_retro_with_non_positive_participant_limit_creates_no_retro(
    client, participant_limit
):
    response = client.post(
        reverse("retro_create"),
        {"name": "Retro", "pin": "1234", "participant_limit": participant_limit},
    )

    assert Retro.objects.count() == 0
    assert response.status_code == 200
    assert "participant_limit" in response.context["form"].errors


@pytest.mark.django_db
def test_two_retros_can_share_the_same_name():
    create_retro(name="Weekly Retro", raw_pin="1111")
    create_retro(name="Weekly Retro", raw_pin="2222")

    assert Retro.objects.filter(name="Weekly Retro").count() == 2


@pytest.mark.django_db
def test_retro_detail_shows_name_and_phase(client):
    retro = create_retro(name="Sprint Retro", raw_pin="1234")

    response = client.get(reverse("retro_detail", kwargs={"pk": retro.pk}))

    assert response.status_code == 200
    assert "Sprint Retro" in response.content.decode()
    assert Retro.Phase.WRITING in response.content.decode()


@pytest.mark.django_db
def test_retro_detail_unknown_uuid_returns_404(client):
    response = client.get(reverse("retro_detail", kwargs={"pk": uuid.uuid4()}))

    assert response.status_code == 404
