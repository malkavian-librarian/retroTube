# Weekly Retro Tool — Task Backlog

Reference docs: `_docs/weekly-retro-mvp.md` (product spec) and `_docs/arch.md` (architecture/stack). Read both before starting any task below — each task assumes that context but does not repeat it.

Stack recap for quick reference: Django 5.x + Channels/Daphne (ASGI), Redis (channel layer), PostgreSQL, Django templates + htmx, Tailwind CSS, Railway hosting, pytest-django for tests, black/isort/ruff for formatting/linting.

Tasks are ordered to match a sensible build sequence, but each one is written to be handed to someone who has only read the spec + architecture doc — not the other tasks.

---

## 1. Project scaffolding with a passing test
goal: Stand up an empty, runnable Django project with the app layout from the architecture doc and one passing test.
description: Create the Django project (`retro_tool/`) with the five apps described in the architecture doc (`retros`, `boards`, `voting`, `actions`, `realtime`) registered in `INSTALLED_APPS`, each with an empty `models.py`. Configure settings for PostgreSQL and Redis via environment variables (12-factor style), and add Channels to `INSTALLED_APPS` with a placeholder ASGI routing config. Set up `pytest-django`, `black`, `isort`, and `ruff` with sane default configs. Add a trivial smoke test (e.g. "settings load" or "homepage returns 200") so there is at least one green test in CI/local runs. No feature code, no models with fields yet — this task is purely scaffolding.
acceptance_criteria:
- [ ] Django project `retro_tool` created with `manage.py` runnable via `python manage.py check`
- [ ] Apps `retros`, `boards`, `voting`, `actions`, `realtime` exist and are registered in `INSTALLED_APPS`
- [ ] `channels` installed and configured with a minimal `asgi.py` (routing can be empty/placeholder)
- [ ] Settings read `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ALLOWED_HOSTS` from environment variables, with local-dev defaults documented in a `.env.example`
- [ ] `pytest-django` configured (`pytest.ini` or `pyproject.toml`) and `pytest` runs successfully
- [ ] At least one test exists and passes (e.g. smoke test hitting a trivial URL or checking Django settings load)
- [ ] `black`, `isort`, `ruff` configs added (pyproject.toml) and running them produces no errors on the fresh scaffold
- [ ] `requirements.txt` (or `pyproject.toml` dependency list) pins Django, Channels, Daphne, psycopg, redis, pytest-django, htmx-friendly deps as needed
- [ ] README or top-of-repo note explains how to install deps and run tests locally

## 2. Retro model and PIN hashing
goal: Implement the `Retro` model with phase state and hashed-PIN creation logic, fully unit tested.
description: In the `retros` app, implement the `Retro` model as sketched in the architecture doc (UUID primary key, name, description, participant_limit, pin_hash, phase enum, timer fields, created_at/closed_at). Add a small service function (e.g. `retros/services.py`) that creates a Retro from `(name, description, participant_limit, raw_pin)`, hashing the PIN with `django.contrib.auth.hashers.make_password`, and a `check_pin(retro, raw_pin)` helper using `check_password`. No views/URLs/templates in this task — model + service + migration + tests only.
acceptance_criteria:
- [ ] `Retro` model implemented matching the architecture doc's field list and `Phase` choices (writing/revealed/voting/discussing/closed)
- [ ] Migration generated and applied cleanly on a fresh database
- [ ] `create_retro(name, description, participant_limit, raw_pin)` service function creates a Retro with `pin_hash` set (never storing the raw PIN)
- [ ] `check_pin(retro, raw_pin)` returns True/False correctly for matching/non-matching PINs
- [ ] Default phase on creation is `writing`
- [ ] Test: creating a retro with valid data persists correctly and PIN is hashed (not equal to raw PIN in DB)
- [ ] Test: `check_pin` succeeds with the correct PIN and fails with an incorrect one
- [ ] Test: `participant_limit` and `description` are optional (nullable/blank) and retro creation succeeds without them

## 3. Create Retro view and form
goal: Let a visitor create a new standalone retro through a web form and land on its private link.
description: Build the "Create" step of the flow (§1 of the spec) as a Django view + template using the `create_retro` service from Task 2. The form collects retro name, optional description, optional soft participant limit, and creator-defined PIN. On success, redirect to the retro's private URL (`/retro/<uuid>/`), which for this task can render a placeholder page just showing the retro name and phase — Join/Write functionality is out of scope here. No accounts, no login — anyone can create a retro.
acceptance_criteria:
- [ ] GET `/retro/create/` renders a form with fields: name (required), description (optional), participant_limit (optional), PIN (required)
- [ ] POST with valid data creates a Retro via the Task 2 service and redirects to `/retro/<uuid>/`
- [ ] POST with missing required fields (name or PIN) re-renders the form with validation errors, no Retro created
- [ ] The private retro URL uses the Retro's UUID, not a sequential/guessable ID
- [ ] `/retro/<uuid>/` renders a placeholder page showing at least the retro name and current phase for a valid UUID
- [ ] `/retro/<uuid>/` for a non-existent UUID returns 404
- [ ] Test: valid form submission creates a Retro and redirects correctly
- [ ] Test: invalid form submission (missing name/PIN) does not create a Retro
- [ ] Test: visiting an unknown retro UUID returns 404

## 4. Participant model and Join flow with signed-cookie identity
goal: Let a participant join a retro by entering the PIN and their name, establishing a signed-cookie identity.
description: Implement the `Participant` model in `retros` (or wherever it currently lives per Task 2's app) as sketched in the architecture doc, with no unique constraint on `(retro, name)` since rejoining creates a new identity. Build the Join view (§2 of the spec): visiting the private retro link prompts for PIN + name; on success, create a `Participant` row and set a signed cookie (`django.core.signing`) containing `{retro_id, participant_id}`, scoped to that retro. Subsequent requests to that retro's pages should recognize the participant from the cookie. Enforce that joining closes after the retro's phase moves past `writing` (i.e., once revealed, no new joins) — for this task it's enough to check `retro.phase == Phase.WRITING` before allowing Join.
acceptance_criteria:
- [ ] `Participant` model implemented (retro FK, name, is_ready, voting_done, joined_at, left_at) with migration
- [ ] No unique constraint on `(retro, name)` — joining twice with the same name creates two distinct participants
- [ ] Join view accepts PIN + name; wrong PIN shows an error and does not create a Participant or set a cookie
- [ ] Correct PIN + name creates a Participant and sets a signed cookie identifying `{retro_id, participant_id}`
- [ ] A helper (e.g. `get_current_participant(request, retro)`) reads and verifies the signed cookie, returning `None` if absent/invalid/for a different retro
- [ ] Attempting to Join a retro whose phase is not `writing` is rejected with a clear message
- [ ] Test: correct PIN + name joins successfully and sets a valid signed cookie
- [ ] Test: incorrect PIN does not create a Participant
- [ ] Test: joining is rejected once the retro's phase is not `writing`
- [ ] Test: the cookie helper correctly resolves a participant from a valid cookie and returns None for a tampered/invalid one

## 5. Card model and Write-phase CRUD
goal: Let a joined participant create, edit, and delete their own cards in the three fixed columns during the Write phase.
description: Implement the `Card` model in `boards` per the architecture doc (retro FK, author FK, column choice, text, group FK nullable, timestamps), with the three fixed columns (`went_well`, `not_well`, `ideas`) matching §3 of the spec. Build views for creating, editing, and deleting a card, restricted to: the retro must be in `writing` phase, the requester must be a joined participant (via the Task 4 cookie helper), and edit/delete are only allowed on cards the requester authored. During Writing, a participant's view of the board should only show their own cards (not other participants' cards) — enforce this in the query, not just the template.
acceptance_criteria:
- [ ] `Card` model implemented with the three column choices and migration applied
- [ ] Authenticated (joined) participant can create a card in any of the three columns while retro is in `writing` phase
- [ ] Card creation is rejected if the retro is not in `writing` phase
- [ ] Card creation/edit/delete is rejected for requests without a valid participant cookie for that retro
- [ ] A participant can edit or delete only their own cards; attempting to edit/delete another participant's card is rejected (403 or equivalent)
- [ ] The board view during Writing returns only the requesting participant's own cards, never other participants' cards
- [ ] Test: creating a card persists it with the correct author and column
- [ ] Test: a participant cannot edit/delete another participant's card
- [ ] Test: card creation fails once phase is not `writing`
- [ ] Test: the Writing-phase board query excludes other participants' cards

## 6. Ready flag and automatic Reveal transition
goal: Let participants mark themselves Ready, auto-triggering Reveal when everyone is ready, with a manual force-Reveal option.
description: Add a "mark ready" action for a joined participant that sets `Participant.is_ready = True`. Implement the phase-transition rule from §3: when all participants (excluding any who have left, if that's already modeled) in a retro are ready, the retro's phase automatically transitions from `writing` to `revealed`. Put this phase-transition logic in a single service function (e.g. `retros/services.py`) rather than scattering it across views, per the architecture doc's guidance. Also add a "force reveal" action any participant can trigger, which transitions the phase immediately regardless of ready state (a confirmation step can be a simple "are you sure" query param or POST confirmation flag — full UI confirmation dialogs are not required for this task).
acceptance_criteria:
- [ ] Participant can mark themselves ready via a view/endpoint; `is_ready` persists correctly
- [ ] A participant can un-ready themselves before Reveal happens (if the spec/UI calls for a toggle) — otherwise document that ready is one-way for this task
- [ ] When every active participant in a retro is ready, phase automatically transitions from `writing` to `revealed` (no manual trigger needed)
- [ ] A single service function owns the "check all ready and transition" logic, called after every ready-flag change
- [ ] Force-reveal endpoint transitions phase to `revealed` immediately regardless of ready states, and requires a confirmation flag on the request
- [ ] Once phase is `revealed`, no further "mark ready" actions are meaningful — attempting one is a no-op or rejected, not an error that breaks the flow
- [ ] Test: retro auto-reveals when the last participant marks ready
- [ ] Test: retro does not reveal while at least one participant is not ready
- [ ] Test: force-reveal transitions phase even with zero participants ready
- [ ] Test: a retro with only one participant reveals as soon as that participant is ready

## 7. Reveal & grouping behavior
goal: After Reveal, show authors on cards, lock card creation/edit/delete, and let anyone group similar cards within a column.
description: Once a retro's phase is `revealed`, enforce the §4 rules: no new cards can be created, existing cards can no longer be edited or deleted by anyone (including their author), but authors may still move their own cards between columns. Implement `CardGroup` per the architecture doc and a "group cards" action that lets any participant group two or more cards within the same column into a `CardGroup` — grouped cards keep their individual text and author, only their `group` FK changes. Card templates/serialized data should now include author name since cards show authorship after Reveal.
acceptance_criteria:
- [ ] Card create/edit/delete endpoints reject requests once phase is `revealed` or later (returns error, does not silently succeed)
- [ ] An author can move their own card to a different column while phase is `revealed`
- [ ] A participant cannot move a card they did not author
- [ ] `CardGroup` model implemented (retro FK, column) with migration
- [ ] "Group cards" action accepts a list of card IDs within the same column and assigns them all the same `CardGroup`, creating the group if needed
- [ ] Grouping rejects cards from different columns (cannot group across columns) with a clear error
- [ ] Grouped cards retain their original `text` and `author` — grouping only changes the `group` FK
- [ ] Card data returned to the client after Reveal includes author name
- [ ] Test: card create/edit/delete all fail once phase is `revealed`
- [ ] Test: author can move their own card between columns post-Reveal; non-author cannot
- [ ] Test: grouping two same-column cards creates a shared `CardGroup` and preserves each card's text/author
- [ ] Test: attempting to group cards from two different columns is rejected

## 8. Vote model and blind voting logic
goal: Implement up-to-5 blind votes per participant per retro, with totals/voters hidden until voting ends.
description: Implement the `Vote` model per the architecture doc (participant FK, card FK, unique-together on participant+card) in the `voting` app. Build a "cast vote" / "remove vote" endpoint enforcing: retro must be in `voting` phase, a participant may vote at most once per card (self-voting allowed), and a participant may have at most 5 total votes across the retro at any time — enforce the 5-vote cap in the service/view layer since it's not a DB constraint. While the retro is in `voting` phase, no endpoint should expose vote counts or voter identities to any participant, including the voter's own total tally view of others (the voter can see which cards they personally voted for). Phase transition into `voting` itself is out of scope for this task — assume a retro can already be manually set to `voting` phase (e.g. via Django admin or a fixture) for testing purposes; a dedicated task later wires up the transition and results reveal.
acceptance_criteria:
- [ ] `Vote` model implemented with `unique_together` on `(participant, card)`, migration applied
- [ ] Participant can cast a vote on any card in the retro, including their own (self-voting allowed)
- [ ] Casting a vote fails once the participant already has 5 active votes in that retro
- [ ] Casting a duplicate vote on the same card by the same participant is rejected (no double-voting a single card)
- [ ] Participant can remove/change one of their own votes before "Done voting" (assume "done" flag exists per Participant model already; toggling it is out of scope here)
- [ ] Voting actions are rejected if the retro is not in `voting` phase
- [ ] No endpoint reachable during `voting` phase reveals vote counts or voter names for any card to any participant
- [ ] A participant can retrieve their own current vote selections (which cards they've voted for) even while phase is `voting`
- [ ] Test: a participant can cast up to exactly 5 votes and the 6th is rejected
- [ ] Test: self-voting succeeds
- [ ] Test: duplicate vote on the same card by the same participant is rejected
- [ ] Test: no vote counts/voter identities leak through any view/response while phase is `voting`

## 9. Done Voting, auto-reveal of results, and ranking
goal: Let participants finish voting irreversibly, auto-transition to results when everyone's done, and expose vote counts/voters/ranking afterward.
description: Add a "Done voting" action that sets `Participant.voting_done = True` per §5 of the spec; once set for a participant, it cannot be unset (their votes become locked — reuse or extend the vote endpoints from Task 8 to reject changes once `voting_done` is True for that participant). When every active participant is done voting, auto-transition the retro's phase from `voting` to `discussing` (reuse the single-service-function pattern from Task 6 for phase transitions). Add a force-end-voting action any participant can trigger. After the phase leaves `voting`, expose per-card vote count, the names of voters, and an overall ranking (ordered by vote count) through a results view/endpoint.
acceptance_criteria:
- [ ] "Done voting" endpoint sets `voting_done = True` for the requesting participant and is irreversible (a second call is a no-op, cannot be undone)
- [ ] Once a participant's `voting_done` is True, their vote-cast/remove endpoints (from Task 8) reject further changes
- [ ] When all active participants have `voting_done = True`, phase auto-transitions from `voting` to `discussing`
- [ ] Force-end-voting endpoint transitions the phase immediately regardless of individual done states, with a confirmation flag required
- [ ] Once phase is no longer `voting`, a results view returns, per card: vote count and list of voter names
- [ ] Results view also returns an overall ranking of cards ordered by vote count (ties broken consistently, e.g. by card creation order)
- [ ] Results are not exposed while phase is still `voting` (build on Task 8's hiding rule)
- [ ] Test: retro auto-transitions to `discussing` when the last participant finishes voting
- [ ] Test: a participant cannot cast/change a vote after marking themselves done
- [ ] Test: force-end-voting transitions phase even with participants not done
- [ ] Test: results view returns correct counts, voter names, and ranking order after voting ends

## 10. Flat comments on cards
goal: Let participants add simple, non-threaded comments to any card once discussion is unlocked.
description: Implement the `Comment` model per the architecture doc (card FK, author FK, text, created_at) in the `actions` app (per the suggested layout) or wherever comments currently belong. Build create/list endpoints: any joined participant can add a comment to any card, but only once the retro's phase is `discussing` or later (i.e., after voting has ended, per §6 of the spec). Comments are flat — there is no reply-to/parent field and no nesting in the API or template. Deleting/editing comments is out of scope unless the spec requires it (it doesn't for MVP) — implement create + list only.
acceptance_criteria:
- [ ] `Comment` model implemented (card FK, author FK, text, created_at), migration applied, no parent/reply field
- [ ] A joined participant can add a comment to any card once phase is `discussing` or later
- [ ] Adding a comment is rejected if the retro's phase is still `writing`, `revealed`, or `voting`
- [ ] Comments endpoint requires a valid participant cookie (Task 4) — anonymous requests are rejected
- [ ] A card's comment list returns comments in chronological order with author name and text
- [ ] No editing/deleting endpoints are built for comments (explicitly out of scope per spec)
- [ ] Test: comment creation succeeds once phase is `discussing`
- [ ] Test: comment creation fails while phase is `writing`, `revealed`, or `voting`
- [ ] Test: comment list returns all comments for a card in chronological order with correct author attribution

## 11. Action items — create, edit, delete, reassign
goal: Let any participant create action items (from a card or standalone), and edit/delete/reassign any action before the retro closes.
description: Implement the `Action` model per the architecture doc (retro FK, optional source_card FK, description, optional owner FK) in the `actions` app. Build endpoints to create an action either from a specific card or independently (owner and source_card are both optional/nullable, matching the model sketch), plus edit, delete, and reassign-owner endpoints. Per §6 of the spec, any participant can edit/delete/reassign any action (not just their own) up until the retro is closed — there is no acceptance workflow, no due dates, and no status tracking, so do not add fields or endpoints for those.
acceptance_criteria:
- [ ] `Action` model implemented with `source_card` and `owner` both nullable, migration applied
- [ ] Any joined participant can create an action with just a description (no card, no owner required)
- [ ] Any joined participant can create an action linked to a specific card (`source_card` set)
- [ ] Any joined participant can edit an action's description, regardless of who created it
- [ ] Any joined participant can reassign an action's `owner` to a different participant (or unset it), regardless of who created it
- [ ] Any joined participant can delete any action, regardless of who created it
- [ ] Action create/edit/delete/reassign endpoints are rejected once the retro's phase is `closed`
- [ ] No status or due-date field/endpoint exists anywhere in this task's implementation
- [ ] Test: creating a standalone action and a card-linked action both succeed
- [ ] Test: a participant can edit/delete/reassign an action they did not create
- [ ] Test: action mutations are rejected once phase is `closed`

## 12. Close retro flow and read-only summary
goal: Let any participant close a retro after voting has ended, producing a read-only summary view.
description: Implement the Close action from §7 of the spec: any joined participant can close a retro whose phase is `discussing` (i.e., voting has already ended) — transition phase to `closed` and set `closed_at`. Closing requires a confirmation flag on the request (same pattern as force-reveal/force-end-voting from earlier tasks). Build a read-only summary view for closed retros showing: the original board (cards by column, with groups), overall top feedback (highest-voted cards), rankings within each category/column, all comments, and all action items. Once closed, verify (via existing phase-gating from prior tasks) that no board/vote/comment/action mutation endpoints succeed anymore.
acceptance_criteria:
- [ ] Close endpoint transitions phase from `discussing` to `closed` and sets `closed_at`, requiring a confirmation flag
- [ ] Close is rejected if the retro's phase is anything other than `discussing` (can't close during writing/revealed/voting)
- [ ] Closing requires the requester to be a joined participant for that retro
- [ ] Summary view for a closed retro shows: board grouped by column (including card groups), top feedback ranked by votes, per-column rankings, all comments per card, and all action items
- [ ] Summary view is accessible without further mutation — it's read-only, no create/edit forms rendered
- [ ] All previously-built mutation endpoints (cards, votes, comments, actions, ready/done flags) reject requests once phase is `closed`, relying on each task's existing phase checks — this task adds a test confirming the aggregate behavior, not new gating code, unless a gap is found
- [ ] Test: closing a `discussing`-phase retro succeeds and phase becomes `closed`
- [ ] Test: closing fails for a retro in any phase other than `discussing`
- [ ] Test: summary view returns correct board/rankings/comments/actions data for a closed retro
- [ ] Test: at least one mutation endpoint from an earlier task (e.g. adding a comment) is confirmed rejected once phase is `closed`

## 13. Copy-to-clipboard summary export
goal: Give the closed-retro summary a "copy to clipboard" action that produces a clean text/markdown summary of the retro.
description: Per §7 of the spec, the closed-retro summary can be copied to clipboard. Add a server-rendered (or endpoint-provided) plain-text/markdown representation of the summary — retro name, top feedback, per-column rankings, comments, and action items — and wire a "Copy summary" button on the closed-retro page that copies this text to the clipboard using the browser Clipboard API. This is a small, mostly-frontend task on top of Task 12's summary view; no new backend models are needed, though a dedicated endpoint/template fragment that renders the plain-text version is expected.
acceptance_criteria:
- [ ] A view or template fragment renders the closed retro's summary as plain text/markdown (not HTML) matching the same content as Task 12's summary view
- [ ] The plain-text summary includes: retro name, top feedback (ranked), per-column rankings, comments, and action items with owners
- [ ] A "Copy summary" button exists on the closed-retro page
- [ ] Clicking "Copy summary" copies the plain-text summary to the clipboard via the browser Clipboard API, with a visible confirmation (e.g. "Copied!" message)
- [ ] The button is only shown/enabled on closed retros
- [ ] Test: the plain-text summary endpoint/fragment returns the expected content for a closed retro with known cards/votes/comments/actions
- [ ] Manual check: clicking the button in a browser actually places the summary text on the clipboard (documented as tested, since clipboard access isn't easily unit-tested)

## 14. Retro deletion with typed-name confirmation
goal: Let any participant permanently delete a retro by typing its name to confirm, cascading through all related data.
description: Per §9 of the spec, any participant (joined via the Task 4 cookie) can permanently delete a retro at any time (open or closed) by typing the retro's exact name as confirmation. Build a delete endpoint that requires the submitted confirmation string to exactly match `retro.name`, then deletes the Retro — relying on the `on_delete=models.CASCADE` relationships already defined across the Card, Vote, Comment, Action, Participant, CardGroup models (per the architecture doc) to clean up everything else in one query. After deletion, the retro's URL should 404.
acceptance_criteria:
- [ ] Delete endpoint requires a joined participant for that retro (valid signed cookie)
- [ ] Delete endpoint requires a `confirm_name` field that must exactly match `retro.name` (case-sensitive) or the request is rejected with no deletion
- [ ] On a correct confirmation, the Retro row is deleted and all related Cards, CardGroups, Votes, Comments, Actions, and Participants are also deleted (verify cascade actually works end-to-end, not just assumed from `on_delete`)
- [ ] Deletion works regardless of the retro's current phase (writing through closed)
- [ ] After deletion, visiting the retro's URL returns 404
- [ ] Test: deletion with a mismatched confirmation string does not delete anything
- [ ] Test: deletion with the correct name deletes the retro and all related rows (assert each related table is empty for that retro's former ID)
- [ ] Test: deletion works on a retro in `writing` phase and on a `closed` retro

## 15. Channels realtime infrastructure and card-event broadcasting
goal: Wire up Django Channels so that card create/edit/delete/move events broadcast live to everyone viewing a retro.
description: Per the architecture doc's realtime event contract, set up one Channels group per retro (`retro_<uuid>`), with a Channels consumer that handles WebSocket connect/disconnect for a retro's page and joins/leaves that retro's group. Keep business logic in existing Django views (per the architecture doc's recommendation) — after a card is created/edited/deleted/moved (from Tasks 5 and 7's endpoints), broadcast a small JSON event (e.g. `{"type": "card.created", "card": {...}}`) to the retro's Channels group. On the client side, connect to the retro's WebSocket on page load and trigger an htmx fragment refresh (or minimal DOM update) when a card event arrives. This task only covers card events — voting, comments, actions, ready/phase, and timer events are separate follow-on tasks (not required here).
acceptance_criteria:
- [ ] A Channels consumer accepts WebSocket connections scoped to a retro (e.g. `/ws/retro/<uuid>/`), joining group `retro_<uuid>` on connect and leaving on disconnect
- [ ] Consumer rejects connections without a valid participant cookie for that retro (reuse Task 4's identity check)
- [ ] Card create (Task 5), edit (Task 5), delete (Task 5), and move (Task 7) views broadcast a JSON event to the retro's group after a successful mutation
- [ ] Event payloads are small and named after the action (`card.created`, `card.updated`, `card.deleted`, `card.moved`) — not a generic `update` event
- [ ] A client connected via WebSocket to a retro receives these events in real time when another client mutates a card
- [ ] Client-side JS connects to the retro's WebSocket on page load and triggers an htmx swap (or minimal DOM patch) on each event type
- [ ] Test: a consumer test (using Channels' testing utilities) confirms connecting without a valid cookie is rejected
- [ ] Test: a consumer test confirms a client in a retro's group receives a broadcast event sent to that group
- [ ] Manual check: two browser tabs joined to the same retro see a card appear/update/disappear in near-real-time when one tab performs the action

## 16. Shared timer with realtime sync
goal: Let any participant start, pause, resume, and reset a shared retro timer, synced live to everyone via Channels.
description: Per §8 of the spec, implement the optional shared timer using the `timer_duration_seconds`, `timer_started_at`, and `timer_paused_remaining_seconds` fields already sketched on the `Retro` model (architecture doc) — add them via migration if not already present from Task 2. Build start/pause/resume/reset endpoints any participant can call, and broadcast a `timer.changed` event (via the Task 15 Channels group) to all connected clients whenever the timer's state changes, so all viewers see the same countdown. Timer expiry is informational only — no phase transitions or blocking behavior should be tied to it.
acceptance_criteria:
- [ ] Timer fields exist on `Retro` (add migration if Task 2 didn't already include them)
- [ ] "Start timer" endpoint sets `timer_duration_seconds` and `timer_started_at`, clearing any paused-remaining state
- [ ] "Pause timer" endpoint computes and stores remaining seconds in `timer_paused_remaining_seconds`, clearing `timer_started_at`
- [ ] "Resume timer" endpoint resumes from `timer_paused_remaining_seconds`, setting a new `timer_started_at` accordingly
- [ ] "Reset timer" endpoint clears all timer fields back to unset/null
- [ ] Any joined participant can call any of these endpoints — no owner-only restriction
- [ ] Each timer state change broadcasts a `timer.changed` event with enough data (duration, started_at or remaining) for clients to render a synced countdown
- [ ] Timer expiring does not trigger any phase transition or block any other action — verify by letting a timer expire and confirming board/vote actions still work normally
- [ ] Test: start/pause/resume/reset each correctly update the Retro's timer fields
- [ ] Test: each timer action broadcasts a `timer.changed` event to the retro's group
- [ ] Test: an expired timer has no side effects on phase or other actions

## 17. Participant leave handling
goal: Let a participant leave a retro, removing their votes but keeping their cards and comments intact.
description: Per §8 of the spec, implement a "leave" action for a joined participant: set `Participant.left_at` (already on the model per the architecture doc) and delete that participant's `Vote` rows for the retro, while leaving their `Card`, `Comment`, and `Action` rows untouched (their FKs to the departed Participant remain valid, per the architecture doc's note on why the Participant row isn't deleted). A participant who has left should no longer be able to perform participant actions (voting, commenting, marking ready, etc.) using their old cookie — check `left_at is None` alongside the existing cookie-based identity check used throughout the app. Rejoining after leaving creates a brand-new Participant row (already guaranteed by Task 4's lack of a unique constraint) — this task does not need to change the Join flow, just confirm the behavior with a test.
acceptance_criteria:
- [ ] "Leave" endpoint sets `left_at` on the requesting participant and deletes all of that participant's `Vote` rows for the retro
- [ ] The departed participant's `Card`, `Comment`, and `Action` rows remain in the database, still attributed to them, after leaving
- [ ] A departed participant's identity cookie no longer authorizes participant actions (vote, comment, ready, create card, etc.) — the shared identity-check helper (Task 4) is updated to reject participants with `left_at` set
- [ ] Rejoining the same retro (same name) after leaving creates a new, distinct Participant row rather than reactivating the old one
- [ ] Leaving does not delete the retro's other data (cards/comments/actions from other participants are unaffected)
- [ ] Test: leaving deletes the participant's votes but not their cards/comments/actions
- [ ] Test: a departed participant's cookie is rejected by the shared identity-check helper for any participant action
- [ ] Test: rejoining after leaving produces a new Participant row distinct from the original

## 18. Railway deployment configuration
goal: Make the app deployable on Railway as a persistent ASGI process with Postgres and Redis attached.
description: Per the architecture doc's deployment section, add the configuration needed to deploy on Railway: a `Procfile` (or `railway.json`) that runs Daphne against `retro_tool.asgi:application` (not `runserver`, not gunicorn), a release/deploy step that runs `python manage.py migrate`, and settings that correctly pick up Railway's auto-injected `DATABASE_URL` and `REDIS_URL` env vars (building on Task 1's 12-factor settings). Document the required environment variables (`SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`) and confirm static files (Tailwind CSS output, if built at deploy time) are collected/served correctly under Daphne. This task is configuration/documentation plus a local smoke test of the production-like startup command — it does not require an actual Railway account/deploy to complete, but the configuration should be correct and ready to deploy.
acceptance_criteria:
- [ ] `Procfile` or `railway.json` defines a web process running `daphne -b 0.0.0.0 -p $PORT retro_tool.asgi:application`
- [ ] A release/deploy step runs `python manage.py migrate` before the web process starts (or is documented as Railway's release phase command)
- [ ] Settings correctly parse `DATABASE_URL` (Postgres) and `REDIS_URL` for the Channels layer without hardcoded fallbacks that would silently mask a missing env var in production
- [ ] `ALLOWED_HOSTS` and `SECRET_KEY` are required from environment in production (e.g. `DEBUG=False` path raises/fails fast if unset, rather than defaulting insecurely)
- [ ] Static files (including built Tailwind CSS) are collected via `collectstatic` and served correctly when running under Daphne locally with `DEBUG=False`
- [ ] A short deployment doc/section (README or `_docs/`) lists every required environment variable and what Railway auto-provides vs. what must be set manually
- [ ] Manual check: running `daphne -b 0.0.0.0 -p 8000 retro_tool.asgi:application` locally against a local Postgres+Redis (with `DEBUG=False` and env vars set) serves pages correctly, confirming the production startup path works
- [ ] Test: settings module raises a clear error (not a silent fallback) if `SECRET_KEY` or `DATABASE_URL` is missing while `DEBUG=False`

## 19. Triple review
goal: Run the project's local triple-review skill across the full codebase before considering the MVP backlog complete.
description: Once all preceding tasks are implemented and merged, run the local `code-review` skill (triple/ultra review mode) against the accumulated changes to catch correctness bugs, spec-compliance gaps against `_docs/weekly-retro-mvp.md`, and simplification/efficiency issues across the whole codebase. Address any CRITICAL/HIGH findings before considering the backlog done; document any accepted lower-severity findings with a rationale rather than silently ignoring them.
acceptance_criteria:
- [ ] The local triple-review skill has been run against the full set of changes from Tasks 1–18
- [ ] Every CRITICAL and HIGH severity finding has been fixed, with the fix verified (tests pass, behavior re-checked)
- [ ] Every MEDIUM/LOW finding has an explicit disposition recorded (fixed, or accepted with a one-line rationale) — none left silently unaddressed
- [ ] The full test suite passes after all review-driven fixes are applied
- [ ] A final pass confirms the implemented behavior matches `_docs/weekly-retro-mvp.md` section by section (§1 Create through §9 Deletion), flagging any drift discovered during review
- [ ] Review findings and dispositions are recorded somewhere durable (PR description, `_docs/` note, or commit messages) for future reference
