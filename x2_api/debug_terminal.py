#!/usr/bin/env python3
"""X2 Debug Terminal — Web monitoring dashboard for robot services."""

import glob
import json
import os
import subprocess
import time
from flask import Flask, Response, jsonify, send_file

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEBUG_PORT = 9090
DEBUG_HOST = "0.0.0.0"
SERVICES = [
    "agibot_software.service",
    "x2-motion-api.service",
    "x2-mqtt-client.service",
]
SERVICE_NAMES = [s.replace(".service", "") for s in SERVICES]
REST_API_BASE = "http://127.0.0.1:8080/api/v1"
API_KEY = os.environ.get("X2_API_KEY", "x2-dev-key-change-me")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(path, default=""):
    try:
        with open(path) as f:
            return f.read().strip()
    except (OSError, IOError):
        return default


def _run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _parse_meminfo():
    info = {}
    for line in _read_file("/proc/meminfo").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            info[parts[0].rstrip(":")] = int(parts[1]) * 1024  # kB -> bytes
    total = info.get("MemTotal", 1)
    available = info.get("MemAvailable", 0)
    return {
        "total": total,
        "available": available,
        "used": total - available,
        "percent": round((total - available) / total * 100, 1),
    }


def _parse_disk():
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bavail
        used = total - free
        return {
            "total": total,
            "used": used,
            "free": free,
            "percent": round(used / total * 100, 1) if total else 0,
        }
    except OSError:
        return None


def _parse_temperatures():
    temps = []
    for zone in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        name = _read_file(os.path.join(zone, "type"), "unknown")
        raw = _read_file(os.path.join(zone, "temp"))
        if raw:
            try:
                temps.append({"zone": name, "temp_c": round(int(raw) / 1000, 1)})
            except ValueError:
                pass
    return temps


def _parse_gpu():
    # Try multiple known GPU sysfs paths (varies by Jetson model)
    gpu_load_paths = [
        "/sys/devices/platform/bus@0/17000000.gpu/load",  # Orin NX
        "/sys/devices/gpu.0/load",                        # older Jetson
    ]
    load_raw = None
    for p in gpu_load_paths:
        load_raw = _read_file(p)
        if load_raw:
            break
    if not load_raw:
        return None
    try:
        load_pct = round(int(load_raw) / 10, 1)
    except ValueError:
        return None
    freq_raw = _read_file("/sys/devices/platform/bus@0/17000000.gpu/devfreq/17000000.gpu/cur_freq")
    if not freq_raw:
        freq_raw = _read_file("/sys/devices/gpu.0/devfreq/17000000.gpu/cur_freq")
    freq_mhz = round(int(freq_raw) / 1_000_000, 1) if freq_raw else None
    return {"load_percent": load_pct, "freq_mhz": freq_mhz}


def _parse_uptime():
    raw = _read_file("/proc/uptime")
    if raw:
        return float(raw.split()[0])
    return None


def _format_bytes(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    html_path = os.path.join(os.path.dirname(__file__), "debug_terminal.html")
    return send_file(html_path)


@app.route("/api/metrics")
def api_metrics():
    try:
        load = os.getloadavg()
    except OSError:
        load = (0, 0, 0)

    cpu_count = os.cpu_count() or 1

    return jsonify({
        "load_avg": {"1m": load[0], "5m": load[1], "15m": load[2]},
        "cpu_count": cpu_count,
        "memory": _parse_meminfo(),
        "disk": _parse_disk(),
        "gpu": _parse_gpu(),
        "temperatures": _parse_temperatures(),
        "uptime_sec": _parse_uptime(),
    })


@app.route("/api/services")
def api_services():
    results = []
    for svc in SERVICES:
        props = (
            "ActiveState,SubState,MainPID,MemoryCurrent,"
            "ExecMainStartTimestamp,Description"
        )
        raw = _run(["systemctl", "show", svc, f"--property={props}", "--no-pager"])
        info = {"name": svc}
        for line in raw.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k] = v
        # Convert MemoryCurrent to int
        try:
            info["MemoryCurrent"] = int(info.get("MemoryCurrent", 0))
        except (ValueError, TypeError):
            info["MemoryCurrent"] = 0
        try:
            info["MainPID"] = int(info.get("MainPID", 0))
        except (ValueError, TypeError):
            info["MainPID"] = 0
        results.append(info)
    return jsonify(results)


@app.route("/api/robot")
def api_robot():
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{REST_API_BASE}/robot/state",
            headers={"X-API-Key": API_KEY},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return jsonify(json.loads(resp.read()))
    except Exception as e:
        return jsonify({"error": f"API unreachable: {e}"}), 503


@app.route("/api/processes")
def api_processes():
    raw = _run(["ps", "aux", "--sort=-rss"], timeout=3)
    lines = raw.splitlines()
    if not lines:
        return jsonify([])
    procs = []
    for line in lines[1:16]:  # top 15
        parts = line.split(None, 10)
        if len(parts) >= 11:
            procs.append({
                "user": parts[0],
                "pid": parts[1],
                "cpu": parts[2],
                "mem": parts[3],
                "rss": parts[5],
                "command": parts[10][:120],
            })
    return jsonify(procs)


@app.route("/api/network")
def api_network():
    # Interfaces
    interfaces = []
    raw = _run(["ip", "-j", "addr", "show"], timeout=3)
    if raw:
        try:
            for iface in json.loads(raw):
                addrs = []
                for a in iface.get("addr_info", []):
                    addrs.append(f"{a.get('local', '')}/{a.get('prefixlen', '')}")
                interfaces.append({
                    "name": iface.get("ifname", ""),
                    "state": iface.get("operstate", ""),
                    "addresses": addrs,
                })
        except (json.JSONDecodeError, KeyError):
            pass

    # RX/TX from /proc/net/dev
    traffic = {}
    for line in _read_file("/proc/net/dev").splitlines()[2:]:
        parts = line.split()
        if len(parts) >= 10:
            name = parts[0].rstrip(":")
            traffic[name] = {
                "rx_bytes": int(parts[1]),
                "tx_bytes": int(parts[9]),
            }

    # Internet check
    internet = _run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], timeout=3)
    online = "1 received" in internet

    return jsonify({
        "interfaces": interfaces,
        "traffic": traffic,
        "internet": online,
    })


@app.route("/api/mqtt-status")
def api_mqtt_status():
    active = _run(["systemctl", "is-active", "x2-mqtt-client.service"])
    # Parse recent logs for key events
    raw = _run([
        "journalctl", "-u", "x2-mqtt-client.service",
        "-n", "30", "--no-pager", "-o", "short-iso",
    ], timeout=3)
    last_connected = None
    last_published = None
    last_received = None
    for line in raw.splitlines():
        lower = line.lower()
        if "connected" in lower and "disconnect" not in lower:
            last_connected = line
        if "published" in lower or "heartbeat" in lower:
            last_published = line
        if "received" in lower or "command" in lower:
            last_received = line

    return jsonify({
        "active": active,
        "last_connected": last_connected,
        "last_published": last_published,
        "last_received": last_received,
    })


@app.route("/stream/logs/<service>")
def stream_logs(service):
    # Validate service name
    if service not in SERVICE_NAMES:
        return jsonify({"error": f"Unknown service: {service}"}), 404

    svc_unit = service + ".service"

    def generate():
        proc = subprocess.Popen(
            ["journalctl", "-u", svc_unit, "-f", "-n", "150",
             "--no-pager", "-o", "short-iso"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            for line in proc.stdout:
                data = json.dumps({"line": line.rstrip()})
                yield f"data: {data}\n\n"
        except GeneratorExit:
            pass
        finally:
            proc.terminate()
            proc.wait(timeout=2)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"X2 Debug Terminal starting on http://{DEBUG_HOST}:{DEBUG_PORT}")
    app.run(host=DEBUG_HOST, port=DEBUG_PORT, threaded=True)
