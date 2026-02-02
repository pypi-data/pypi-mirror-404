from zscams.agent.src.support.configuration import get_config
from zscams.agent.src.support.filesystem import append_to_file
from zscams.agent.src.support.logger import get_logger


logger = get_logger("ssh_support")


def add_to_known_hosts(hostname: str, pub_key: str):
    logger.debug("Appending '%s' to known hosts...", pub_key)
    append_to_file(
        get_config().get("ssh", {}).get("known_hosts_file_path"),
        f"{hostname} {pub_key}\n",
    )
    logger.debug("Appended key to known hosts")


def add_to_authorized_keys(user, pub_key):
    logger.debug(f"Appending to public key to {user}")
    key = pub_key.split(' ')[1] if len(pub_key.split(' ')) >= 2 else pub_key
    append_to_file(
        f"/home/{user}/.ssh/authorized_keys",
        f"ssh-rsa {key} zscams@orangecyberdefense\n",
    )
