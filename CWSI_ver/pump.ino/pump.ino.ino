/**
 * @file pump_test.ino
 * @brief Arduino Sketch to test a pump connected via a 5V relay channel.
 * * This code repeatedly cycles the pump ON and OFF to verify the wiring, 
 * relay function, and pump operation.
 * * NOTE: Assumes Active-LOW relay module: LOW = ON, HIGH = OFF.
 */

// Define the digital pin connected to the relay controlling the pump.
const int PUMP_RELAY_PIN = 5; // Using Digital Pin D4 for the pump relay

// Define the ON and OFF times for the pump cycle (in milliseconds)
const int PUMP_ON_TIME = 3000; // 3 seconds ON
const int PUMP_OFF_TIME = 5000; // 5 seconds OFF

void setup() {
  // Start Serial communication
  Serial.begin(9600);
  Serial.println("--- Pump Relay Test Cycle Started ---");
  Serial.print("Pump controlled by Relay on Pin D");
  Serial.println(PUMP_RELAY_PIN);
  Serial.println("Cycle: 3s ON / 5s OFF");

  // Initialize the relay pin as an output
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  
  // Ensure the pump is initially OFF (HIGH for Active-LOW relay)
  digitalWrite(PUMP_RELAY_PIN, HIGH);
}

void loop() {
  // 1. Turn the Pump ON
  // Send LOW signal to the Active-LOW relay
  digitalWrite(PUMP_RELAY_PIN, LOW);
  Serial.print(millis());
  Serial.println(": PUMP ON (Relay LOW)");
  
  // Wait for the specified ON time
  delay(PUMP_ON_TIME);

  // 2. Turn the Pump OFF
  // Send HIGH signal to the Active-LOW relay
  digitalWrite(PUMP_RELAY_PIN, HIGH);
  Serial.print(millis());
  Serial.println(": PUMP OFF (Relay HIGH)");

  // Wait for the specified OFF time before repeating the cycle
  delay(PUMP_OFF_TIME);
}
