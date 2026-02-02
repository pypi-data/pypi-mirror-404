import ssl
import os
from typing import Optional
from zscams.agent.src.support.configuration import RemoteConfig
from zscams.agent.src.support.filesystem import resolve_path
from zscams.agent.src.support.logger import get_logger

logger = get_logger("tls_utils")


def create_ssl_context(
    remote_cfg: RemoteConfig, config_dir: Optional[str] = None
) -> ssl.SSLContext:
    """
    Create an SSL context for TLS connections based on configuration.

    Args:
        remote_cfg (dict): Remote server configuration including:
            - verify_cert (bool)
            - ca_cert (str)
            - client_cert (str)
            - client_key (str)
        config_dir (str, optional): Directory to resolve relative paths from.

    Returns:
        ssl.SSLContext: Configured SSL context
    """
    context = ssl.create_default_context()

    ca_cert = resolve_path(remote_cfg.get("ca_cert"), config_dir)
    client_cert = resolve_path(remote_cfg.get("client_cert"), config_dir)
    client_key = resolve_path(remote_cfg.get("client_key"), config_dir)

    if not remote_cfg.get("verify_cert", True):
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        logger.warning("Certificate verification is disabled!")
    else:
        if ca_cert and os.path.exists(ca_cert):
            context.load_verify_locations(cafile=ca_cert)
            logger.info("Loaded CA certificate from %s", ca_cert)
        else:
            logger.warning("CA certificate not found or not provided: %s", ca_cert)

    if client_cert and client_key:
        if os.path.exists(client_cert) and os.path.exists(client_key):
            context.load_cert_chain(certfile=client_cert, keyfile=client_key)
            logger.info(
                "Loaded client certificate/key: %s / %s", client_cert, client_key
            )
        else:
            raise FileNotFoundError(
                f"Client certificate or key not found: {client_cert}, {client_key}"
            )

    return context
