#include <Wire.h>
#include <Adafruit_MLX90614.h>

Adafruit_MLX90614 mlx = Adafruit_MLX90614();
const int soilMoisturePin = A0;

void setup() {
  Serial.begin(9600);
  if (!mlx.begin()) {
    while (1);
  }
}

void loop() {
  // Countdown before reading
  for (int i = 3; i > 0; i--) {
    Serial.print("Reading in... ");
    Serial.println(i);
    delay(1000);
  }
  Serial.println(); // Add a blank line for readability

  // Read temperatures
  float ambientTemp = mlx.readAmbientTempC();
  float objectTemp = mlx.readObjectTempC();
  
  // Average 10 soil moisture readings
  long moistureSum = 0;
  for (int i = 0; i < 10; i++) {
    moistureSum += analogRead(soilMoisturePin);
    delay(50);
  }
  float moisturePercentage = 100 - (((float)moistureSum / 10) / 1023.0) * 100;
  
  // Print values to the serial monitor for debugging
  Serial.print(ambientTemp);
  Serial.print(",");
  Serial.print(objectTemp);
  Serial.print(",");
  Serial.println(moisturePercentage);

  // Send data to RPi as a single comma-separated string
  String dataString = String(ambientTemp) + "," + String(objectTemp) + "," + String(moisturePercentage);
  Serial.println(dataString);
  
  delay(10000);
}

