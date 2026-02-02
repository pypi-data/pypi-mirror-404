from typing import Optional, cast
from zscams.agent.src.support.logger import get_logger

logger = get_logger("bootstrap")


class RequiredFieldException(Exception):
    pass


class InvalidFieldException(Exception):
    pass


def prompt(
    name: str,
    message: str,
    required=False,
    startswith: Optional[str] = None,
    fail_on_error=False,
    retries_count=3,
):
    _message = message
    if not required:
        _message += " (Optional)"

    _message += ": "

    val = input(_message)

    if required and not val:
        if fail_on_error:
            raise RequiredFieldException(f"Missing {name}")
        logger.error(f"{name} is required..")
        retries_count -= 1
        return prompt(
            name, message, required, startswith, fail_on_error=retries_count <= 0
        )

    if startswith is not None and not val.startswith(startswith):
        error_mesagge = f"The value has to start with {startswith}"
        if fail_on_error:
            raise InvalidFieldException(error_mesagge)
        logger.error(error_mesagge)
        retries_count -= 1
        return prompt(
            name, message, required, startswith, fail_on_error=retries_count <= 0
        )

    return val
