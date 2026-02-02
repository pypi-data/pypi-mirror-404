import asyncio
import json
import os
import sys
from zscams.agent.src.support.logger import get_logger
from zscams.agent.src.support.filesystem import resolve_path
from zscams.agent.src.support.configuration import CONFIG_PATH

logger = get_logger("autossh_service")

# Load service-specific params from environment
params_env = os.environ.get("SERVICE_PARAMS")
if not params_env:
    logger.error("SERVICE_PARAMS environment variable not set")
    sys.exit(1)

params = json.loads(params_env)
config_dir = os.path.dirname(CONFIG_PATH)
LOCAL_PORT = params.get("local_port", 4422)
SERVER_SSH_USER = params.get("server_ssh_user", "ssh_user")
REVERSE_PORT = params.get("reverse_port", 2222)
PRIVATE_KEY = resolve_path(params.get("private_key"), config_dir)  # Path to RSA key
SSH_OPTIONS = params.get("ssh_options", [])
CHECK_INTERVAL = 120  #


async def run():
    backoff = 1
    max_backoff = 60
    ssh_cmd = [
        "ssh",
        "-p",
        f"{LOCAL_PORT}",
        "-R",
        f"*:{REVERSE_PORT}:localhost:22",
        f"{SERVER_SSH_USER}@localhost",
        "-N",
    ]

    # Use key file if provided
    if PRIVATE_KEY:
        ssh_cmd += ["-i", PRIVATE_KEY]

    # Add additional SSH options
    ssh_cmd += SSH_OPTIONS
    os.chmod(PRIVATE_KEY, 0o700)
    logger.info(f"Starting reverse SSH tunnel: {' '.join(ssh_cmd)}")

    while True:
        try:
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"SSH tunnel started (PID={process.pid})")
            stdout, stderr = await process.communicate()
            if stdout:
                logger.info(stdout.decode())
            if stderr:
                logger.warning(stderr.decode())
            returncode = process.returncode
            logger.warning(f"SSH tunnel exited with code {returncode}")
        except Exception as e:
            logger.error(f"SSH tunnel failed: {e}")

        logger.info(f"Reconnecting in {backoff} seconds...")
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Exiting autossh_service.py")
        sys.exit(0)
