# Camera Simulator (test harness — not shipped)

Not production code. This is just how the phone stands in for a real doorbell
cam / IP camera during MVP testing, so edge-service never has to be written or
tested any differently than it would be against real hardware.

## Android (Samsung S22)

1. Install **IP Webcam** (free, F-Droid/Play Store).
2. Start server; it exposes an MJPEG stream, typically at
   `http://<phone-ip>:8080/video`.
3. Point `edge-service`'s `STREAM_URL` env var at that address.

## iOS (iPhone 12)

1. Install a free RTSP-broadcast app (evaluate options at build time — several
   free ones exist; pick whichever has the least friction).
2. If no reliable free RTSP option is found, fall back to periodic still-frame
   capture over HTTP (e.g. a simple Shortcuts automation posting a frame every
   N seconds to a local endpoint) — lower fidelity but sufficient for testing
   the classification pipeline.

## Why this matters

`edge-service` and everything downstream must never hardcode assumptions about
this being a phone. The stream URL is the only integration point — swapping in
a real doorbell cam later should require a config change, not a code change.
