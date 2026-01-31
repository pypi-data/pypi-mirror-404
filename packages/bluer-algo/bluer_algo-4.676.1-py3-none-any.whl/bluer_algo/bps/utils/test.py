#!/usr/bin/env python3

import asyncio
import signal
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method
from dbus_next import BusType

from blueness import module

from bluer_algo import NAME
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)


class Hello(ServiceInterface):
    def __init__(self):
        super().__init__("org.example.Hello")

    @method()
    def Ping(self) -> "s":
        logger.info(f"{NAME}.ping() called by busctl!")
        return "Pong"


async def main():
    stop_event = asyncio.Event()

    def handle_sigint():
        logger.info(f"{NAME}: received Ctrl+C — shutting down gracefully ...")
        stop_event.set()

    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_sigint)

    # Connect to system bus
    bus = MessageBus(bus_type=BusType.SYSTEM)
    await bus.connect()
    logger.info(f"{NAME}: connected to system bus with unique name: {bus.unique_name}")

    obj_path = "/org/example/Hello"
    bus.export(obj_path, Hello())

    logger.info(f"exported org.example.Hello at {obj_path}")
    logger.info(
        f'run in another terminal: "@bps introspect unique_bus_name={bus.unique_name}"'
    )

    # Wait until interrupted
    await stop_event.wait()

    # Clean shutdown
    logger.info(f"{NAME}: disconnected cleanly.")
    bus.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{NAME}: interrupted — exiting.")
