"""
Health monitor for agent services.

This module periodically checks the defined health ports of all services.
If a service is not responding on its port, it will be restarted.
"""

import asyncio
from zscams.agent.src.support.logger import get_logger
from zscams.agent.src.core.services import start_service
from zscams.agent.src.core import running_services
from zscams.agent.src.support.network import is_port_open

logger = get_logger("health_monitor")


async def monitor_services(services: list, config_dir: str, interval: int = 60):
    """
    Periodically check service health by port.

    If a service's health port is closed, attempt to restart it.
    """
    logger.info(f"Health monitor started (interval={interval}s)")
    await asyncio.sleep(30)  # Initial delay to allow services to start
    while True:
        for svc in services:
            name = svc["name"]
            health = svc.get("health", {})

            host = health.get("host", "localhost")
            port = health.get("port")
            if not port:
                logger.debug(f"Skipping {name}: no health port defined.")
                continue

            if name in running_services and is_port_open(host, port, logger):
                logger.debug(f"{name} is healthy on {host}:{port}")
                continue

            logger.warning(f"{name} not healthy, restarting...")
            if name in running_services:
                running_services.remove(name)
            try:
                await start_service(svc, config_dir)
                logger.info(f"Restarted service: {name}")
            except Exception as e:
                logger.error(f"Failed to restart {name}: {e}")

        await asyncio.sleep(interval)
