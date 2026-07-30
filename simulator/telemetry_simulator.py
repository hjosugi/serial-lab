#!/usr/bin/env python3
"""Send ESP32-like telemetry to Serial Studio over UDP."""

from __future__ import annotations

import argparse
import math
import socket
import sys
import time


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000
DEFAULT_RATE_HZ = 20.0


def build_frame(elapsed_seconds: float) -> str:
    """Build one six-column CSV telemetry frame."""
    temperature_c = 42.0 + 3.0 * math.sin(2.0 * math.pi * 0.03 * elapsed_seconds)
    free_heap_kib = 286.0 - 4.0 * math.sin(2.0 * math.pi * 0.01 * elapsed_seconds)
    sine = math.sin(2.0 * math.pi * 0.50 * elapsed_seconds)
    triangle = (2.0 / math.pi) * math.asin(
        math.sin(2.0 * math.pi * 0.25 * elapsed_seconds)
    )
    button_pressed = 1 if int(elapsed_seconds) % 10 >= 5 else 0

    return (
        f"{temperature_c:.2f},"
        f"{free_heap_kib:.2f},"
        f"{elapsed_seconds:.2f},"
        f"{sine:.4f},"
        f"{triangle:.4f},"
        f"{button_pressed}\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send six-column telemetry to Serial Studio over UDP."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE_HZ)
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Stop after this many frames. Zero means run until interrupted.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Also print each frame to stdout.",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    if args.rate <= 0:
        raise ValueError("--rate must be greater than zero")
    if not 1 <= args.port <= 65535:
        raise ValueError("--port must be between 1 and 65535")
    if args.count < 0:
        raise ValueError("--count must be zero or greater")

    interval = 1.0 / args.rate
    address = (args.host, args.port)
    started_at = time.monotonic()
    next_send_at = started_at
    sent = 0

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        while args.count == 0 or sent < args.count:
            now = time.monotonic()
            if now < next_send_at:
                time.sleep(next_send_at - now)

            elapsed_seconds = time.monotonic() - started_at
            frame = build_frame(elapsed_seconds)
            udp_socket.sendto(frame.encode("utf-8"), address)

            if args.stdout:
                sys.stdout.write(frame)
                sys.stdout.flush()

            sent += 1
            next_send_at += interval

            if next_send_at < time.monotonic() - interval:
                next_send_at = time.monotonic()


def main() -> int:
    args = parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

