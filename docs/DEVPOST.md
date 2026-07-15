# Devpost submission text

Draft for the Devpost form fields. Copy/paste per section; trim if the form
has stricter length limits than expected.

## Inspiration

Doorbell and IP cameras all answer the same narrow question — "was there
motion?" — not the one that actually matters to a homeowner: "should I care
about this?" That gap is why camera apps train people to ignore push alerts
entirely. Kenbunshoku ("the art of perceiving," 見聞色) tries to close that
gap by adding a layer of visitor *context*, without ever taking the decision
out of the homeowner's hands.

## What it does

Any existing doorbell/IP camera streams video → an edge service does local
person detection (YOLOv8n) → cropped, motion-triggered frames go to a cloud
backend on Alibaba Cloud → Qwen-VL reasons about visitor context (familiar /
delivery-like / anomalous, with a plain-language explanation) → a memory
store checks whether this is a recurring pattern (same visitor, similar time
of day) → the homeowner gets a push notification with the reasoning attached.
Recognized, low-priority recurring patterns (e.g. the same delivery courier
at the same time each week) are logged but not re-pushed, to cut alert
fatigue deliberately rather than silently.

The system never takes autonomous action. It informs; the human decides.

## How we built it

- **`edge-service/`** — Python, YOLOv8n (ultralytics), OpenCV, Docker. Reads
  frames from any camera stream URL (RTSP/MJPEG/device index — config, not
  hardcoded), yields person-present detections above a confidence threshold.
- **`cloud-backend/`** — FastAPI, deployed on Alibaba Cloud ECS. Calls
  Qwen-VL (`qwen-vl-plus`) via the OpenAI-compatible Qwen Cloud API
  (`dashscope-intl.aliyuncs.com`), stores visit history in SQLite, decides
  whether to push based on classification + recognized-pattern context.
- **`notification-client/`** — Flutter, listening on an ntfy.sh topic
  (free tier, zero backend setup). Display-only feed + detail view.
- **Deployment** — Alibaba Cloud ECS, Singapore region, Docker.

## Challenges we ran into

- An em dash in a push notification's `Title` header crashed the request
  outright — HTTP headers must be ASCII/latin-1, and that only showed up
  once we actually sent a real alert, not from reading the code.
- macOS's App Sandbox silently blocked all outbound network requests from
  the notification client until we added the `network.client` entitlement;
  Android needed an explicit `INTERNET` permission too. Neither gap was
  visible from `flutter analyze` — only from actually running the app.
- Getting a repeat-visitor test to be deterministic meant isolating the
  pattern-matching test from Qwen-VL's real (slightly nondeterministic)
  classification output, and from wall-clock "now" — `get_pattern_context`
  needed the visit's own timestamp, not the server's.

## Accomplishments that we're proud of

Every layer was verified against something real, not just unit-tested:
real YOLOv8n detections against a live phone camera stream, a real
classification round trip through Qwen-VL, a simulated repeat visitor whose
2nd visit correctly triggered pattern recognition and alert suppression, a
real push alert rendered on a physical Android phone, and `cloud-backend`
deployed and verified live on Alibaba Cloud ECS — including catching and
fixing three real bugs (the header crash and both sandbox/permission gaps)
that would otherwise have shipped silently broken.

## What we learned

That "it compiles" and "it analyzes cleanly" are a long way from "it works"
— every real bug found this build came from actually running the thing on
real hardware against a real network, not from static analysis.

## What's next

Real OS-level background push (current notification client holds a
foreground connection to ntfy.sh, which is fine for a demo, not for daily
use), TLS on the ingestion endpoint, and richer pattern memory beyond the
current time-of-day heuristic. Explicitly *not* next: weapon/threat
detection or any autonomous action — both are deliberate, permanent scope
cuts, not gaps to fill later.

## Built with

Python, FastAPI, ultralytics YOLOv8n, OpenCV, Qwen-VL (Qwen Cloud /
DashScope), SQLite, Flutter, Dart, Docker, ntfy.sh, Alibaba Cloud ECS.
