# Alibaba Cloud Deployment

This directory holds the deployment config for cloud-backend, and is also
where the hackathon's required "proof of Alibaba Cloud deployment" evidence
lives.

## Plan

- Target: Alibaba Cloud ECS instance (chosen over Function Compute — the
  existing Dockerfile runs as-is on a VM with zero repackaging, which matters
  more than serverless elegance given the deadline).
- Deploy the cloud-backend Docker image via `deploy.sh` (see below).
- Record a short screen capture (separate from the 3-min demo video) showing
  the backend actually running on Alibaba Cloud.
- Link a code file in this repo that clearly shows Alibaba Cloud service/API
  usage, as required by the submission rules: `cloud-backend/qwen_client.py`
  (its `base_url` targets `dashscope-intl.aliyuncs.com`, Alibaba Cloud's
  Model Studio / DashScope API — this is the Qwen-VL call, not a generic
  OpenAI proxy) alongside this deploy config.

## Provisioning (ECS console — one-time, manual)

1. Log into the [ECS console](https://ecs.console.aliyun.com) with the
   hackathon voucher / free-trial account.
2. Create Instance → **Pay-As-You-Go** (draws from voucher credit).
3. Region: `ap-southeast-1` (Singapore) is a safe default with good
   `dashscope-intl` latency; pick whichever region your voucher covers.
4. Instance type: smallest general-purpose instance that covers 2GB+ RAM
   (e.g. `ecs.t6-c1m2.large` or `ecs.e-c1m1.large`) — no GPU needed, YOLO
   runs on the edge box, not here.
5. Image: Ubuntu 22.04 64-bit (public image).
6. Storage: default system disk is enough.
7. Networking: assign a public IP.
8. Security group: allow inbound TCP 22 (SSH) and TCP 8000 (the `/ingest`
   API) — restrict source IPs if you can.
9. Key pair: create one, download the private key, `chmod 400` it locally.
10. Launch, wait for "Running", note the public IP.

## Deploying the image

Once the instance is up and the repo is pushed to GitHub:

```bash
./cloud-backend/deploy/deploy.sh <ecs-public-ip> <path-to-ssh-key> [ssh-user]
```

This installs Docker on the box if missing, pulls the repo, copies the local
`.env` over SSH (kept off git the whole way), builds the image, and runs it
with `--restart unless-stopped`. Verify with:

```bash
curl http://<ecs-public-ip>:8000/health
```

## TODO

- [ ] Provision ECS instance (console steps above)
- [ ] Run `deploy.sh` against it
- [ ] Record proof-of-deployment clip
- [ ] Link this file + `qwen_client.py` + the recording in the Devpost submission
