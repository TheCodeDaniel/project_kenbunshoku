"""
Manual test harness: run edge-service's detector against a live phone stream
and print detections as they fire, before wiring up the cloud side.

Not shipped — see README.md. Depends on edge-service's requirements
(ultralytics, opencv-python-headless), so run it from an environment that has
those installed, e.g.:

    pip install -r ../edge-service/requirements.txt
    python test_detector.py --stream-url http://<phone-ip>:8080/video

Stop with Ctrl+C; it prints a summary of how many detections fired.
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "edge-service"))

from detector import load_model, watch_stream  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stream-url",
        default=os.environ.get("STREAM_URL", "http://192.168.1.100:8080/video"),
        help="MJPEG/RTSP stream URL (default: $STREAM_URL, e.g. phone's IP Webcam address)",
    )
    parser.add_argument("--camera-id", default=os.environ.get("CAMERA_ID", "test-cam-1"))
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument(
        "--save-dir",
        default=None,
        help="If set, save each detected frame as a .jpg here for visual confirmation",
    )
    args = parser.parse_args()

    if args.save_dir:
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)

    print("Loading YOLOv8n...")
    model = load_model()

    print(f"Watching {args.stream_url} (camera_id={args.camera_id}, "
          f"confidence>={args.confidence}). Ctrl+C to stop.")

    count = 0
    start = time.monotonic()
    try:
        for detection in watch_stream(
            args.stream_url, args.camera_id, model=model, confidence_threshold=args.confidence
        ):
            count += 1
            elapsed = time.monotonic() - start
            print(
                f"[{count}] t={elapsed:6.1f}s confidence={detection.confidence:.2f} "
                f"timestamp={detection.timestamp}"
            )
            if args.save_dir:
                out_path = Path(args.save_dir) / f"detection_{count:04d}.jpg"
                out_path.write_bytes(detection.frame_bytes)
                print(f"    saved {out_path}")
    except KeyboardInterrupt:
        pass

    elapsed = time.monotonic() - start
    print(f"\nStopped after {elapsed:.1f}s — {count} detection(s) fired.")


if __name__ == "__main__":
    main()
