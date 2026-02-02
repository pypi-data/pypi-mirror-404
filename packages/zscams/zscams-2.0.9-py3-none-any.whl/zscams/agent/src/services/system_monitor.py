import asyncio
import os
import sys
import datetime
import psutil
import logging
import logging.handlers
import json
import socket
import platform
from zscams.agent.src.support.logger import get_logger
from http.client import BadStatusLine, HTTPConnection, HTTPException

logger = get_logger("system_monitor")

# Load service-specific params from environment
params_env = os.environ.get("SERVICE_PARAMS")
if not params_env:
    logger.error("SERVICE_PARAMS environment variable not set")
    sys.exit(1)

params = json.loads(params_env)
# -----------------------------
# Configuration
# -----------------------------
SYSLOG_HOST = params.get("remote_host", "localhost")  # remote rsyslog host
SYSLOG_PORT = params.get("remote_port", 514)  # TCP syslog port
EQUIPMENT_NAME = params.get("equipment_name", "connector")
EQUIPMENT_TYPE = params.get("equipment_type", "zpa")
SERVICE_NAME = params.get("service_name", "Zscaler-AppConnector")
HOSTNAME = platform.node()


def network():
    """
    Collect network interfaces and their statistics.
    Returns a dictionary with per-interface
    """
    ifaces = {}
    for iface, stats in psutil.net_io_counters(pernic=True).items():
        ifaces[iface] = {
            "in": {
                "bytes": stats.bytes_recv,
                "packets": stats.packets_recv,
                "errors": getattr(stats, "errin", 0),
                "dropped": getattr(stats, "dropin", 0),
            },
            "out": {
                "bytes": stats.bytes_sent,
                "packets": stats.packets_sent,
                "errors": getattr(stats, "errout", 0),
                "dropped": getattr(stats, "dropout", 0),
            },
        }
    if "lo" in ifaces:
        del ifaces["lo"]
    return ifaces


def memory():
    """
    Get memory and swap usage
    Returns a dictionary with total, used, free, and swap info.
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    mem_remain = mem.total - mem.available
    output_memory = {
        "actual": {
            "free": mem.available,
            "used": {
                "pct": round(mem_remain / mem.total, 4),
                "bytes": mem_remain,
            },
        },
        "total": mem.total,
        "used": {
            "pct": round(mem.percent / 100, 4),
            "bytes": mem.total - mem.available,
        },
        "free": mem.available,
        "swap": {
            "total": swap.total,
            "used": {
                "pct": swap.percent / 100,
                "bytes": swap.used,
            },
            "free": swap.free,
        },
    }
    return output_memory


def cpu():
    """
    Get CPU usage
    Returns a dictionary with total, user, system, idle, and core count.
    """
    times = psutil.cpu_times()
    total = sum(times)
    used = total - times.idle
    cpu_total_pct = round(used / total, 4)
    return {
        "total": {"pct": cpu_total_pct},
        "system": {"pct": round(times.system / total, 4)},
        "user": {"pct": round(times.user / total, 4)},
        "idle": {"pct": round(times.idle / total, 4)},
        "cores": psutil.cpu_count(),
        "iowait": {"pct": round(getattr(times, "iowait", 0) / total, 4)},
        "irq": {"pct": round(getattr(times, "irq", 0) / total, 4)},
        "softirq": {"pct": round(getattr(times, "softirq", 0) / total, 4)},
        "nice": {"pct": round(getattr(times, "nice", 0) / total, 4)},
        "steal": {"pct": round(getattr(times, "steal", 0) / total, 4)},
    }


def load():
    """
    Get CPU load averages over 1, 5, and 15 minutes.
    Returns a dictionary with normalized load per CPU core.
    """
    load1, load5, load15 = psutil.getloadavg()
    cores = psutil.cpu_count()
    cores = float(cores) if cores else 1.0
    return {
        "1": load1,
        "5": load5,
        "15": load15,
        "cores": cores,
        "norm": {
            "1": load1 / cores,
            "5": load5 / cores,
            "15": load15 / cores,
        },
    }


def uptime():
    """
    Return system boot time in seconds since the epoch.
    """
    return {"duration": {"seconds": int(psutil.boot_time())}}


def disk():
    """
    Get disk usage metrics for the root filesystem.
    Returns a dictionary with total, used, and free bytes.
    """
    disk = psutil.disk_usage("/")
    return {"total": disk.total, "used": disk.used, "free": disk.free}


def process(process_names=None):
    """
    Get metrics about running processes by name.
    Default: ["zpa-connector", "zpa-service-edge"]
    Returns a list of dictionaries with process info.
    """
    if process_names is None:
        process_names = ["zpa-connector", "zpa-service-edge"]

    output = []
    for proc in psutil.process_iter(
        [
            "name",
            "pid",
            "ppid",
            "username",
            "memory_info",
            "cpu_times",
            "cmdline",
            "status",
            "create_time",
        ]
    ):
        try:
            if proc.info["name"] in process_names:
                mem = proc.info["memory_info"]
                cpu_pct = proc.cpu_percent(interval=0.1)
                output.append(
                    {
                        "name": proc.info["name"],
                        "pid": proc.info["pid"],
                        "ppid": proc.info["ppid"],
                        "username": proc.info["username"],
                        "memory": {
                            "rss": mem.rss,
                            "vms": mem.vms,
                            "percent": round(proc.memory_percent(), 2),
                        },
                        "cpu": {
                            "percent": cpu_pct,
                            "start_time": datetime.datetime.fromtimestamp(
                                proc.info["create_time"]
                            ).isoformat(),
                        },
                        "cmdline": proc.info["cmdline"],
                        "status": proc.info["status"],
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return output


def collect_all():
    """
    Collect all metrics in a single dictionary.
    """
    return {
        "network": network(),
        "memory": memory(),
        "cpu": cpu(),
        "load": load(),
        "uptime": uptime(),
        "disk": disk(),
        "processes": process(),
    }


def log():
    return {
        "system": collect_all(),
        "beat": {
            "name": EQUIPMENT_NAME,
            "type": EQUIPMENT_TYPE,
            "hostname": HOSTNAME,
        },
        "host": HOSTNAME,
    }


# -----------------------------
# Helper function to log JSON
# -----------------------------
async def send_json_log(payload: dict):
    """
    Send a JSON-formatted log to syslog via TCP
    """
    conn = HTTPConnection(SYSLOG_HOST, SYSLOG_PORT, timeout=10)
    conn.request(
        "POST", "/", json.dumps(payload), headers={"Content-type": "application/json"}
    )
    conn.close()
    logger.info("Metrices collected and sent successfully.")


async def schedule_task(interval):
    while True:
        try:
            await send_json_log(log())
        except Exception as exception:
            print(exception)
        await asyncio.sleep(interval)


if __name__ == "__main__":
    try:
        asyncio.run(schedule_task(30))
    except KeyboardInterrupt:
        logger.info("Exiting system_monitor.py")
        sys.exit(0)
