import asyncio
import os
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import argparse
import dataclasses
import signal
import struct

from blueness import module
from bluer_options import string
from bluer_options.terminal.functions import hr
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.bps.stream import Stream
from bluer_algo.bps.stream import Ping
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

BPS_FILE_LOCK = os.getenv("BPS_FILE_LOCK")


def to_dict(obj):
    """Safely convert a dataclass or object to a dict."""
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)

    if hasattr(obj, "__dict__"):
        return vars(obj)

    if isinstance(obj, dict):
        return obj

    return {"repr": repr(obj)}


async def main(
    stream: Stream,
    grep: str = "",
    timeout: float = 10.0,
):
    logger.info(
        "{}: LE Scan for {} (Ctrl+C to stop) ...".format(
            NAME,
            string.pretty_duration(
                timeout,
                short=True,
            ),
        )
    )

    def callback(
        device: BLEDevice,
        advertisement_data: AdvertisementData,
    ):
        if grep and (
            device.name is None
            or not any(grep_ in device.name for grep_ in grep.split("+"))
        ):
            return

        logger.info(hr(width=30))
        logger.info(f"device name: {device.name}")
        logger.info(f"device address: {device.address}")

        if advertisement_data:
            rssi: float = -1.0
            try:
                rssi = advertisement_data.rssi
                logger.info(f"rssi: {rssi} dBm")
            except:
                logger.warning("rssi not found.")

            try:
                x_, y_, z_, sigma_, tx_power = struct.unpack(
                    "<fffff", advertisement_data.manufacturer_data[0xFFFF]
                )

                ping = Ping(
                    {
                        "hostname": device.name,
                        "x": x_,
                        "y": y_,
                        "z": z_,
                        "sigma": sigma_,
                        "tx_power": tx_power,
                        "rssi": rssi,
                    }
                )

                stream.append(ping, log=True)
            except:
                logger.info(advertisement_data)

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    logger.info("scanning started...")

    stop_event = asyncio.Event()

    def handle_sigint():
        logger.info("Ctrl+C detected, stopping scan ...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, handle_sigint)

    async def monitor_lock_file():
        """Periodically check if the lock file still exists."""
        while not stop_event.is_set():
            if not os.path.exists(BPS_FILE_LOCK):
                logger.warning(f"Lock file missing: {BPS_FILE_LOCK}, stopping scan ...")
                stop_event.set()
                break
            await asyncio.sleep(1.0)  # check every second

    # run both the wait and the file monitor
    try:
        await asyncio.wait_for(
            asyncio.gather(stop_event.wait(), monitor_lock_file()),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.info(
            "timeout ({}) reached, stopping advertisement.".format(
                string.pretty_duration(
                    timeout,
                    short=True,
                )
            )
        )

    await scanner.stop()
    logger.info("scan stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(NAME)
    parser.add_argument(
        "--grep",
        type=str,
        default="",
    )
    parser.add_argument(
        "--object_name",
        type=str,
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="in seconds",
    )
    args = parser.parse_args()

    stream = Stream.load(args.object_name)

    asyncio.run(
        main(
            stream=stream,
            grep=args.grep,
            timeout=args.timeout,
        )
    )

    success = stream.save(args.object_name)

    if success:
        success, _ = stream.estimate_position(args.object_name)

    sys_exit(logger, NAME, "receive", success)
