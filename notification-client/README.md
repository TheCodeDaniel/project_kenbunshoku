# Notification Client (Flutter)

Minimal Flutter app that receives push notifications and displays the agent's
reasoning in plain language. **Display only** — no control actions exposed, by
design (see CLAUDE.md).

## Setup (not yet scaffolded)

```bash
flutter create . --project-name kenbunshoku_notify
# add firebase_messaging or an ntfy.sh client, per whichever push
# service cloud-backend/alert_dispatcher.py is configured to use
```

## Screens (MVP)

- Alert feed: list of past alerts (timestamp, classification, reasoning)
- Alert detail: full reasoning text for a single alert
- No settings/controls beyond notification preferences — intentionally thin
