from __future__ import annotations

import importlib.util
import json
import pathlib
import socket
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SIMULATOR_PATH = ROOT / "simulator" / "telemetry_simulator.py"


def load_simulator():
    spec = importlib.util.spec_from_file_location("telemetry_simulator", SIMULATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load telemetry_simulator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TelemetryFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.simulator = load_simulator()

    def test_frame_has_six_numeric_columns_and_newline(self) -> None:
        frame = self.simulator.build_frame(12.5)
        self.assertTrue(frame.endswith("\n"))

        columns = frame.strip().split(",")
        self.assertEqual(len(columns), 6)
        values = [float(value) for value in columns]

        self.assertGreater(values[0], 0)
        self.assertGreater(values[1], 0)
        self.assertEqual(values[2], 12.5)
        self.assertGreaterEqual(values[3], -1)
        self.assertLessEqual(values[3], 1)
        self.assertGreaterEqual(values[4], -1)
        self.assertLessEqual(values[4], 1)
        self.assertIn(values[5], (0, 1))

    def test_button_toggles_every_five_seconds(self) -> None:
        released = self.simulator.build_frame(4.9).strip().split(",")[-1]
        pressed = self.simulator.build_frame(5.0).strip().split(",")[-1]
        released_again = self.simulator.build_frame(10.0).strip().split(",")[-1]

        self.assertEqual(released, "0")
        self.assertEqual(pressed, "1")
        self.assertEqual(released_again, "0")

    def test_udp_sender_transmits_one_frame(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
            receiver.bind(("127.0.0.1", 0))
            receiver.settimeout(1)
            port = receiver.getsockname()[1]
            args = types.SimpleNamespace(
                host="127.0.0.1",
                port=port,
                rate=20.0,
                count=1,
                stdout=False,
            )

            self.simulator.run(args)
            payload, _ = receiver.recvfrom(1024)

        columns = payload.decode("utf-8").strip().split(",")
        self.assertEqual(len(columns), 6)


class ProjectFileTest(unittest.TestCase):
    def load_project(self, name: str) -> dict:
        path = ROOT / "dashboard" / name
        return json.loads(path.read_text(encoding="utf-8"))

    def assert_common_project_shape(self, project: dict) -> None:
        self.assertEqual(project["schemaVersion"], 3)
        self.assertEqual(project["writerVersion"], "4.0.3")
        self.assertEqual(len(project["sources"]), 1)

        source = project["sources"][0]
        self.assertEqual(source["frameDetection"], 0)
        self.assertEqual(source["frameEnd"], "\n")
        self.assertEqual(source["frameParserLanguage"], 2)
        self.assertEqual(source["frameParserTemplate"], "delimited")
        self.assertEqual(source["frameParserParams"]["separator"], ",")

        datasets = [
            dataset
            for group in project["groups"]
            for dataset in group["datasets"]
        ]
        self.assertEqual(len(datasets), 6)
        self.assertEqual(sorted(dataset["index"] for dataset in datasets), list(range(1, 7)))
        self.assertEqual(len({dataset["uniqueId"] for dataset in datasets}), 6)

    def test_uart_project(self) -> None:
        project = self.load_project("esp32_serial_dashboard.ssproj")
        self.assert_common_project_shape(project)

        source = project["sources"][0]
        self.assertEqual(source["busType"], 0)
        self.assertEqual(source["connection"]["baudRate"], 10)
        self.assertEqual(source["connection"]["dataBitsIndex"], 3)

    def test_udp_project(self) -> None:
        project = self.load_project("desktop_udp_dashboard.ssproj")
        self.assert_common_project_shape(project)

        source = project["sources"][0]
        self.assertEqual(source["busType"], 1)
        self.assertEqual(source["connection"]["socketTypeIndex"], 1)
        self.assertEqual(source["connection"]["udpLocalPort"], 9000)


if __name__ == "__main__":
    unittest.main()
