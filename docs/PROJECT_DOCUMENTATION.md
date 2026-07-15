# Kenbunshoku — Project Documentation

Full write-up: problem, solution, architecture, track alignment, ethics, and
future work. See `../CLAUDE.md` for the condensed, code-governing version of
this. The full-formatting Word versions (with the rendered architecture
diagram) are `Kenbunshoku_Project_Plan.docx`, `Kenbunshoku_Project_Documentation.docx`,
and `Kenbunshoku_Code_Implementation_Plan.docx`, shared separately outside the repo
(or add them under docs/ if you want them versioned too).

## Problem
Traditional cameras answer "was there motion?" not "should I care?" — causing
alert fatigue and after-the-fact-only awareness.

## Solution
Camera-agnostic ingestion → edge-level person/motion detection → Qwen-VL
context reasoning on Alibaba Cloud → pattern memory → plain-language,
human-in-the-loop alert.

## Track
Primary: EdgeAgent (Track 5). Supporting theme: pattern memory (MemoryAgent
spirit), not pitched as a second track.

## Ethics
No autonomous action. No weapon/threat detection in MVP. Motion-triggered
crops only, not continuous surveillance video. Framed as context/pattern
awareness, not crime prediction.

## Architecture
![architecture](architecture.png)
