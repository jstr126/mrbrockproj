# Self-hosted Bolt Camera on an Ethernet/LAN Raspberry Pi

The Pi runs OpenCV and the fp32 ONNX model. The browser receives a reduced-size
MJPEG preview and JSON results; it does not load a model or use a cloud service.
The original 0.25-inch checkerboard detector handles scale and perspective.
Capture keeps one replaceable frame. Inference never accumulates a frame queue.

Automatic routing is locked to REVIEW because v3 has not met the requested
99% precision. `candidate_bin` is diagnostic only. There is no actuator control.
The API marks old results stale and never reuses an earlier result as a new
bolt decision. Streamed video can be newer than the last inspected frame.

## Start on a 64-bit Pi

From the copied project directory:

```bash
python3 -m venv .venv
.venv/bin/pip install -r pi_web/requirements.txt
.venv/bin/python -m pi_web.server --camera 0 --threads 2 --port 8080
```

Use a stable device path such as `/dev/v4l/by-id/...` with `--camera` when
multiple USB cameras are present. Add `--calib camera_calib.npz` for lens
calibration. The default model is `models/boltnet_v3.onnx`.

## Open it on other computers — no installation

Connect the Pi to the Ethernet LAN/router/switch, then open
`http://PI_LAN_IP:8080` from any computer on that network. The deployer prints
available addresses and their interface names. Use the Ethernet address.
Viewers need no ChatGPT account, model download, app, or SSH client. All assets
are served by the Pi. The camera stays connected to the Pi, so other browsers
also need no camera permission. Use a DHCP-enabled LAN for automatic network
address assignment; a direct cable without DHCP needs Pi-side network setup.

The default bind is `0.0.0.0`, making the read-only camera page visible on the
Pi's network interfaces. This does not configure router forwarding or public
internet hosting. SSH is used only to deploy and manage the server.

For optional encrypted access from outside the LAN:

```bash
ssh -N -L 8788:127.0.0.1:8080 USER@PI_HOST
# Open http://127.0.0.1:8788
```

Use `--bind 127.0.0.1` when starting the server or deployer if only SSH-tunnel
access is wanted. No client software is required for normal LAN viewing.

## Deploy from this project

```bash
python3 tools/deploy_pi.py USER@PI_HOST
```

The deployer first checks SSH access, the remote Python version and architecture.
It copies only runtime code, the self-hosted page and v3 ONNX; it does not copy
the training data or install torch. It creates an isolated virtual environment,
starts a user-owned server and checks `/api/health` on the Pi. It does not
change SSH configuration, firewall rules or router port forwards.

The camera must be connected to the Pi for this mode. If it is connected to
the computer instead, a separate browser-to-Pi capture transport is required.
The SSH address and camera location must be known before deployment.

## Local API smoke test without a camera

```bash
.venv/bin/python -m pi_web.server --test-image path/to/checkerboard-frame.jpg --port 8080
curl http://127.0.0.1:8080/api/health
```

The source is explicitly reported as `test image`. Synthetic input does not
measure Pi hardware latency or prove real-world 99% accuracy. For a permanent
boot-time service, install a systemd unit for the actual Pi account after
checking camera access and inference on that hardware.

## Use the public ChatGPT site as the viewer

Open https://bolt-camera-sorter.design-tech-9382.chatgpt.site and enter the
Pi address, for example `192.168.1.42:8080`, then click Connect to Pi.
The address is saved only in that browser. No local camera permission is used.
The Pi server must be installed and running first. The site cannot install it
without SSH access.

The server returns JPEG snapshots at `/frame.jpg` and current inspection JSON
at `/api/status`. CORS permits the exact hosted site origin by default; use
`--allow-origin https://YOUR-SITE-ORIGIN` to permit an additional viewer site.
The client requests local network access from a user click. Use a current
Chrome/Edge browser and allow its Local Network permission. Browsers without
local HTTP support can use an HTTPS Pi endpoint or open the Pi directly.
No browser security settings or flags need to be disabled.
