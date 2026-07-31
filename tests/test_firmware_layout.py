from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKETCH = ROOT / "firmware" / "esp32_serial_studio_demo" / "esp32_serial_studio_demo.ino"


class FirmwareLayoutTest(unittest.TestCase):
    def test_arduino_main_sketch_matches_directory_name(self) -> None:
        self.assertTrue(SKETCH.is_file())
        self.assertEqual(SKETCH.parent.name, SKETCH.stem)

    def test_firmware_constants_match_the_documented_protocol(self) -> None:
        source = SKETCH.read_text(encoding="utf-8")

        self.assertIn("constexpr uint32_t BAUD_RATE = 115200;", source)
        self.assertIn("constexpr uint32_t SAMPLE_INTERVAL_MS = 50;", source)
        self.assertIn("constexpr int BUTTON_PIN = 0;", source)
        self.assertIn('Serial.printf("%.2f,%.2f,%.2f,%.4f,%.4f,%d\\n"', source)


if __name__ == "__main__":
    unittest.main()
