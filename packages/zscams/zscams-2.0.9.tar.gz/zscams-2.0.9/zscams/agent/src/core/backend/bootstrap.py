import os
from pathlib import Path
import sysconfig
import sys
from typing import cast
from zscams.agent.src.core.backend.client import backend_client
from zscams.agent.src.support.configuration import reinitialize, CONFIG_PATH
from zscams.agent.src.support.logger import get_logger
from zscams.agent.src.support.os import create_system_user, install_service, is_freebsd
from zscams.agent.src.support.ssh import add_to_authorized_keys
from zscams.agent.src.support.cli import prompt

logger = get_logger("bootstrap")


def bootstrap():
    """Ensure the agent is bootstrapped with the backend."""

    if backend_client.is_bootstrapped():
        logger.info("Agent ID %s is already bootstrapped.", backend_client.agent_id)
        return

    username = input("Username: ")
    totp = input("One Time Password (OTP): ")

    backend_client.login(username, totp)

    customer_name = prompt(
        "Customer Name",
        "Customer Name",
        required=True,
        startswith="",
    )
    connector_name = prompt(
        "Connector Name",
        "Connector Name [Unique name for this connector]",
        required=True,
        startswith="",
    )
    equipment_type = prompt(
        "Equipment Type",
        "Equipment Type [Can be ZPA|VZEN|PSE]",
        required=True,
        startswith="",
    )
    equipment_name = (
        f"{equipment_type.lower()}-{customer_name.lower()}-{connector_name.lower()}"
    )
    enforced_id = prompt("Enforced ID", "Enforced Agent ID")
    if not os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    reinitialize(equipment_name=equipment_name, equipment_type=equipment_type)
    cm_info = backend_client.bootstrap(equipment_name, enforced_id or None)

    sys_user = cast(str, cm_info.get("ssh_user"))

    create_system_user(sys_user)
    add_to_authorized_keys(sys_user, cm_info.get("server_ssh_pub_key"))
    install_zscams_systemd_service(sys_user)


def install_zscams_systemd_service(user_to_run_as: str):

    data = {
        "pythonpath": sysconfig.get_paths()["purelib"],
        "python_exec": sys.executable,
        "user_to_run_as": user_to_run_as,
    }
    import zscams

    BASE_DIR = Path(zscams.__file__).resolve().parent
    filename = "linux_service.j2" if is_freebsd() else "freebsd_service.j2"
    template_path = f"{BASE_DIR}/agent/configuration/{filename}.j2"
    with open(template_path) as f:
        template = f.read()

    rendered_config = template.format(**data)

    install_service("zscams" if is_freebsd() else "zscams.service", rendered_config)
