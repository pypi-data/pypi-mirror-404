import os
from zscams.agent.src.support.logger import get_logger
from zscams.agent.src.support.filesystem import is_file_exists
from zscams.agent.src.core import running_services
from zscams.agent.src.support.network import is_port_open, is_service_running
from zscams.agent.src.support.configuration import CONFIG_PATH

logger = get_logger("service_prerequisites")
config_dir = os.path.dirname(CONFIG_PATH)


def check_prerequisites(prereqs: dict) -> bool:
    """
    Perform a one-shot prerequisites check (no waiting or retry).
    Returns True only if all listed conditions are satisfied.
    """
    if not prereqs:
        return True

    results = []

    # Check file prerequisites
    for path in prereqs.get("files", []):
        results.append(is_file_exists(path, logger, config_dir))

    # Check port prerequisites
    for port in prereqs.get("ports", []):
        results.append(is_port_open("localhost", port, logger))

    # Check service prerequisites
    for svc in prereqs.get("services", []):
        results.append(is_service_running(svc, running_services, logger))

    all_ok = all(results)
    if not all_ok:
        logger.warning("Some prerequisites failed for this service.")
    else:
        logger.info("All prerequisites satisfied.")
    return all_ok
