"""
Main entry point for ZSCAMs Agent
"""

import asyncio
import sys
import os
from zscams.agent.src.core.backend.bootstrap import bootstrap
from zscams.agent.src.core.backend.unbootstrap import unbootstrap
from zscams.agent.src.core.backend.update_machine_info import update_machine_info
from zscams.agent.src.support.logger import get_logger
from zscams.agent import init_parser, ensure_bootstrapped, run

logger = get_logger("ZSCAMs")


def main():
    """Main function to run the asynchronous main."""
    args = init_parser().parse_args()

    if args.bootstrap:
        try:
            if os.geteuid() != 0:
                logger.error("You are NOT running as root.")
                sys.exit(1)
            bootstrap()
            sys.exit(0)
        except Exception as exception:
            logger.error(exception)
            sys.exit(1)

    if args.update_machine_info:
        update_machine_info()
        sys.exit(0)

    if args.unbootstrap:
        try:
            if os.geteuid() != 0:
                logger.error("You are NOT running as root.")
                sys.exit(1)
            unbootstrap()
            sys.exit(0)
        except Exception as exception:
            logger.error(exception)
            sys.exit(1)

    try:
        ensure_bootstrapped()
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Exiting TLS Tunnel Client")


if __name__ == "__main__":
    main()
