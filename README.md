# Project Kenbunshoku

A camera-agnostic security agent that turns any existing doorbell cam, webcam, or
IP camera into a system that understands _who's_ approaching, not just that
_something_ moved. Built for the Global AI Hackathon Series with Qwen Cloud
(Track 5: EdgeAgent).

- Detects people approaching via any connected camera
- Reasons about visitor context using Qwen Cloud (Qwen-VL)
- Remembers recurring visitor patterns over time
- Sends the homeowner a plain-language alert — **never takes action on its own**

See `CLAUDE.md` for full project context and constraints (this file doubles as
the spec Claude Code reads on every session). See `docs/` for the architecture
diagram, tech stack rationale (`docs/TECH_STACK.md`), and full write-up
(`docs/PROJECT_DOCUMENTATION.md`).

## Repo layout

| Folder                 | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| `camera-simulator/`    | Test harness — phone acting as an IP camera (not shipped)  |
| `edge-service/`        | Dockerized local person/motion detection                   |
| `cloud-backend/`       | FastAPI backend on Alibaba Cloud — Qwen-VL, memory, alerts |
| `notification-client/` | Flutter app, receives push alerts                          |
| `docs/`                | Architecture diagram, submission materials                 |
| `scripts/`             | Local dev orchestration                                    |

## Prerequisites

- Docker (for `edge-service` and `cloud-backend`)
- A Qwen Cloud API key (`QWEN_API_KEY` — from your Alibaba Cloud / DashScope
  account, see `docs/TECH_STACK.md`)
- An ntfy.sh topic name — any string works, pick something hard to guess
  since ntfy topics are public (e.g. `your-name-kenbunshoku-alerts`)
- A camera stream to point `edge-service` at — a real IP/doorbell cam's
  MJPEG/RTSP URL, or the phone-as-camera test rig in `camera-simulator/`
- Flutter (only if you want to run `notification-client/` — not needed to
  exercise `edge-service`/`cloud-backend` on their own)

## Running it locally

```bash
cp .env.example .env
# edit .env: fill in QWEN_API_KEY, set PUSH_ENDPOINT to https://ntfy.sh/<your-topic>,
# set STREAM_URL to your camera's stream URL (see camera-simulator/README.md
# if you don't have a real IP camera handy)

docker compose up
```

This brings up both `cloud-backend` (FastAPI on `:8000`) and `edge-service`
(YOLOv8n against `STREAM_URL`) together. `edge-service` will start forwarding
person detections to `cloud-backend` automatically once a person is
detected in-frame above the confidence threshold.

To exercise `cloud-backend` on its own, without a camera:

```bash
curl -X POST http://localhost:8000/ingest \
  -F "frame=@some-photo.jpg;type=image/jpeg" \
  -F "camera_id=test-cam" \
  -F "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

To see alerts land on a phone: run `notification-client/` (`flutter run -d
<device>`) with `--dart-define=NTFY_TOPIC=<your-topic>` matching whatever
you put in `.env`'s `PUSH_ENDPOINT`.

## Status

MVP complete and verified end-to-end, including on real hardware: live
YOLOv8n detections, a real Qwen-VL classification round trip, pattern
recognition on a repeat visitor, a real push alert delivered to a physical
phone, and `cloud-backend` deployed and verified live on Alibaba Cloud ECS.
See `docs/PROJECT_DOCUMENTATION.md` → "Status: as built vs. planned" for
specifics and known limitations, and `CLAUDE.md` → Build order for the
step list.

## License

MIT — see `LICENSE`.
