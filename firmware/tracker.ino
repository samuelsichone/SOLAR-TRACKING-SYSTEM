/*
  tracker.ino
  Dual-axis solar tracker (Arduino)
  - Reads 4 LDR sensors (A0..A3)
  - Controls 2 servos (azimuth & elevation)
  - Emits telemetry over Serial as JSON lines

  Wiring assumptions:
  A0: LDR_NE
  A1: LDR_NW
  A2: LDR_SE
  A3: LDR_SW
  Servo Azimuth -> pin 9
  Servo Elevation -> pin 10
*/

#include <Servo.h>

#define LDR_NE A0
#define LDR_NW A1
#define LDR_SE A2
#define LDR_SW A3

#define SERVO_AZ_PIN 9
#define SERVO_EL_PIN 10

// Calibration / control
const float AZ_GAIN = 0.8;   // proportional gain for azimuth
const float EL_GAIN = 0.8;   // proportional gain for elevation
const int AZ_MIN = 0;
const int AZ_MAX = 180;
const int EL_MIN = 0;
const int EL_MAX = 90;       // restrict elevation to safe range

// smoothing
const float ALPHA = 0.12;    // exponential smoothing factor

Servo servoAz;
Servo servoEl;

float azAngle = 90;   // start middle
float elAngle = 45;

unsigned long lastTelemetry = 0;
const unsigned long TELEMETRY_INTERVAL = 500; // ms

void setup() {
  Serial.begin(115200);
  servoAz.attach(SERVO_AZ_PIN);
  servoEl.attach(SERVO_EL_PIN);

  // Initialize positions
  servoAz.write((int)azAngle);
  servoEl.write((int)elAngle);

  delay(500);
}

int readLdr(int pin) {
  // returns 0..1023 (higher = brighter depending on wiring)
  return analogRead(pin);
}

void loop() {
  // Read raw sensors
  int ne = readLdr(LDR_NE);
  int nw = readLdr(LDR_NW);
  int se = readLdr(LDR_SE);
  int sw = readLdr(LDR_SW);

  // Convert to brightness values where larger = brighter
  // Compute left/right and top/bottom sums
  float left = nw + sw;
  float right = ne + se;
  float topv = ne + nw;
  float botv = se + sw;

  // Avoid divide by zero
  float horizontal_total = left + right + 1e-6;
  float vertical_total = topv + botv + 1e-6;

  // Error signals (-1..1)
  float horiz_err = (right - left) / horizontal_total; // positive -> need to move azimuth positive
  float vert_err = (topv - botv) / vertical_total;   // positive -> need to increase elevation

  // Desired angle changes (deg)
  float delta_az = AZ_GAIN * horiz_err * 10.0; // scale to degrees
  float delta_el = EL_GAIN * vert_err * 10.0;

  // Apply smoothing/exponential moving average
  azAngle = azAngle + ALPHA * (delta_az - (azAngle - azAngle)); // simplified smoothing (keeps angle incremental)
  // But above line is redundant; instead just increment with small smoothing:
  azAngle += ALPHA * delta_az;
  elAngle += ALPHA * delta_el;

  // Constrain to limits
  if (azAngle < AZ_MIN) azAngle = AZ_MIN;
  if (azAngle > AZ_MAX) azAngle = AZ_MAX;
  if (elAngle < EL_MIN) elAngle = EL_MIN;
  if (elAngle > EL_MAX) elAngle = EL_MAX;

  // Write servo positions
  servoAz.write((int)azAngle);
  servoEl.write((int)elAngle);

  // Simulated electrical telemetry (replace with real ADC readings if available)
  float ia = 0.08 + abs(delta_az) * 0.002; // A (simulated)
  float ib = 0.07 + abs(delta_el) * 0.002;
  float v = 12.0; // measured supply voltage placeholder

  // Send telemetry periodically
  unsigned long now = millis();
  if (now - lastTelemetry >= TELEMETRY_INTERVAL) {
    lastTelemetry = now;
    // Build JSON line (compact)
    Serial.print("{");
    Serial.print("\"t\":"); Serial.print(now);
    Serial.print(",\"az\":"); Serial.print((int)azAngle);
    Serial.print(",\"el\":"); Serial.print((int)elAngle);
    Serial.print(",\"pwm_az\":"); Serial.print((int)azAngle); // using angle as write value
    Serial.print(",\"pwm_el\":"); Serial.print((int)azAngle);
    Serial.print(",\"ia\":"); Serial.print(ia, 3);
    Serial.print(",\"ib\":"); Serial.print(ib, 3);
    Serial.print(",\"v\":"); Serial.print(v, 2);
    Serial.println("}");
  }

  delay(90); // main loop cadence
}
