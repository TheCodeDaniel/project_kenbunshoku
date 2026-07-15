# Alibaba Cloud Deployment

This directory holds the deployment config for cloud-backend, and is also
where the hackathon's required "proof of Alibaba Cloud deployment" evidence
lives.

## Plan

- Target: Alibaba Cloud ECS instance (or Function Compute, if a serverless
  fit turns out cleaner for the ingestion endpoint).
- Deploy the cloud-backend Docker image.
- Record a short screen capture (separate from the 3-min demo video) showing
  the backend actually running on Alibaba Cloud.
- Link a code file in this repo (this deploy config) that clearly shows
  Alibaba Cloud service/API usage, as required by the submission rules.

## TODO

- [ ] Provision ECS instance / Function Compute
- [ ] Deploy cloud-backend image
- [ ] Set QWEN_API_KEY and PUSH_ENDPOINT as environment secrets (never commit these)
- [ ] Record proof-of-deployment clip
- [ ] Link this file + the recording in the Devpost submission
