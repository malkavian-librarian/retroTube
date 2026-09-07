from django.contrib.auth.hashers import check_password, make_password

from retros.models import Retro


def create_retro(name, description="", participant_limit=None, raw_pin=""):
    return Retro.objects.create(
        name=name,
        description=description or "",
        participant_limit=participant_limit,
        pin_hash=make_password(raw_pin),
    )


def check_pin(retro, raw_pin):
    return check_password(raw_pin, retro.pin_hash)
