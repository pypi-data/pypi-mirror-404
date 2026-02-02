"""
Service launcher utilities for TLS Tunnel Client

- Generic solution: any service can receive parameters via `SERVICE_PARAMS` env variable
- Starts services asynchronously using asyncio
- Supports both Python scripts and executables
"""

import asyncio
import json
import os
from zscams.agent.src.support.logger import get_logger
from zscams.agent.src.core.prerequisites import check_prerequisites
from zscams.agent.src.core import running_services

logger = get_logger("service_launcher")


async def start_service(service_cfg, config_dir=None):
    """
    Launch an external script/service asynchronously.

    Args:
        service_cfg (dict): Service configuration from config.yaml
            - name: service name
            - script: path to script/executable
            - port: associated port (optional)
            - args: list of extra arguments
            - params: dict of arbitrary parameters (SERVICE_PARAMS)
        config_dir (str, optional): Base directory to resolve relative script paths

    Returns:
        asyncio.subprocess.Process or None
    """
    base_dir = config_dir or os.getcwd()
    script_path = os.path.join(base_dir, service_cfg["script"])
    prereqs = service_cfg.get("prerequisites")
    name = service_cfg["name"]
    # Wait for prerequisites before starting
    logger.info("Checking prerequisites for %s...", name)
    ok = check_prerequisites(prereqs)
    if not ok:
        logger.error("Prerequisites not met for %s. Skipping start.", name)
        return

    if not os.path.exists(script_path):
        logger.error("Service script not found: %s", script_path)
        return None

    env = os.environ.copy()
    params = service_cfg.get("params")
    if params:
        # Pass generic parameters to the service via JSON environment variable
        env["SERVICE_PARAMS"] = json.dumps(params)

    cmd = ["python", script_path] + service_cfg.get("args", [])
    logger.info(
        "Starting service %s on port %d: %s",
        service_cfg.get("name"),
        service_cfg.get("port", 0),
        cmd,
    )

    try:
        process = await asyncio.create_subprocess_exec(*cmd, env=env)
        running_services.add(name)
        return process
    except Exception as e:
        logger.error("Failed to start service %s: %s", service_cfg.get("name"), e)
        return None


async def start_all_services(services_cfg_list, config_dir=None):
    """
    Start all services defined in the configuration concurrently.

    Args:
        services_cfg_list (list): List of service configuration dictionaries
        config_dir (str, optional): Base directory to resolve relative script paths
    """
    tasks = []
    for svc in services_cfg_list:
        tasks.append(start_service(svc, config_dir=config_dir))

    # Wait for all services to start
    await asyncio.gather(*tasks)
