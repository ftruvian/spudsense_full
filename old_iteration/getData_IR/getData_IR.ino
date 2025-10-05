#include <DFRobot_MLX90614.h>
#include <Wire.h> // Required for I2C communication (used by MLX90614)

// --- Pin Definitions ---
const int MOISTURE_SENSOR_PIN = A0; // Analog pin connected to the soil moisture sensor

// --- Sensor Calibration Values ---
// Raw ADC reading for 0% moisture (driest)
const int MOISTURE_DRY_VALUE = 767;
// Raw ADC reading for 100% moisture (wettest)
const int MOISTURE_WET_VALUE = 463;

// --- Sensor Objects ---
// Create an instance of the MLX90614 sensor
// Default I2C address is 0x5A
DFRobot_MLX90614_I2C mlx; 

// --- Timing ---
const long INTERVAL = 2000; // Time in milliseconds between readings (2 seconds)
unsigned long previousMillis = 0; // Will store the last time the data was sent

void setup() {
  // Initialize Serial communication at 9600 baud rate
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect. Needed for native USB port boards
  }
  
  // Initialize I2C communication and the MLX90614 sensor
  Wire.begin();
  mlx.begin();
  
  Serial.println("Soil Moisture (%),Object Temp (C)"); // Print header for CSV
}

void loop() {
  unsigned long currentMillis = millis();

  // Check if the defined interval has passed
  if (currentMillis - previousMillis >= INTERVAL) {
    previousMillis = currentMillis;

    // 1. Read Soil Moisture Sensor
    int rawMoisture = analogRead(MOISTURE_SENSOR_PIN);
    
    // 2. Convert Raw Moisture to Percentage
    // The map function can be used for linear conversion:
    // map(value, fromLow, fromHigh, toLow, toHigh)
    // Here, 767 -> 0 and 463 -> 100
    long moisturePercentage = map(rawMoisture, MOISTURE_DRY_VALUE, MOISTURE_WET_VALUE, 0, 100);
    
    // Clamp the percentage to be between 0 and 100 in case readings go out of range
    if (moisturePercentage < 0) {
      moisturePercentage = 0;
    } else if (moisturePercentage > 100) {
      moisturePercentage = 100;
    }

    // 3. Read MLX90614 Object Temperature
    // Read the object temperature in Celsius
    int sensorValue = analogRead(A0);
    float ambientTemp = sensor.getAmbientTempCelsius();
    float objectTemp = sensor.getObjectTempCelsius();

    // 4. Send Data to Raspberry Pi via Serial Port (in CSV format)
    // The format will be: <Moisture Percentage>,<Object Temperature C>
    Serial.print(sens);
    Serial.print(",");
    Serial.print(ambientTemp, 2);
    Serial.println(objectTemp, 2); // Print temperature with 2 decimal places
  }
}
