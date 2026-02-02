"""
Network utilities for TLS Tunnel Client
"""

import socket


def is_port_open(host, port, logger):
    """Check if TCP port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        try:
            sock.connect((host, port))
            logger.debug(f"Port {port} on {host} is open.")
            return True
        except (ConnectionRefusedError, OSError):
            logger.error(f"Port {port} on {host} is not open.")
            return False
        except Exception as err:
            logger.error("Port check failed for %s:%s. Error: %s", host, port, err)
            return False


def is_service_running(service_name, running_services, logger):
    """Wait for another service to be marked as running."""
    if service_name in running_services:
        logger.debug(f"Service {service_name} is running.")
        return True

    logger.error(f"Service {service_name} is not running.")
    return False


def get_local_ip_address():
    """Get the local IP address of the machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # The IP used here doesn't need to be reachable
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        return ip


def get_local_hostname():
    """Get the local hostname of the machine."""

    return socket.gethostname()
