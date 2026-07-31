from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKETCH = ROOT / "firmware" / "esp32_serial_studio_demo" / "esp32_serial_studio_demo.ino"


def strip_comments(source: str) -> str:
    """Drop `//` comments so assertions only see executable lines."""
    return "\n".join(line.split("//")[0] for line in source.splitlines())


class FirmwareLayoutTest(unittest.TestCase):
    def test_arduino_main_sketch_matches_directory_name(self) -> None:
        self.assertTrue(SKETCH.is_file())
        self.assertEqual(SKETCH.parent.name, SKETCH.stem)

    def test_firmware_constants_match_the_documented_protocol(self) -> None:
        source = SKETCH.read_text(encoding="utf-8")

        self.assertIn("constexpr uint32_t BAUD_RATE = 115200;", source)
        self.assertIn("constexpr int64_t SAMPLE_INTERVAL_US = 50000;", source)
        self.assertIn("constexpr int BUTTON_PIN = 0;", source)
        self.assertIn('Serial.printf("%.2f,%.2f,%.2f,%.4f,%.4f,%d\\n"', source)

    def test_uptime_uses_the_sixty_four_bit_timer(self) -> None:
        source = SKETCH.read_text(encoding="utf-8")

        self.assertIn("#include <esp_timer.h>", source)
        self.assertIn("esp_timer_get_time()", source)
        # millis() is named in a comment explaining why it is not used, so only
        # the executable lines are checked here.
        self.assertNotIn("millis()", strip_comments(source))

    def test_wave_phase_is_reduced_before_reaching_float(self) -> None:
        source = SKETCH.read_text(encoding="utf-8")

        self.assertIn("constexpr double SINE_PERIOD_S = 2.0;", source)
        self.assertIn("constexpr double TRIANGLE_PERIOD_S = 4.0;", source)
        self.assertIn("fmod(seconds, periodSeconds)", source)


if __name__ == "__main__":
    unittest.main()
