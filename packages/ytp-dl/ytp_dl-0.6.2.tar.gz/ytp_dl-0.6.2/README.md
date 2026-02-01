# ytp-dl

> A lightweight YouTube downloader with an HTTP API

[![PyPI version](https://img.shields.io/pypi/v/ytp-dl.svg)](https://pypi.org/project/ytp-dl/)
[![Python Support](https://img.shields.io/pypi/pyversions/ytp-dl.svg)](https://pypi.org/project/ytp-dl/)
[![License](https://img.shields.io/pypi/l/ytp-dl.svg)](https://pypi.org/project/ytp-dl/)
[![Downloads](https://img.shields.io/pypi/dm/ytp-dl.svg)](https://pypi.org/project/ytp-dl/)

**ytp-dl** is a privacy-focused YouTube downloader that exposes a simple HTTP API for automated downloads.

---

## Features

* Smart quality selection (prefers 1080p H.264 + AAC when available; no transcoding needed)
* Audio downloads (extract audio as MP3)
* HTTP API (Flask-based API with concurrency controls)
* VPS-ready (includes an automated installer script for Ubuntu)

---

## Installation

```bash
pip install ytp-dl==0.6.2 yt-dlp[default]
```

**Requirements:**

* Linux operating system (tested on Ubuntu 24.04/25.04)
* FFmpeg (for handling audio + video)
* Deno (system-wide, required by yt-dlp for modern YouTube extraction)
* Python 3.8+

Notes:

* yt-dlp expects **Deno** to be available on `PATH` to run its JavaScript-based extraction logic.

---

## Using Your VPS

Once your VPS is running, you can download videos using simple HTTP requests:

### Download a Video (1080p MP4)

```bash
curl -X POST http://YOUR_VPS_IP:5000/api/download   -H "Content-Type: application/json"   -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'   --output video.mp4
```

### Download Audio Only (MP3)

```bash
curl -X POST http://YOUR_VPS_IP:5000/api/download   -H "Content-Type: application/json"   -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "extension": "mp3"}'   --output audio.mp3
```

### Download at Specific Resolution

```bash
curl -X POST http://YOUR_VPS_IP:5000/api/download   -H "Content-Type: application/json"   -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "resolution": 720}'   --output video.mp4
```

### Check Server Health

```bash
curl http://YOUR_VPS_IP:5000/healthz
```

Response example:

```json
{
  "ok": true,
  "in_use": 1,
  "capacity": 1
}
```

### Using from Python

```python
import requests

response = requests.post(
    "http://YOUR_VPS_IP:5000/api/download",
    json={
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "resolution": 1080,
        "extension": "mp4"
    },
    stream=True
)

if response.status_code == 200:
    with open("video.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
elif response.status_code == 503:
    print("Server busy, try again later")
else:
    print(f"Error: {response.json()}")
```

---

## Configuration

### Installation Script Variables

These environment variables configure the VPS installation (they can be overridden when running the script):

| Variable               | Description                          | Default            |
| ---------------------- | ------------------------------------ | ------------------ |
| `PORT`                 | API server port                      | `5000`             |
| `APP_DIR`              | Installation directory               | `/opt/ytp-dl`      |
| `YTPDL_MAX_CONCURRENT` | Max simultaneous downloads (API cap) | `1`                |

### Runtime Environment Variables

After installation, these variables control the API behavior. They are set in `/etc/default/ytp-dl-api` and can be edited manually:

| Variable               | Description                     | Default               |
| ---------------------- | ------------------------------- | --------------------- |
| `YTPDL_MAX_CONCURRENT` | Maximum concurrent downloads    | `1`                   |
| `YTPDL_VENV`           | Path to virtualenv for ytp-dl   | `/opt/ytp-dl/venv`    |

To change configuration after installation:

```bash
sudo nano /etc/default/ytp-dl-api
sudo systemctl restart ytp-dl-api
```

---

## Managing Your VPS Service

### View Service Status

```bash
sudo systemctl status ytp-dl-api
```

### View Logs

```bash
sudo journalctl -u ytp-dl-api -f
```

### Restart Service

```bash
sudo systemctl restart ytp-dl-api
```

### Stop/Start Service

```bash
sudo systemctl stop ytp-dl-api
sudo systemctl start ytp-dl-api
```

---

## API Reference

### POST `/api/download`

**Request Body:**

```json
{
  "url": "string (required)",
  "resolution": "integer (optional, default: 1080)",
  "extension": "string (optional, 'mp4' or 'mp3')"
}
```

**Response:**

* `200 OK` - File download stream
* `400 Bad Request` - Missing or invalid URL
* `500 Internal Server Error` - Download failed
* `503 Service Unavailable` - Server busy (max concurrent downloads reached)

### GET `/healthz`

**Response:**

```json
{
  "ok": true,
  "in_use": 1,
  "capacity": 1
}
```

---

## VPS Deployment

**What it does:**

* Installs Python and FFmpeg
* Installs Deno system-wide (required by yt-dlp for modern YouTube extraction)
* Creates a virtualenv at `/opt/ytp-dl/venv`
* Installs `ytp-dl==0.6.2` + `yt-dlp[default]` into the virtualenv
* Sets up a systemd service on port 5000
* Configures Gunicorn with gevent workers

```bash
#!/usr/bin/env bash
# VPS_Installation.sh - Minimal Ubuntu 24.04/25.04 setup for ytp-dl API
#
# What this does:
#   - Installs Python + ffmpeg
#   - Installs Deno system-wide (JS runtime required for modern YouTube extraction via yt-dlp)
#   - Creates a virtualenv at /opt/ytp-dl/venv
#   - Installs ytp-dl==0.6.2 + yt-dlp[default] + gunicorn + gevent in that venv
#   - Creates a simple systemd service ytp-dl-api.service on port 5000

set -euo pipefail

### --- Tunables -------------------------------------------------------------
PORT="${PORT:-5000}"                      # API listen port
APP_DIR="${APP_DIR:-/opt/ytp-dl}"         # app/venv root
VENV_DIR="${VENV_DIR:-${APP_DIR}/venv}"   # python venv

YTPDL_MAX_CONCURRENT="${YTPDL_MAX_CONCURRENT:-1}"     # API concurrency cap
### -------------------------------------------------------------------------

[[ "${EUID}" -eq 0 ]] || { echo "Please run as root"; exit 1; }
export DEBIAN_FRONTEND=noninteractive

echo "==> 1) Base packages"
apt-get update
apt-get install -yq --no-install-recommends \
  python3-venv python3-pip curl ffmpeg ca-certificates unzip

echo "==> 1.5) Install Deno (system-wide, for yt-dlp YouTube extraction)"
# Install into /usr/local/bin/deno so systemd PATH can see it.
# Official installer supports system-wide install via DENO_INSTALL=/usr/local.
if ! command -v deno >/dev/null 2>&1; then
  curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh
fi
deno --version

echo "==> 2) App dir & virtualenv"
mkdir -p "${APP_DIR}"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install "ytp-dl==0.6.2" "yt-dlp[default]" gunicorn gevent
deactivate

echo "==> 3) API environment file (/etc/default/ytp-dl-api)"
tee /etc/default/ytp-dl-api >/dev/null <<EOF
YTPDL_MAX_CONCURRENT=${YTPDL_MAX_CONCURRENT}
YTPDL_VENV=${VENV_DIR}
EOF

echo "==> 4) Gunicorn systemd service (ytp-dl-api.service on :${PORT})"
tee /etc/systemd/system/ytp-dl-api.service >/dev/null <<EOF
[Unit]
Description=Gunicorn for ytp-dl API (minimal)
After=network-online.target
Wants=network-online.target

[Service]
User=root
WorkingDirectory=${APP_DIR}
EnvironmentFile=/etc/default/ytp-dl-api
Environment=VIRTUAL_ENV=${VENV_DIR}
Environment=PATH=${VENV_DIR}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin

ExecStart=${VENV_DIR}/bin/gunicorn -k gevent -w 1 \
  --worker-connections 200 --timeout 0 --graceful-timeout 15 --keep-alive 20 \
  --bind 0.0.0.0:${PORT} scripts.api:app

Restart=always
RestartSec=3
LimitNOFILE=65535
MemoryMax=800M

[Install]
WantedBy=multi-user.target
EOF

echo "==> 5) Start and enable API service"
systemctl daemon-reload
systemctl enable --now ytp-dl-api.service

echo "==> 6) Quick status + health check"
systemctl status ytp-dl-api --no-pager || true

echo
echo "Waiting for API to start..."
sleep 3
echo "Health (local):"
curl -sS "http://127.0.0.1:${PORT}/healthz" || true

echo
echo "========================================="
echo "Installation complete!"
echo "API running on port ${PORT}"
echo "Test from outside: curl http://YOUR_VPS_IP:${PORT}/healthz"
echo "========================================="
```
