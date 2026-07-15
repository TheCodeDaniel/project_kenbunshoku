# Build prompts

The actual sequence of prompts used to build this project with Claude Code,
kept for transparency about process (this is an agentic-development track
submission, after all) and as a reusable script if the project needs
rebuilding or extending along the same lines.

A couple of notes on using these:

- If a step's output isn't working, iterate within that same numbered step
  before moving to the next — resist letting Claude Code "keep going" into
  the next component on a broken foundation.
- Anywhere it proposes something outside scope (weapon detection, an
  autonomous action), it should self-correct per `CLAUDE.md` — but call it
  out explicitly if it doesn't.

## 1. Edge service — local detection

> Read CLAUDE.md and edge-service/detector.py. Implement load_model() and
> watch_stream() using ultralytics YOLOv8n and opencv-python to pull frames
> from a stream URL and yield Detection objects for person-present frames
> above a confidence threshold. Keep it camera-agnostic — the stream URL is
> config, not hardcoded.

> Now implement edge-service/forwarder.py's forward_detection() to POST
> detections to CLOUD_INGEST_URL per the API contract in CLAUDE.md, with
> basic retry/backoff and a local fallback alert if the cloud is
> unreachable.

> Write a small test script to run detector.py against a live stream from
> my phone (IP Webcam on Android) and confirm detections are firing
> correctly before we move to the cloud side.

## 2. Cloud backend — ingestion + Qwen reasoning

> Read CLAUDE.md and cloud-backend/qwen_client.py. Implement
> classify_frame() to send the frame as a base64 image to a Qwen-VL model
> via the Qwen Cloud OpenAI-compatible API, using CLASSIFICATION_PROMPT,
> and parse the JSON response.

> Now implement cloud-backend/ingestion_api.py's /ingest endpoint
> end-to-end: read the uploaded frame, call classify_frame, and return the
> classification/reasoning. Get this working without memory or alerts yet
> — just detection in, classification out.

> Run cloud-backend locally with docker compose and confirm a full round
> trip: edge-service sends a detection, cloud-backend returns a Qwen
> classification.

## 3. Memory + alerts

> Implement cloud-backend/memory_store.py's record_visit() and
> get_pattern_context() against SQLite, per the schema and pattern logic
> described in the docstring.

> Implement cloud-backend/alert_dispatcher.py's build_alert_message() and
> dispatch_alert(). Wire memory_store and alert_dispatcher into the
> /ingest endpoint so a full request now returns classification + pattern
> context + whether an alert was sent.

> Simulate the same "visitor" appearing twice at a similar time and
> confirm the second visit gets recognized-pattern context instead of
> being treated as brand new.

## 4. Notification client

> Scaffold notification-client as a minimal Flutter app per its README —
> a Firebase Cloud Messaging (or ntfy.sh) listener that displays incoming
> alerts in a simple feed + detail view. Display only, no controls, per
> CLAUDE.md.

> Connect the notification client to a real alert sent from cloud-backend
> and confirm it renders the reasoning text correctly on my phone.

## 5. Deployment + proof

> Help me deploy cloud-backend to Alibaba Cloud ECS (or Function Compute
> if simpler) per cloud-backend/deploy/README.md. Walk me through
> provisioning and getting the Docker image running there.

> Now help me identify exactly what to screen-record and which code file
> to link as proof-of-Alibaba-Cloud-deployment, per the hackathon
> submission rules.

## 6. Submission polish

> Update the architecture diagram description and
> docs/PROJECT_DOCUMENTATION.md to reflect what was actually built vs.
> what was planned, and flag any drift from CLAUDE.md.

> Help me write the Devpost text description and README updates so
> someone unfamiliar with the project can understand and run it from the
> repo alone.
