"""
Utilities to start TLS tunnels asynchronously

- Supports multiple forwards
- Signals readiness via asyncio.Event
- Auto-reconnect and logging
"""

import asyncio
from zscams.agent.src.core.tunnel import start_tunnel
from zscams.agent.src.support.logger import get_logger

logger = get_logger("tunnel_launcher")


async def start_all_tunnels(forwards_cfg_list, remote_host, remote_port, ssl_context):
    """
    Start all TLS tunnels concurrently and wait for readiness.

    Args:
        forwards_cfg_list (list): List of forward dictionaries from config
            Each dict should have:
                - local_port
                - sni_hostname
        remote_host (str): Remote host to connect to
        remote_port (int): Remote port to connect to
        ssl_context (ssl.SSLContext): SSL context for the TLS tunnel

    Returns:
        list of asyncio.Tasks: tunnel tasks running indefinitely
    """
    tasks = []
    ready_events = []

    for forward_cfg in forwards_cfg_list:
        ready_event = asyncio.Event()
        ready_events.append(ready_event)
        tasks.append(
            asyncio.create_task(
                start_tunnel(
                    local_port=forward_cfg["local_port"],
                    remote_host=remote_host,
                    remote_port=remote_port,
                    sni_hostname=forward_cfg["sni_hostname"],
                    ssl_context=ssl_context,
                    reconnect_max_delay=60,
                    ready_event=ready_event,
                )
            )
        )

    # Wait for all tunnels to signal readiness
    await asyncio.gather(*(event.wait() for event in ready_events))
    logger.info("[*] %d tunnel(s) ready", len(tasks))
    return tasks
