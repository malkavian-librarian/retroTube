from uuid import uuid4

from django.db import models


class Retro(models.Model):
    class Phase(models.TextChoices):
        WRITING = "writing"
        REVEALED = "revealed"
        VOTING = "voting"
        DISCUSSING = "discussing"
        CLOSED = "closed"

    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    participant_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    pin_hash = models.CharField(max_length=128)

    phase = models.CharField(max_length=20, choices=Phase.choices, default=Phase.WRITING)

    timer_duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    timer_started_at = models.DateTimeField(null=True, blank=True)
    timer_paused_remaining_seconds = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
