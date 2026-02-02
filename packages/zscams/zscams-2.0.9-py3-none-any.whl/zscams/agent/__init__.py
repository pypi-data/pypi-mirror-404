import os
import asyncio
import sys
import argparse
from zscams.agent.src.support.configuration import get_config, CONFIG_PATH
from zscams.agent.src.support.filesystem import is_file_exists, resolve_path
from zscams.agent.src.core.tunnel.tls import create_ssl_context
from zscams.agent.src.core.tunnels import start_all_tunnels
from zscams.agent.src.core.services import start_all_services
from zscams.agent.src.core.service_health_check import monitor_services
from zscams.agent.src.core.backend.client import backend_client
from zscams.agent.src.support.logger import get_logger


logger = get_logger("tls_tunnel_main")


def init_parser():
    parser = argparse.ArgumentParser(description="ZSCAMs Agent")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Run bootstrap process and exit",
    )
    parser.add_argument(
        "--unbootstrap",
        action="store_true",
        help="Run unbootstrap process and exit",
    )
    parser.add_argument(
        "--update-machine-info",
        action="store_true",
        help="Reinitialize machine info",
    )
    return parser


def ensure_bootstrapped():
    """Ensure the agent is bootstrapped with the backend."""

    config = get_config()
    remote_cfg = config["remote"]
    config_dir = os.path.dirname(CONFIG_PATH)

    files_to_ensure = [
        resolve_path(remote_cfg.get("ca_cert"), config_dir),
        resolve_path(remote_cfg.get("client_cert"), config_dir),
        resolve_path(remote_cfg.get("client_key"), config_dir),
    ]

    has_missing_file = False

    for file in files_to_ensure:
        if not is_file_exists(file, logger):
            has_missing_file = True
            break

    bootstrapped = backend_client.is_bootstrapped()

    logger.debug("Agent has entry on server: %s", bootstrapped)

    if not bootstrapped or has_missing_file:
        logger.error(
            "Agent is not bootstrapped. Please run `zscams --bootstrap` to start the bootstrap process.",
        )
        sys.exit(1)


async def run():
    """Asynchronous main function to start tunnels and services."""

    config = get_config()
    config_dir = os.path.dirname(CONFIG_PATH)
    ssl_context = create_ssl_context(config["remote"], config_dir=config_dir)
    remote_host = config["remote"]["host"]
    remote_port = config["remote"]["port"]

    # Start tunnels and wait for readiness
    tunnel_tasks = await start_all_tunnels(
        config.get("forwards", []), remote_host, remote_port, ssl_context
    )

    # Start services that depend on tunnels
    service_tasks = asyncio.create_task(
        start_all_services(config.get("services", []), config_dir=config_dir)
    )

    # Start health checks
    monitor_task = asyncio.create_task(
        monitor_services(
            config.get("services", []),
            config_dir=config_dir,
            interval=config.get("general", {}).get("health_check_interval", 300),
        )
    )

    logger.info("[*] All tunnels and services started. Press Ctrl+C to stop.")
    await asyncio.gather(*tunnel_tasks, service_tasks, monitor_task)
