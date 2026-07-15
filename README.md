# Kenbunshoku

A camera-agnostic security agent that turns any existing doorbell cam, webcam, or
IP camera into a system that understands *who's* approaching, not just that
*something* moved. Built for the Global AI Hackathon Series with Qwen Cloud
(Track 5: EdgeAgent).

- Detects people approaching via any connected camera
- Reasons about visitor context using Qwen Cloud (Qwen-VL)
- Remembers recurring visitor patterns over time
- Sends the homeowner a plain-language alert — **never takes action on its own**

See `CLAUDE.md` for full project context and constraints (this file doubles as
the spec Claude Code reads on every session). See `docs/` for the architecture
diagram and full write-up.

## Repo layout

| Folder | Purpose |
|---|---|
| `camera-simulator/` | Test harness — phone acting as an IP camera (not shipped) |
| `edge-service/` | Dockerized local person/motion detection |
| `cloud-backend/` | FastAPI backend on Alibaba Cloud — Qwen-VL, memory, alerts |
| `notification-client/` | Flutter app, receives push alerts |
| `docs/` | Architecture diagram, submission materials |
| `scripts/` | Local dev orchestration |

## Local dev

```bash
docker compose up
```

Brings up `edge-service` and `cloud-backend` together for local end-to-end
testing before anything is deployed to Alibaba Cloud.

## Status

MVP in progress — see `CLAUDE.md` → Build order.

## License

MIT — see `LICENSE`.
