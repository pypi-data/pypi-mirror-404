from zscams.agent.src.core.backend.client import backend_client
from zscams.agent.src.support.logger import get_logger

logger = get_logger("agent_machine_info")


def update_machine_info():
    """Ensure the agent is bootstrapped with the backend."""

    username = input("LDAP Username: ")
    totp = input("TOTP: ")

    backend_client.login(username, totp)

    logger.info("Getting machine info from backend...")
    backend_client.get_machine_info(ignore_cache=True)
