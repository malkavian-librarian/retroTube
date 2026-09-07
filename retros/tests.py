import pytest

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
