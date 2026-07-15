# Tech Stack

Concrete choices behind the summary line in `CLAUDE.md`. Each one below was a
fork where more than one free/open-source option fit — this records which
was picked and why, so the choice doesn't need re-litigating later.

## Edge (`edge-service/`)

- **Python 3.11**, `black` formatting, type hints.
- **ultralytics YOLOv8n** for person detection — smallest YOLOv8 variant,
  runs fine on CPU, open weights (no paid tier).
- **opencv-python-headless** for stream capture (`cv2.VideoCapture`) and
  JPEG encoding — headless because the container has no display, and we
  never call any GUI function (`imshow`, etc.).
- **Docker** (`python:3.11-slim` base) — portable to any edge box, not tied
  to the phone-based test rig in `camera-simulator/`.

## Cloud (`cloud-backend/`)

- **FastAPI** + **uvicorn** — the `/ingest` endpoint.
- **Qwen Cloud** via the **OpenAI-compatible SDK** (`openai` package),
  pointed at `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.
  Model: `qwen-vl-plus` (overridable via `QWEN_VL_MODEL`) — the cheaper
  VL-capable Qwen model, sufficient for visitor-context classification.
- **SQLite** (stdlib `sqlite3`) for `memory_store.py` — an MVP-simple visit
  log, not Redis; concurrent-write contention isn't a real concern at this
  scale, and it needs zero extra infra.
- **requests** for the outbound push to the notification service.

## Notifications

- **ntfy.sh** (free tier), not Firebase Cloud Messaging — resolves the
  "Firebase Cloud Messaging or ntfy.sh" choice left open in the original
  plan. Picked because it needs zero backend setup (no Firebase project,
  no `google-services.json`/`GoogleService-Info.plist`, no APNs certs) —
  the deciding factor was hackathon time, not a technical requirement.
  `alert_dispatcher.py`'s `PUSH_ENDPOINT` is just an ntfy.sh topic URL;
  swapping to FCM later would mean changing that module's POST shape, not
  the surrounding architecture.

## Client (`notification-client/`)

- **Flutter**, `http` package only — no state-management library, no
  `flutter_local_notifications`. The client holds a live HTTP connection to
  ntfy.sh's `/<topic>/json` stream (not a true OS-level background push);
  that's an intentional MVP scope cut, see "Known limitations" in
  `PROJECT_DOCUMENTATION.md`.

## Deployment

- **Alibaba Cloud ECS** (not Function Compute) — the existing Dockerfile
  runs on a VM with zero repackaging, which mattered more than serverless
  elegance given the deadline. See `cloud-backend/deploy/README.md`.
- Region **ap-southeast-1 (Singapore)**, Ubuntu 22.04, free-trial instance
  (`ecs.e-c1m2.large`, 2 vCPU/4GiB) — well under the trial's $0.25/hr cap.
