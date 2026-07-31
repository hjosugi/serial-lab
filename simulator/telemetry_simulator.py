#!/usr/bin/env python3
"""Send ESP32-like telemetry to Serial Studio over UDP."""

from __future__ import annotations

import argparse
import math
import socket
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000
DEFAULT_RATE_HZ = 20.0
MAX_RATE_HZ = 1000.0
SINE_PERIOD_S = 2.0
TRIANGLE_PERIOD_S = 4.0


@dataclass(frozen=True)
class Config:
    """Validated-at-runtime simulator settings."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    rate: float = DEFAULT_RATE_HZ
    count: int = 0
    stdout: bool = False


def wave_phase(elapsed_seconds: float, period_seconds: float) -> float:
    """Reduce elapsed time to one waveform period, in radians.

    The firmware performs the same reduction so that its 32-bit float phase
    keeps full resolution on long runs. Mirroring it here keeps both telemetry
    sources on identical waveform semantics.
    """
    return 2.0 * math.pi * math.fmod(elapsed_seconds, period_seconds) / period_seconds


def build_frame(elapsed_seconds: float) -> str:
    """Build one six-column CSV telemetry frame."""
    temperature_c = 42.0 + 3.0 * math.sin(2.0 * math.pi * 0.03 * elapsed_seconds)
    free_heap_kib = 286.0 - 4.0 * math.sin(2.0 * math.pi * 0.01 * elapsed_seconds)
    sine = math.sin(wave_phase(elapsed_seconds, SINE_PERIOD_S))
    triangle = (2.0 / math.pi) * math.asin(
        math.sin(wave_phase(elapsed_seconds, TRIANGLE_PERIOD_S))
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


def parse_args(argv: Sequence[str] | None = None) -> Config:
    """Parse command-line arguments into an immutable configuration."""
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
    namespace = parser.parse_args(argv)
    return Config(
        host=namespace.host,
        port=namespace.port,
        rate=namespace.rate,
        count=namespace.count,
        stdout=namespace.stdout,
    )


def validate_config(config: Config) -> None:
    """Reject values that could produce invalid or unbounded behavior."""
    if not config.host.strip():
        raise ValueError("--host must not be empty")
    if not math.isfinite(config.rate) or not 0 < config.rate <= MAX_RATE_HZ:
        raise ValueError(f"--rate must be finite and between 0 and {MAX_RATE_HZ:g}")
    if not 1 <= config.port <= 65535:
        raise ValueError("--port must be between 1 and 65535")
    if config.count < 0:
        raise ValueError("--count must be zero or greater")


def run(config: Config) -> None:
    """Send frames until the configured count is reached or interrupted."""
    validate_config(config)

    interval = 1.0 / config.rate
    address = (config.host, config.port)
    started_at = time.monotonic()
    next_send_at = started_at
    sent = 0

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        while config.count == 0 or sent < config.count:
            now = time.monotonic()
            if now < next_send_at:
                time.sleep(next_send_at - now)

            elapsed_seconds = time.monotonic() - started_at
            frame = build_frame(elapsed_seconds)
            udp_socket.sendto(frame.encode("utf-8"), address)

            if config.stdout:
                sys.stdout.write(frame)
                sys.stdout.flush()

            sent += 1
            next_send_at += interval

            if next_send_at < time.monotonic() - interval:
                next_send_at = time.monotonic()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and translate expected failures into exit codes."""
    config = parse_args(argv)
    try:
        run(config)
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
