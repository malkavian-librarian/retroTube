# Process

How work on this repo is tracked and how to pick up a task, for anyone (or any agent) joining cold.

## Where tasks live

Tasks are **GitHub issues**, not `_docs/tasks.md` (that file is the original backlog draft — the issues in the repo are the source of truth going forward; if the two ever disagree, the issue wins).

Repo: [`malkavian-librarian/retroTube`](https://github.com/malkavian-librarian/retroTube) — see the [Issues tab](https://github.com/malkavian-librarian/retroTube/issues).

Each issue follows the same shape:

- **Goal** — one-line summary of the outcome
- **Description** — 3-5 sentences of context on the work needed
- **Acceptance Criteria** — a checklist of everything that must be true for the task to be done

## How to work an issue

Work **one issue at a time**, start to finish, before picking up the next one.

1. **Read the acceptance criteria before starting.** They're the actual spec for the task — more precise than the description. If something in the description conflicts with an acceptance criterion, the criterion wins. If the criteria seem to require something out of scope for this task (e.g. touching another app/model), stop and flag it rather than silently expanding scope.
2. Check `_docs/arch.md` and `_docs/weekly-retro-mvp.md` (see below) for any context the issue references but doesn't repeat.
3. Implement the task. Don't implement ahead of the current issue — later issues assume earlier ones landed, not the reverse.
4. **Read the acceptance criteria again before closing.** Go down the checklist item by item and confirm each one is actually true (tests pass, the behavior is verified, not just "probably fine"). Check off each box in the issue as you confirm it.
5. Close the issue only once every box is checked. If a criterion turns out to be wrong or no longer applicable, say so in the issue rather than quietly checking it off.

## Commit regularly

Commit as you complete meaningful chunks of a task — not one giant commit at the end of an issue. Each commit should leave the repo in a working state (tests passing). Reference the issue number in the commit message (e.g. `Add Retro model and PIN hashing (#2)`) so history stays traceable back to the issue.

## Other files in `_docs/`

| File | Purpose |
|---|---|
| `weekly-retro-mvp.md` | Product spec — what the app does, section by section (Create, Join, Write, Reveal, Vote, Discuss, Actions, Close, Deletion). Read this to understand *behavior*. |
| `arch.md` | Architecture reference — stack choices, Django app layout, data model sketches, the realtime event contract, coding standards, deployment notes. Read this to understand *how it's built*. |
| `tasks.md` | The original backlog draft the GitHub issues were generated from. Superseded by the issues themselves (see above) — kept for historical reference, don't treat it as current status. |
| `process.md` | This file. |
| `testing-guidelines.md` *(not yet created)* | Will describe how tests are structured and what's expected per task (unit vs. integration, fixtures, what "done" looks like for test coverage). Until it exists, follow `arch.md`'s testing note (pytest-django, one test per hard-numbered rule) and each issue's own acceptance criteria. |
| `design-system.md` *(not yet created)* | Will define shared UI conventions (Tailwind tokens, component patterns, spacing/typography) so the interface doesn't drift session to session. Until it exists, match whatever visual patterns already exist in the templates rather than inventing new ones per task. |
| `api.md` *(not yet created)* | Will describe the shape of any HTTP/WebSocket endpoints (request/response formats, the Channels event vocabulary). Until it exists, follow the realtime event contract in `arch.md` and keep new endpoints consistent with whatever the current codebase already does. |

If one of the not-yet-created files above would materially help with a task and doesn't exist yet, flag it rather than guessing at conventions — creating it may be worth its own issue.
