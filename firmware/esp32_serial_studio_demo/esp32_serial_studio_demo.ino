#include <Arduino.h>
#include <esp_timer.h>
#include <math.h>

namespace {

constexpr uint32_t BAUD_RATE = 115200;
constexpr int64_t SAMPLE_INTERVAL_US = 50000;
constexpr int BUTTON_PIN = 0;
constexpr double TWO_PI_D = 6.28318530717958647692;
constexpr double SINE_PERIOD_S = 2.0;
constexpr double TRIANGLE_PERIOD_S = 4.0;

// esp_timer_get_time() counts microseconds since boot in a signed 64-bit
// counter, so uptime keeps rising for the life of the board. millis() is
// 32-bit and returns to zero after about 49.7 days.
double uptimeSeconds(const int64_t nowUs) {
  return static_cast<double>(nowUs) / 1000000.0;
}

// Reduce the phase to a single period while still in double precision. An
// unreduced phase reaches ~271000 rad after 24 h, where a 32-bit float
// resolves only ~0.03 rad and the plotted wave visibly steps.
float wavePhase(const double seconds, const double periodSeconds) {
  return static_cast<float>(TWO_PI_D * fmod(seconds, periodSeconds) /
                            periodSeconds);
}

float triangleWave(const float phase) {
  return (2.0f / PI) * asinf(sinf(phase));
}

void sendTelemetry(const double uptimeS) {
  const float chipTemperatureC = temperatureRead();
  const float freeHeapKiB = static_cast<float>(ESP.getFreeHeap()) / 1024.0f;
  const float sine = sinf(wavePhase(uptimeS, SINE_PERIOD_S));
  const float triangle = triangleWave(wavePhase(uptimeS, TRIANGLE_PERIOD_S));
  const int buttonPressed = digitalRead(BUTTON_PIN) == LOW ? 1 : 0;

  Serial.printf("%.2f,%.2f,%.2f,%.4f,%.4f,%d\n",
                chipTemperatureC,
                freeHeapKiB,
                uptimeS,
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
  static int64_t lastSampleUs = 0;
  const int64_t nowUs = esp_timer_get_time();

  if (nowUs - lastSampleUs < SAMPLE_INTERVAL_US) {
    delay(1);
    return;
  }

  lastSampleUs = nowUs;
  sendTelemetry(uptimeSeconds(nowUs));
}
