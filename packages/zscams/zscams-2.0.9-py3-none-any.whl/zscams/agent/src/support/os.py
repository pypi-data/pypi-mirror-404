import os
import sys
import subprocess
import platform
import subprocess
from zscams.agent.src.support.logger import get_logger

from .filesystem import write_to_file

logger = get_logger("os_support")


def is_linux():
    if sys.platform.lower().startswith("linux"):
        return True
    return False


def system_user_exists(username: str):
    try:
        subprocess.run(
            ["id", username],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.debug("found the system user %s", username)
        return True
    except subprocess.CalledProcessError:
        return False


def is_freebsd():
    return (
        platform.system().lower() == "freebsd"
        or platform.system().lower() == "zscaleros"
    )


def create_system_user(username: str):
    # Support both Linux and FreeBSD
    if not (platform.system() == "Linux" or is_freebsd()):
        logger.error(
            "Error creating system user: This script is intended to run on Linux or FreeBSD systems."
        )
        return

    if not username:
        logger.error("Error creating system user: Username must be provided.")
        return

    # Assuming system_user_exists is already updated to handle both
    if system_user_exists(username):
        logger.warning("User '%s' already exists.", username)
        return

    try:
        if is_freebsd():
            cmd = ["sudo", "pw", "useradd", "-n", username, "-m", "-s", "/bin/sh"]
        else:
            # Standard Linux useradd
            cmd = ["sudo", "useradd", "-m", "-s", "/bin/bash", username]

        subprocess.run(cmd, check=True)
        logger.info("System user '%s' created successfully.", username)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to create user '%s': %s", username, e)


def install_service(service_name: str, content: str):
    """
    Main entry point to install services.
    Redirects to systemd for Linux and rc.d for FreeBSD.
    """
    if is_linux():
        install_systemd_service(service_name, content)
    elif is_freebsd():
        install_rc_service(service_name, content)
    else:
        logger.error("Unsupported OS for service installation.")


def install_rc_service(service_name: str, content: str):
    """
    Installs a FreeBSD rc.d script.
    Note: 'content' for FreeBSD should be a valid rc.subr shell script.
    """
    service_path = f"/usr/local/etc/rc.d/{service_name}"

    try:
        # 1. Write the rc script
        logger.debug("Installing FreeBSD rc script: %s", service_path)
        # Using sudo tee to ensure write permissions on restricted paths
        echo_cmd = f"printf '%s' '{content}' | sudo tee {service_path}"
        subprocess.run(echo_cmd, shell=True, check=True, stdout=subprocess.DEVNULL)

        # 2. Make it executable (Crucial for FreeBSD)
        subprocess.run(["sudo", "chmod", "+x", service_path], check=True)

        # 3. Enable and Start
        # In FreeBSD, enabling adds 'service_name_enable="YES"' to /etc/rc.conf
        logger.debug("Enabling and starting FreeBSD service %s...", service_name)
        subprocess.run(["sudo", "sysrc", f"{service_name}_enable=YES"], check=True)
        subprocess.run(["sudo", "service", service_name, "start"], check=True)

        logger.info("Service %s installed and started successfully.", service_name)

    except Exception as e:
        logger.error("Failed to install FreeBSD service %s: %s", service_name, e)


def install_systemd_service(service_name: str, content: str):
    service_path = f"/etc/systemd/system/{service_name}"

    try:
        logger.debug("Installing service '%s' content", service_name)
        write_to_file(service_path, content)
        logger.debug(f"Installed {service_name}")
    except PermissionError:
        logger.warning("Permission denied: trying to write with sudo...")
        echo_cmd = f"echo '{content}' | sudo tee {service_path}"
        subprocess.run(echo_cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
        logger.debug("Wrote the service")
    except Exception as e:
        logger.error("Failed to install service %s. %s", service_name, e)
        return

    try:
        logger.debug("Enabling %s...", service_name)
        subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
        logger.debug("Starting %s...", service_name)
        subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
    except subprocess.CalledProcessError:
        logger.error(
            "Failed to enable/restart zscams service, You might need to do that manually by running\nsudo systemctl enable %s && sudo systemctl start %s",
            service_name,
            service_name,
        )


def remove_service(service_name: str):
    """
    Stops, disables, and removes service configurations for Linux and FreeBSD.
    """
    # Standardize name (remove .service suffix if present for consistency)
    clean_name = service_name.replace(".service", "")

    if is_linux():
        _remove_systemd_service(clean_name)
    elif is_freebsd():
        _remove_rc_service(clean_name)
    else:
        logger.error("Unsupported OS for service removal.")


def _remove_systemd_service(name: str):
    service_file = f"/etc/systemd/system/{name}.service"
    try:
        logger.info("Stopping and disabling systemd service: %s", name)
        subprocess.run(["sudo", "systemctl", "stop", name], check=False)
        subprocess.run(["sudo", "systemctl", "disable", name], check=False)

        if os.path.exists(service_file):
            subprocess.run(["sudo", "rm", service_file], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            logger.info("Systemd service %s removed.", name)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to remove systemd service: %s", e)


def _remove_rc_service(name: str):
    rc_file = f"/usr/local/etc/rc.d/{name}"
    try:
        logger.info("Stopping and disabling FreeBSD service: %s", name)
        # 1. Stop the service
        subprocess.run(["sudo", "service", name, "stop"], check=False)

        # 2. Disable in /etc/rc.conf
        # Using sysrc -x removes the variable entirely from rc.conf
        subprocess.run(["sudo", "sysrc", "-x", f"{name}_enable"], check=False)

        # 3. Remove the rc.d script
        if os.path.exists(rc_file):
            subprocess.run(["sudo", "rm", rc_file], check=True)
            logger.info("FreeBSD rc script %s removed.", name)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to remove FreeBSD service: %s", e)
