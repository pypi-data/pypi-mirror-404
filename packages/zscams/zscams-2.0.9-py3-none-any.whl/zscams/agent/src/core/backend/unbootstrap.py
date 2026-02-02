import os
from zscams.agent.src.support.filesystem import resolve_path
from zscams.agent.src.support.configuration import get_config, CONFIG_PATH, ROOT_PATH
from zscams.agent.src.core.backend.client import BackendClient
from zscams.agent.src.support.logger import get_logger
from zscams.agent.src.support.os import remove_service, is_freebsd

logger = get_logger("Unbootstrap")


def unbootstrap():
    remote_configs = get_config().get("remote", {})
    backend_config = get_config().get("backend", {})
    private_key_path = resolve_path(
        remote_configs.get("client_key"), os.path.dirname(CONFIG_PATH)
    )

    cert_path = resolve_path(
        remote_configs.get("client_key"), os.path.dirname(CONFIG_PATH)
    )

    ca_chain_path = resolve_path(
        remote_configs.get("client_key"), os.path.dirname(CONFIG_PATH)
    )

    cache_path = os.path.join(
        ROOT_PATH.parent,
        backend_config.get("cache_dir"),
        BackendClient.MACHINE_INFO_FILE_NAME,
    )

    if os.path.exists(private_key_path):
        os.remove(private_key_path)
        logger.debug("Removed private key")

    if os.path.exists(cert_path):
        os.remove(cert_path)
        logger.debug("Removed certificate")

    if os.path.exists(ca_chain_path):
        os.remove(ca_chain_path)
        logger.debug("Removed CA Chain")

    if os.path.exists(cache_path):
        os.remove(cache_path)
        logger.debug("Removed Machine info")

    remove_service("zscams" if is_freebsd() else "zscams.service")
    logger.debug("Removed ZSCAMs service")
