from __future__ import annotations

import json
import pathlib
import unittest
from typing import Any, cast

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "dashboard"
UART_PROJECT = "esp32_serial_dashboard.ssproj"
UDP_PROJECT = "desktop_udp_dashboard.ssproj"

# Supported maximum continuous run time. The firmware reports uptime from a
# 64-bit timer, so the Meter range is the only limit on how long the dashboard
# stays readable.
MAX_UPTIME_S = 86400

EXPECTED_GROUPS = (
    ("ESP32 System", "", ("Chip Temperature", "Free Heap", "Uptime")),
    ("Generated Waveforms", "multiplot", ("Sine Wave", "Triangle Wave")),
    ("Digital Input", "datagrid", ("BOOT Button",)),
)

EXPECTED_DATASETS = (
    (1, "Chip Temperature", "deg C", "gauge", 0, 100),
    (2, "Free Heap", "KiB", "bar", 0, 400),
    (3, "Uptime", "s", "meter", 0, MAX_UPTIME_S),
    (4, "Sine Wave", "", "", -1, 1),
    (5, "Triangle Wave", "", "", -1, 1),
    (6, "BOOT Button", "", "", 0, 1),
)


def load_project(name: str) -> dict[str, Any]:
    path = DASHBOARD_DIR / name
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def datasets(project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        cast(dict[str, Any], dataset)
        for group in project["groups"]
        for dataset in group["datasets"]
    ]


class ProjectFileTest(unittest.TestCase):
    uart: dict[str, Any]
    udp: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.uart = load_project(UART_PROJECT)
        cls.udp = load_project(UDP_PROJECT)

    def assert_common_project_shape(self, project: dict[str, Any]) -> None:
        self.assertEqual(project["schemaVersion"], 3)
        self.assertEqual(project["writerVersion"], "4.0.3")
        self.assertEqual(project["writerVersionAtCreation"], "4.0.3")
        self.assertEqual(project["pointCount"], 500)
        self.assertEqual(project["plotTimeRange"], 20)
        self.assertEqual(len(project["sources"]), 1)

        source = project["sources"][0]
        self.assertEqual(source["sourceId"], 0)
        self.assertEqual(source["frameDetection"], 0)
        self.assertEqual(source["frameStart"], "")
        self.assertEqual(source["frameEnd"], "\n")
        self.assertEqual(source["frameParserLanguage"], 2)
        self.assertEqual(source["frameParserTemplate"], "delimited")
        self.assertEqual(source["frameParserParams"]["separator"], ",")
        self.assertTrue(source["frameParserParams"]["trimFields"])

        project_datasets = datasets(project)
        self.assertEqual(len(project_datasets), 6)
        self.assertEqual(
            sorted(dataset["index"] for dataset in project_datasets),
            list(range(1, 7)),
        )

    def test_uart_project(self) -> None:
        self.assert_common_project_shape(self.uart)

        source = self.uart["sources"][0]
        self.assertEqual(source["busType"], 0)
        self.assertEqual(source["title"], "ESP32 UART")
        self.assertEqual(
            source["connection"],
            {
                "autoReconnect": True,
                "baudRate": 10,
                "dataBitsIndex": 3,
                "dtr": True,
                "flowControlIndex": 0,
                "parityIndex": 0,
                "portIndex": 0,
                "stopBitsIndex": 0,
            },
        )

    def test_udp_project(self) -> None:
        self.assert_common_project_shape(self.udp)

        source = self.udp["sources"][0]
        self.assertEqual(source["busType"], 1)
        self.assertEqual(source["title"], "Desktop UDP Simulator")
        self.assertEqual(
            source["connection"],
            {
                "address": "127.0.0.1",
                "socketTypeIndex": 1,
                "udpLocalPort": 9000,
                "udpMulticast": False,
                "udpRemotePort": 9000,
            },
        )

    def test_dashboard_definitions_do_not_drift_between_transports(self) -> None:
        shared_keys = set(self.uart) - {"sources", "title"}

        for key in shared_keys:
            with self.subTest(key=key):
                self.assertEqual(self.uart[key], self.udp[key])

    def test_groups_match_the_documented_dashboard_contract(self) -> None:
        groups = self.uart["groups"]
        actual = tuple(
            (
                group["title"],
                group["widget"],
                tuple(dataset["title"] for dataset in group["datasets"]),
            )
            for group in groups
        )

        self.assertEqual(actual, EXPECTED_GROUPS)

    def test_datasets_match_the_six_column_csv_contract(self) -> None:
        actual = tuple(
            (
                dataset["index"],
                dataset["title"],
                dataset["units"],
                dataset["widget"],
                dataset["widgetMin"],
                dataset["widgetMax"],
            )
            for dataset in datasets(self.uart)
        )

        self.assertEqual(actual, EXPECTED_DATASETS)

    def test_group_and_dataset_identifiers_are_consistent(self) -> None:
        groups = self.uart["groups"]
        unique_ids: list[int] = []

        for expected_group_id, group in enumerate(groups):
            self.assertEqual(group["groupId"], expected_group_id)
            unique_ids.append(group["uniqueId"])
            for expected_dataset_id, dataset in enumerate(group["datasets"]):
                self.assertEqual(dataset["groupId"], expected_group_id)
                self.assertEqual(dataset["datasetId"], expected_dataset_id)
                unique_ids.append(dataset["uniqueId"])

        self.assertEqual(sorted(unique_ids), list(range(1, 10)))
        self.assertEqual(self.uart["nextUniqueId"], max(unique_ids) + 1)


if __name__ == "__main__":
    unittest.main()
