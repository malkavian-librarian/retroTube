# Weekly Retro Tool — MVP Specification

## Core Concept

A lightweight, accountless, real-time retrospective tool for small trusted teams. Each retro is standalone and accessed through a private link + PIN.

**Core flow:**

`Create → Join → Write → Ready → Reveal → Blind Vote → Results → Discuss → Actions → Close`

## 1. Create

Anyone can create a standalone retro with:

- Retro name
- Optional description
- Soft participant limit
- Creator-defined PIN

No projects. No accounts. No persistent dashboard.

## 2. Join

Participants open the private link, enter the PIN and their name, then explicitly **Join Retro**.

Identity is remembered in that browser. Cross-device recovery is out of scope. Joining closes after Reveal.

## 3. Write

Three fixed columns:

- **Went well**
- **Didn't go well**
- **Ideas**

Cards show their authors after Reveal. During Writing, participants only see their own cards. Authors can edit/delete them.

Participants mark themselves **Ready**. When everyone is ready, cards automatically Reveal. Anyone can force Reveal with confirmation.

## 4. Reveal & Group

After Reveal:

- No new cards.
- Existing cards cannot be edited/deleted.
- Authors can move their own cards between columns.
- Anyone can group similar cards within the same column.
- Grouped cards retain their individual text + authors.

## 5. Blind Voting

Each participant gets **up to 5 votes**, maximum one per card. Self-voting is allowed.

Vote totals and voters are hidden during voting.

Participants can change votes until clicking **Done voting**. Done is irreversible. When everyone finishes, results reveal automatically. Anyone can force-end voting.

Afterwards everyone sees:

- Vote count
- Names of voters
- Ranking

## 6. Discussion & Actions

Discussion unlocks **after voting**.

Each card supports simple flat comments.

Anyone can create an action:

- From a feedback card, or
- Independently

Action = **description + participant owner**.

Anyone can edit/delete/reassign actions before closing. No due dates, status tracking or acceptance workflow.

## 7. Close

Any participant can close the retro after voting, with confirmation.

Closed retro becomes read-only and shows:

- Original board
- Overall top feedback
- Rankings within each category
- Comments
- Action items

Summary can be **copied to clipboard**.

## 8. Collaboration

Everything updates in real time.

Optional shared timer can be started, paused, resumed or reset by anyone. Timer expiry is informational only.

Participants can leave; their cards remain but their votes are removed. Rejoining creates a new identity.

## 9. Deletion

Closed retros persist indefinitely.

Any participant can permanently delete the retro by **typing its name to confirm**.

## Explicitly Out of MVP

- Accounts
- Authentication
- Project/workspace dashboards
- Recurring retros
- Email notifications
- Integrations (Slack/Jira/etc.)
- AI summaries
- PDF export
- Action-status tracking
- Due dates
- Threaded comments
- Moderation
- Cross-device identity recovery
- Custom retro templates/categories
- Analytics
- Historical comparison
