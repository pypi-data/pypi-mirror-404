"""
Forwarding utilities for TLS Tunnel Client with:
- Auto-reconnect with exponential backoff
- Health checks
"""

import asyncio
from zscams.agent.src.support.logger import get_logger

READ_BUFFER_SIZE = 4096

logger = get_logger("tls_forward")


async def forward(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Forward data from reader to writer until connection closes.
    Handles Windows-specific connection resets gracefully.
    """
    try:
        while True:
            data = await reader.read(READ_BUFFER_SIZE)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, OSError) as err:
        # Handle Windows WinError 64 and other disconnects gracefully
        logger.debug("Connection closed by peer (expected): %s", err)
    except Exception as err:
        logger.error("Unexpected forwarding error: %s", err)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass  # ignore errors on close


async def handle_client(
    local_reader, local_writer, remote_host, remote_port, sni_hostname, ssl_context
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Forward a single local connection to the remote TLS server with SNI.
    Handles abrupt disconnects gracefully.
    """
    try:
        remote_reader, remote_writer = await asyncio.open_connection(
            host=remote_host,
            port=remote_port,
            ssl=ssl_context,
            server_hostname=sni_hostname,
        )
        logger.debug(
            "New connection: local -> %s:%s (SNI=%s)",
            remote_host,
            remote_port,
            sni_hostname,
        )

        await asyncio.gather(
            forward(local_reader, remote_writer), forward(remote_reader, local_writer)
        )

    except (ConnectionResetError, OSError) as e:
        logger.debug("Connection closed unexpectedly: %s", e)
    except Exception as e:
        logger.error("Unexpected client handling error: %s", e)
    finally:
        try:
            local_writer.close()
            await local_writer.wait_closed()
            logger.debug(
                f"Connection closed: local -> {remote_host}:{remote_port} (SNI={sni_hostname})"
            )
        except Exception as e:
            logger.error("Unexpected client handling error: %s", e)


async def start_tunnel(
    local_port,
    remote_host,
    remote_port,
    sni_hostname,
    ssl_context,
    reconnect_max_delay=60,
    ready_event=None,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Start a TCP listener on local_port and forward connections to the remote TLS server.
    Automatically reconnects on failure with exponential backoff and performs periodic health checks.

    Args:
        local_port (int)
        remote_host (str)
        remote_port (int)
        sni_hostname (str)
        ssl_context (ssl.SSLContext)
        reconnect_max_delay (int): Maximum delay between reconnect attempts
    """
    backoff = 1  # initial delay in seconds

    while True:
        try:
            server = await asyncio.start_server(
                lambda r, w: handle_client(
                    r, w, remote_host, remote_port, sni_hostname, ssl_context
                ),
                "127.0.0.1",
                local_port,
            )
            addr = server.sockets[0].getsockname()
            logger.info(
                "Listening on :%s -> %s:%s (SNI=%s)",
                addr[1],
                remote_host,
                remote_port,
                sni_hostname,
            )

            # Health check task: logs tunnel is alive every 30 seconds
            async def health_check():
                while True:
                    await asyncio.sleep(600)
                    logger.info(
                        "Tunnel on local port %s is healthy and running", local_port
                    )

            asyncio.create_task(health_check())

            # Signal ready if event is provided
            if ready_event:
                ready_event.set()

            async with server:
                await server.serve_forever()

        except Exception as e:
            logger.error("Tunnel error on local port %s: %s", local_port, e)
            logger.info("Reconnecting in %s seconds...", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, reconnect_max_delay)  # exponential backoff
        else:
            backoff = 1  # reset backoff if successful
