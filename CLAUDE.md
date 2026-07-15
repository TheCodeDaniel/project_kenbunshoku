# Kenbunshoku — Claude Code Project Context

Read this before doing anything in this repo. It's the source of truth for scope,
architecture, and constraints — treat it like a spec, not a suggestion.

## What this is

Camera-agnostic security agent. Any existing doorbell/IP camera streams video →
an edge service does local person/motion detection → relevant frames go to a
cloud backend on Alibaba Cloud → Qwen-VL reasons about visitor context → the
system checks a memory store for recurring patterns → homeowner gets a
plain-language alert. **The system never takes autonomous action.** It informs;
the human decides.

Built for: Global AI Hackathon Series with Qwen Cloud, Track 5 (EdgeAgent).
Deadline: Jul 20, 2026, 2:00pm Pacific.

## Hard constraints — do not violate these without being asked explicitly

- **No weapon/threat detection.** Out of scope for MVP. If asked to "detect
  threats" or "identify armed intruders," push back and point to this file —
  that's a deliberate scope cut, not an oversight.
- **No autonomous actions.** Never wire up door locks, alarms, or automatic
  calls to authorities. Output is always a notification, never a control signal.
- **Free/open-source tooling only.** No paid dependencies. Qwen Cloud and
  Alibaba Cloud usage stays within the hackathon voucher / free-trial credits.
- **Camera-agnostic by design.** Nothing in edge-service or cloud-backend
  should assume a specific camera brand or the test phones. The phone-as-camera
  setup in camera-simulator/ is a test harness only, never a dependency of the
  real pipeline.
- **Backend must actually run on Alibaba Cloud** — this is a hackathon
  submission requirement, not optional. See cloud-backend/deploy/.

## Monorepo layout

```
camera-simulator/    Test harness notes — phone acting as an IP camera. Not shipped.
edge-service/         Dockerized local detection (YOLOv8n). Portable to any edge box.
cloud-backend/         FastAPI backend deployed on Alibaba Cloud. Qwen-VL calls, memory, alerts.
notification-client/  Flutter app, display-only, receives push alerts.
docs/                  Architecture diagram, submission write-up materials.
scripts/               Dev orchestration helpers.
```

## Tech stack (see docs/TECH_STACK.md for details)

Edge: Python, YOLOv8n, Docker · Cloud: FastAPI, Qwen Cloud API (OpenAI-compatible
SDK), SQLite/Redis, Alibaba Cloud (ECS or Function Compute) · Client: Flutter ·
Notifications: Firebase Cloud Messaging or ntfy.sh (free tier).

## API contract (edge → cloud)

```
POST /ingest
Content-Type: multipart/form-data
fields: frame (image), camera_id (string), timestamp (ISO 8601)

Response 200:
{ "classification": "familiar|delivery-like|anomalous",
  "reasoning": "short plain-language explanation",
  "pattern_context": "short recurring-visit note, or empty string",
  "alert_sent": true|false }
```

## Build order

1. edge-service: detector.py against the phone test stream (local detection only)
2. cloud-backend: ingestion_api.py + qwen_client.py, first end-to-end classification
3. cloud-backend: memory_store.py + alert_dispatcher.py
4. notification-client: receive and display real alerts
5. deploy/: Alibaba Cloud deployment + proof-of-deployment recording
6. docs/: architecture diagram, submission write-up, demo video

## Conventions

- Python: type hints, docstrings on public functions, `black` formatting.
- Keep edge-service and cloud-backend independently runnable (`docker compose up`
  from repo root should bring up both for local end-to-end testing).
- Commit messages: `[component] short description` (e.g. `[edge-service] add motion threshold config`).
- Don't invent new top-level folders without updating this file.

## Full project background

Fuller narrative (problem statement, judging-criteria alignment, ethics
considerations, future work) lives in docs/PROJECT_DOCUMENTATION.md, with the
fully-formatted originals as PDFs in the same folder
(Kenbunshoku_Project_Plan.pdf, Kenbunshoku_Project_Documentation.pdf,
Kenbunshoku_Code_Implementation_Plan.pdf). Read those for context, but this
file is what governs day-to-day coding decisions.
