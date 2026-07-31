from __future__ import annotations

import contextlib
import io
import math
import socket
import struct
import unittest
from unittest import mock

from simulator import telemetry_simulator as simulator


def as_float32(value: float) -> float:
    """Round a value through 32-bit float, as the firmware does."""
    return float(struct.unpack("f", struct.pack("f", value))[0])


class TelemetryFrameTest(unittest.TestCase):
    def test_zero_second_frame_is_stable_and_has_six_columns(self) -> None:
        frame = simulator.build_frame(0.0)

        self.assertEqual(frame, "42.00,286.00,0.00,0.0000,0.0000,0\n")
        self.assertEqual(len(frame.strip().split(",")), 6)

    def test_waveforms_remain_in_expected_range(self) -> None:
        frame = simulator.build_frame(12.5)
        values = [float(value) for value in frame.strip().split(",")]

        self.assertGreater(values[0], 0)
        self.assertGreater(values[1], 0)
        self.assertEqual(values[2], 12.5)
        self.assertGreaterEqual(values[3], -1)
        self.assertLessEqual(values[3], 1)
        self.assertGreaterEqual(values[4], -1)
        self.assertLessEqual(values[4], 1)
        self.assertIn(values[5], (0, 1))

    def test_button_toggles_every_five_seconds(self) -> None:
        released = simulator.build_frame(4.9).strip().split(",")[-1]
        pressed = simulator.build_frame(5.0).strip().split(",")[-1]
        released_again = simulator.build_frame(10.0).strip().split(",")[-1]

        self.assertEqual(released, "0")
        self.assertEqual(pressed, "1")
        self.assertEqual(released_again, "0")


class LongRunTest(unittest.TestCase):
    """Guard the uptime semantics agreed in issue #7."""

    # The 32-bit millis() counter the firmware used to derive uptime from
    # returned to zero here.
    MILLIS_WRAP_S = 2**32 / 1000.0

    @staticmethod
    def columns(elapsed_seconds: float) -> list[float]:
        frame = simulator.build_frame(elapsed_seconds)
        return [float(value) for value in frame.strip().split(",")]

    def test_uptime_column_keeps_rising_past_the_millis_wrap(self) -> None:
        marks = (
            3600.0,
            86400.0,
            self.MILLIS_WRAP_S - 1.0,
            self.MILLIS_WRAP_S + 1.0,
            self.MILLIS_WRAP_S * 2,
        )

        reported = [self.columns(seconds)[2] for seconds in marks]

        for seconds, value in zip(marks, reported, strict=True):
            with self.subTest(seconds=seconds):
                self.assertAlmostEqual(value, seconds, places=1)
        self.assertEqual(reported, sorted(reported))

    def test_waveform_columns_repeat_once_per_period(self) -> None:
        periods = (
            (3, simulator.SINE_PERIOD_S),
            (4, simulator.TRIANGLE_PERIOD_S),
        )

        for column, period in periods:
            for offset in (0.0, 0.25, 0.9, 1.5):
                with self.subTest(column=column, offset=offset):
                    self.assertAlmostEqual(
                        self.columns(offset)[column],
                        self.columns(offset + period)[column],
                        places=4,
                    )

    def test_waveforms_keep_full_resolution_after_a_full_day(self) -> None:
        # A day is a whole number of both wave periods, so the reduced phase
        # must land back on the boot-time sample instead of quantizing.
        for offset in (0.0, 0.5, 1.25):
            with self.subTest(offset=offset):
                self.assertEqual(
                    self.columns(86400.0 + offset)[3:5],
                    self.columns(offset)[3:5],
                )

    def test_wave_phase_is_reduced_to_a_single_turn(self) -> None:
        for period in (simulator.SINE_PERIOD_S, simulator.TRIANGLE_PERIOD_S):
            for seconds in (0.0, 1.5, 86400.25, self.MILLIS_WRAP_S):
                with self.subTest(period=period, seconds=seconds):
                    phase = simulator.wave_phase(seconds, period)
                    self.assertGreaterEqual(phase, 0.0)
                    self.assertLess(phase, 2.0 * math.pi)

    def test_reduced_phase_survives_the_firmware_float32_cast(self) -> None:
        """Reduction is what keeps the ESP32 waveform accurate on long runs.

        The firmware casts the phase to a 32-bit float. Feeding it raw elapsed
        time costs about four significant digits after a day; the reduced phase
        does not.
        """
        seconds = 86400.25
        period = simulator.SINE_PERIOD_S
        exact = math.sin(2.0 * math.pi * seconds / period)

        reduced = math.sin(as_float32(simulator.wave_phase(seconds, period)))
        unreduced = math.sin(as_float32(2.0 * math.pi * seconds / period))

        self.assertLess(abs(reduced - exact), 1e-6)
        self.assertGreater(abs(unreduced - exact), 1e-3)

    def test_waveforms_stay_in_range_on_long_runs(self) -> None:
        for seconds in (86400.0, self.MILLIS_WRAP_S, 10_000_000.0):
            with self.subTest(seconds=seconds):
                sine, triangle = self.columns(seconds)[3:5]
                self.assertGreaterEqual(min(sine, triangle), -1.0)
                self.assertLessEqual(max(sine, triangle), 1.0)


class ConfigTest(unittest.TestCase):
    def test_parse_args_maps_every_option(self) -> None:
        config = simulator.parse_args(
            [
                "--host",
                "192.0.2.1",
                "--port",
                "10000",
                "--rate",
                "25.5",
                "--count",
                "3",
                "--stdout",
            ]
        )

        self.assertEqual(
            config,
            simulator.Config(
                host="192.0.2.1",
                port=10000,
                rate=25.5,
                count=3,
                stdout=True,
            ),
        )

    def test_rejects_empty_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "--host must not be empty"):
            simulator.validate_config(simulator.Config(host=" "))

    def test_rejects_non_finite_non_positive_and_excessive_rates(self) -> None:
        invalid_rates = (
            float("nan"),
            float("inf"),
            float("-inf"),
            -1.0,
            0.0,
            simulator.MAX_RATE_HZ + 1,
        )

        for rate in invalid_rates:
            with self.subTest(rate=rate):
                with self.assertRaisesRegex(
                    ValueError, "--rate must be finite and between"
                ):
                    simulator.validate_config(simulator.Config(rate=rate))

    def test_accepts_rate_boundaries(self) -> None:
        for rate in (0.001, simulator.MAX_RATE_HZ):
            with self.subTest(rate=rate):
                simulator.validate_config(simulator.Config(rate=rate))

    def test_rejects_port_outside_udp_range(self) -> None:
        for port in (0, 65536):
            with self.subTest(port=port):
                with self.assertRaisesRegex(ValueError, "--port must be between"):
                    simulator.validate_config(simulator.Config(port=port))

    def test_rejects_negative_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "--count must be zero or greater"):
            simulator.validate_config(simulator.Config(count=-1))

    def test_run_validates_before_opening_socket(self) -> None:
        with (
            mock.patch("simulator.telemetry_simulator.socket.socket") as socket_factory,
            self.assertRaises(ValueError),
        ):
            simulator.run(simulator.Config(rate=float("nan")))

        socket_factory.assert_not_called()


class SenderTest(unittest.TestCase):
    def test_udp_sender_transmits_requested_frame_count(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
            receiver.bind(("127.0.0.1", 0))
            receiver.settimeout(1)
            port = int(receiver.getsockname()[1])
            config = simulator.Config(port=port, rate=100.0, count=2)

            simulator.run(config)
            payloads = [receiver.recvfrom(1024)[0] for _ in range(2)]

        for payload in payloads:
            columns = payload.decode("utf-8").strip().split(",")
            self.assertEqual(len(columns), 6)

    def test_stdout_receives_the_same_frame(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            simulator.run(simulator.Config(rate=100.0, count=1, stdout=True))

        self.assertEqual(len(output.getvalue().strip().split(",")), 6)


class MainTest(unittest.TestCase):
    def test_main_returns_zero_after_success(self) -> None:
        with mock.patch.object(simulator, "run") as run:
            result = simulator.main(["--count", "1"])

        self.assertEqual(result, 0)
        run.assert_called_once()

    def test_main_returns_zero_after_keyboard_interrupt(self) -> None:
        with mock.patch.object(simulator, "run", side_effect=KeyboardInterrupt):
            result = simulator.main([])

        self.assertEqual(result, 0)

    def test_main_reports_expected_errors(self) -> None:
        stderr = io.StringIO()

        with (
            mock.patch.object(simulator, "run", side_effect=OSError("network down")),
            contextlib.redirect_stderr(stderr),
        ):
            result = simulator.main([])

        self.assertEqual(result, 1)
        self.assertEqual(stderr.getvalue(), "error: network down\n")


if __name__ == "__main__":
    unittest.main()
