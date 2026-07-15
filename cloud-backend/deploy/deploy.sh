#!/usr/bin/env bash
# Deploys cloud-backend to an already-provisioned Alibaba Cloud ECS instance.
# Provisioning the instance itself is a console step — see README.md — this
# script only handles getting the Docker image built and running on it.
#
# Prereqs:
#   - ECS instance running (Ubuntu 22.04+), public IP known, SSH key on hand
#   - Security group allows inbound TCP 22 and TCP 8000
#   - Repo pushed to GitHub (the box pulls from there rather than needing scp)
#   - .env populated at repo root (QWEN_API_KEY, QWEN_VL_MODEL, PUSH_ENDPOINT)
#
# Usage:
#   ./cloud-backend/deploy/deploy.sh <ecs-public-ip> <path-to-ssh-key> [ssh-user]

set -euo pipefail

HOST="${1:?usage: deploy.sh <ecs-public-ip> <ssh-key-path> [ssh-user]}"
KEY="${2:?usage: deploy.sh <ecs-public-ip> <ssh-key-path> [ssh-user]}"
SSH_USER="${3:-root}"

REPO_URL="https://github.com/TheCodeDaniel/project_kenbunshoku.git"
REMOTE_DIR="kenbunshoku-repo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "error: $ENV_FILE not found (copy .env.example and fill in QWEN_API_KEY etc.)" >&2
  exit 1
fi

echo "==> installing Docker and pulling latest code on $HOST"
ssh -i "$KEY" "$SSH_USER@$HOST" bash -s <<EOF
set -euo pipefail
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
if [ -d "$REMOTE_DIR" ]; then
  git -C "$REMOTE_DIR" pull
else
  git clone "$REPO_URL" "$REMOTE_DIR"
fi
EOF

echo "==> copying .env (kept off git, sent directly over SSH)"
scp -i "$KEY" "$ENV_FILE" "$SSH_USER@$HOST:$REMOTE_DIR/.env"

echo "==> building and (re)starting the container"
ssh -i "$KEY" "$SSH_USER@$HOST" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR/cloud-backend"
docker build -t kenbunshoku-cloud-backend .
docker rm -f kenbunshoku-cloud-backend 2>/dev/null || true
docker run -d --name kenbunshoku-cloud-backend --restart unless-stopped \
  -p 8000:8000 --env-file ../.env \
  kenbunshoku-cloud-backend
EOF

echo "==> done. Verify with: curl http://$HOST:8000/health"
