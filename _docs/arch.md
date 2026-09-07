# Architecture — Weekly Retro Tool

Reference doc for any agent/dev picking up this project. Pairs with `_docs/weekly-retro-mvp.md` (product spec — read that first for behavior).

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language/framework | Django 5.x, Python 3.12 | Team's strongest language; Django's batteries (ORM, migrations, templates, sessions) cover everything this app needs without extra services. |
| Realtime | Django Channels + Daphne (ASGI) | App is fundamentally realtime (live cards, votes, timer, presence) — needs persistent WebSocket connections, which rules out plain WSGI/serverless. |
| Channel layer / ephemeral state | Redis | Channels pub/sub backend for broadcasting to all clients in a retro "room"; also used for short-lived state (ready flags, presence) that doesn't need to survive in Postgres. |
| Database | PostgreSQL | Relational fit — cards/votes/actions all reference retros and each other; needs real constraints (unique vote per card, cascading delete on retro deletion). |
| Frontend rendering | Django templates + htmx | Server renders HTML fragments; WebSocket messages trigger htmx swaps. Avoids standing up a separate SPA/JS build — keeps everything in Python. |
| Styling | Tailwind CSS | Utility CSS, no design system overhead for an MVP. |
| Hosting | Railway | Runs Daphne as a persistent ASGI process (required for WebSockets) + Postgres and Redis as add-on plugins, all in one project. |
| Auth | None (no accounts) | Identity = signed cookie (Django `signing`) scoped to a retro, set on Join. Retro access = PIN, hashed with `django.contrib.auth.hashers.make_password`. |

Explicitly **not** using: DRF (no public REST API needed — server-rendered pages + WebSocket events cover it), Celery (no background jobs in MVP), Vercel (serverless functions can't hold WebSocket connections — see decision note below).

### Decision note: why not Vercel

Vercel Functions are stateless/serverless — no persistent connections, so no Django Channels/WebSockets. The product spec requires true realtime sync (cards, blind voting, shared timer), not polling. Railway runs Daphne as a long-lived process, so WebSockets work natively. This was a deliberate tradeoff to keep realtime UX over Vercel's DX — revisit only if realtime requirements loosen.

## Django apps (suggested layout)

```
retro_tool/
  retros/       # Retro model, create/join/close views, PIN auth, phase state machine
  boards/       # Card, CardGroup — write/reveal/group behavior
  voting/       # Vote model, blind voting logic, tallying
  actions/      # Action, Comment models
  realtime/     # Channels consumers, room group naming, event contracts
```

Keep apps small and behavior-scoped rather than one monolithic `retro` app — each maps to a section of the spec (§3 Write, §5 Voting, §6 Discussion & Actions) so future agents can find the relevant code by feature name.

## Data models (sketch)

```python
# retros/models.py
class Retro(models.Model):
    class Phase(models.TextChoices):
        WRITING = "writing"
        REVEALED = "revealed"
        VOTING = "voting"
        DISCUSSING = "discussing"
        CLOSED = "closed"

    id = models.UUIDField(primary_key=True, default=uuid4)  # used in the private URL
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    participant_limit = models.PositiveSmallIntegerField(null=True, blank=True)  # soft limit
    pin_hash = models.CharField(max_length=128)

    phase = models.CharField(max_length=20, choices=Phase.choices, default=Phase.WRITING)

    # shared timer (§8) — nullable, one active timer per retro
    timer_duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    timer_started_at = models.DateTimeField(null=True, blank=True)
    timer_paused_remaining_seconds = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class Participant(models.Model):
    retro = models.ForeignKey(Retro, on_delete=models.CASCADE, related_name="participants")
    name = models.CharField(max_length=100)
    is_ready = models.BooleanField(default=False)       # Write phase readiness
    voting_done = models.BooleanField(default=False)    # Voting phase "Done voting"
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)  # leaving removes votes, keeps cards (§8)

    class Meta:
        # Rejoining creates a new identity (§8) — no unique constraint on (retro, name)
        pass
```

```python
# boards/models.py
class CardGroup(models.Model):
    retro = models.ForeignKey(Retro, on_delete=models.CASCADE, related_name="card_groups")
    column = models.CharField(max_length=20, choices=[
        ("went_well", "Went well"),
        ("not_well", "Didn't go well"),
        ("ideas", "Ideas"),
    ])
    # grouping only happens after Reveal — created on first "group these cards" action


class Card(models.Model):
    retro = models.ForeignKey(Retro, on_delete=models.CASCADE, related_name="cards")
    author = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="cards")
    column = models.CharField(max_length=20, choices=CardGroup._meta.get_field("column").choices)
    text = models.TextField()
    group = models.ForeignKey(CardGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="cards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Column on a Card can change after Reveal (author moves own card, §4) —
    # track via column field directly, group membership independent of column moves.
```

```python
# voting/models.py
class Vote(models.Model):
    retro = models.ForeignKey(Retro, on_delete=models.CASCADE, related_name="votes")
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="votes")
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("participant", "card")  # max one vote per card per participant
        # "up to 5 votes total" enforced in the view/service layer (count per participant per retro)
```

```python
# actions/models.py
class Comment(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # flat only — no parent/reply field (threaded comments explicitly out of MVP)


class Action(models.Model):
    retro = models.ForeignKey(Retro, on_delete=models.CASCADE, related_name="actions")
    source_card = models.ForeignKey(Card, null=True, blank=True, on_delete=models.SET_NULL, related_name="actions")
    description = models.TextField()
    owner = models.ForeignKey(Participant, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_actions")
    created_at = models.DateTimeField(auto_now_add=True)
    # no status/due-date fields — explicitly out of MVP
```

### Notes on the sketch

- **Retro deletion (§9)** cascades through every FK above via `on_delete=models.CASCADE`, matching "permanently delete the retro."
- **Leaving removes votes but keeps cards (§8)**: don't cascade-delete a `Participant` on leave — set `left_at` and separately delete their `Vote` rows. Keep the participant row so existing `Card.author` FKs stay valid.
- **Phase gating** (no new cards after Reveal, no card edits after Reveal, discussion locked until voting done, etc.) belongs in view/service-layer checks against `Retro.phase`, not in the models — keep models dumb, put the state machine in one place (e.g. `retros/services.py`) so phase rules aren't scattered.
- **Identity**: no `User` model. A participant's browser identity is a signed cookie (`{retro_id, participant_id}` via `django.core.signing`) set on Join, checked on every request/WebSocket connect. This is what "identity remembered in that browser" (§2) means in implementation terms.

## Realtime event contract

One Channels group per retro (`retro_<uuid>`). Every mutation (card CRUD, ready toggle, group, vote, action CRUD, timer control, phase transition) is:

1. Validated + persisted via a normal Django view or a Channels consumer method (pick one path consistently — recommend plain Django views for writes, Channels only for broadcasting the result, so business logic stays testable outside the WebSocket layer).
2. Broadcast as a small JSON event (`{"type": "card.created", "card": {...}}`, `{"type": "phase.changed", "phase": "revealed"}`, etc.) to the retro's group.
3. Received client-side and turned into an htmx `hx-swap` (fetch the updated fragment) or a minimal direct DOM patch for high-frequency events (timer tick).

Keep the event vocabulary small and 1:1 with spec sections — don't invent generic "update" events; name them after what happened so future agents can trace an event back to a spec line.

## Coding standards

- **Formatting**: `black` + `isort`, enforced via pre-commit. `ruff` for linting.
- **Tests**: `pytest-django`. Every phase-transition rule and vote-limit rule (the parts of the spec with hard numbers/constraints) needs a test — these are the easiest things to silently regress.
- **Migrations**: commit migrations with the model change in the same PR; never hand-edit a migration that's already been applied elsewhere.
- **Settings**: 12-factor — all secrets/config (DB URL, Redis URL, `SECRET_KEY`, `ALLOWED_HOSTS`) via environment variables, Railway injects these automatically for the Postgres/Redis plugins.
- **No accounts app, no DRF, no Celery** — if a future task seems to need one of these, treat it as a scope change and flag it rather than adding silently.

## Deployment (Railway)

- One Railway service running Daphne against `retro_tool/asgi.py` (not `manage.py runserver`, not gunicorn — needs ASGI for WebSockets).
- Postgres plugin + Redis plugin attached to the same project; Railway auto-injects `DATABASE_URL` / `REDIS_URL`.
- `railway.json` / `Procfile` start command: `daphne -b 0.0.0.0 -p $PORT retro_tool.asgi:application`.
- Run `python manage.py migrate` as a Railway release/deploy step, not manually.
