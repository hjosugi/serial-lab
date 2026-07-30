#include <Arduino.h>
#include <math.h>

namespace {

constexpr uint32_t BAUD_RATE = 115200;
constexpr uint32_t SAMPLE_INTERVAL_MS = 50;
constexpr int BUTTON_PIN = 0;
constexpr float TWO_PI_F = 6.28318530717958647692f;

float triangleWave(const float phase) {
  return (2.0f / PI) * asinf(sinf(phase));
}

void sendTelemetry(const uint32_t nowMs) {
  const float uptimeSeconds = static_cast<float>(nowMs) / 1000.0f;
  const float chipTemperatureC = temperatureRead();
  const float freeHeapKiB = static_cast<float>(ESP.getFreeHeap()) / 1024.0f;
  const float sine = sinf(TWO_PI_F * 0.50f * uptimeSeconds);
  const float triangle = triangleWave(TWO_PI_F * 0.25f * uptimeSeconds);
  const int buttonPressed = digitalRead(BUTTON_PIN) == LOW ? 1 : 0;

  Serial.printf("%.2f,%.2f,%.2f,%.4f,%.4f,%d\n",
                chipTemperatureC,
                freeHeapKiB,
                uptimeSeconds,
                sine,
                triangle,
                buttonPressed);
}

}  // namespace

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.begin(BAUD_RATE);
  delay(500);
}

void loop() {
  static uint32_t lastSampleMs = 0;
  const uint32_t nowMs = millis();

  if (nowMs - lastSampleMs < SAMPLE_INTERVAL_MS) {
    delay(1);
    return;
  }

  lastSampleMs = nowMs;
  sendTelemetry(nowMs);
}

