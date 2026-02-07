import os
import sys
import json
import time
import socket
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / "venv" / "Scripts" / "python.exe"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "service.log"
PID_FILE = LOG_DIR / "server.pid"
CONF_FILE = ROOT / "config" / "service_config.json"


DEFAULT_CONF = {
    "host": "127.0.0.1",
    "port": 8000,
    "check_interval_ms": 2000,
    "restart_threshold": 3,
    "uvicorn_args": ["-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"],
}


def load_conf():
    if CONF_FILE.exists():
        try:
            return {**DEFAULT_CONF, **json.loads(CONF_FILE.read_text(encoding="utf-8"))}
        except Exception:
            return DEFAULT_CONF
    return DEFAULT_CONF


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    LOG_FILE.write_text((LOG_FILE.read_text(encoding="utf-8") if LOG_FILE.exists() else "") + line, encoding="utf-8")
    try:
        if LOG_FILE.stat().st_size > 5 * 1024 * 1024:
            bak = LOG_DIR / f"service-{int(time.time())}.log"
            LOG_FILE.replace(bak)
    except Exception:
        pass


def port_open(host: str, port: int, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def health_ok(host: str, port: int, timeout=1.0) -> bool:
    import http.client
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        return resp.status == 200
    except Exception:
        return False


def start(conf):
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text())
            log(f"skip start: pid file exists pid={pid}")
            return True
        except Exception:
            pass
    # if already healthy, skip
    if health_ok(conf["host"], conf["port"]):
        log("skip start: server healthy")
        return True
    args = [str(VENV_PY)] + conf["uvicorn_args"]
    # inject configured host/port
    for i, a in enumerate(args):
        if a == "--host" and i + 1 < len(args):
            args[i + 1] = conf["host"]
        if a == "--port" and i + 1 < len(args):
            args[i + 1] = str(conf["port"])
    log(f"starting server: {' '.join(args)}")
    p = subprocess.Popen(args, cwd=str(ROOT))
    PID_FILE.write_text(str(p.pid))
    time.sleep(1.0)
    ok = health_ok(conf["host"], conf["port"])
    log(f"start result: healthy={ok}")
    return ok


def stop():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text())
        except Exception:
            pid = None
        PID_FILE.unlink(missing_ok=True)
        if pid:
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
                log(f"stopped pid={pid}")
                return True
            except Exception as e:
                log(f"stop failed: {e}")
                return False
    # fallback: kill uvicorn processes
    try:
        subprocess.run(["taskkill", "/IM", "uvicorn.exe", "/F"], check=False)
        log("stopped uvicorn.exe")
        return True
    except Exception:
        return False


def status(conf):
    s = {
        "port_open": port_open(conf["host"], conf["port"]),
        "health": health_ok(conf["host"], conf["port"]),
        "pid": None,
    }
    if PID_FILE.exists():
        try:
            s["pid"] = int(PID_FILE.read_text())
        except Exception:
            s["pid"] = None
    print(json.dumps(s))
    log(f"status {s}")
    return s


def monitor(conf):
    log("monitor start")
    consecutive_fail = 0
    while True:
        ok = health_ok(conf["host"], conf["port"])
        if ok:
            consecutive_fail = 0
        else:
            consecutive_fail += 1
            log(f"health check failed count={consecutive_fail}")
            if consecutive_fail >= conf["restart_threshold"]:
                stop()
                start(conf)
                consecutive_fail = 0
        time.sleep(conf["check_interval_ms"] / 1000.0)


def main():
    conf = load_conf()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        start(conf)
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        status(conf)
    elif cmd == "monitor":
        monitor(conf)
    else:
        print("usage: python manage_service.py [start|stop|status|monitor]")


if __name__ == "__main__":
    main()