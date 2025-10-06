/**
 * @file relay_test.ino
 * @brief Arduino Sketch for testing a 5-channel relay board.
 * * This sketch cycles through 5 digital pins (D4, D6, D8, D10, D12), 
 * activating each connected relay for 1 second.
 * * NOTE: Most common relay modules are Active-LOW, meaning:
 * - LOW signal (GND) = Relay ON (Green LED lights up)
 * - HIGH signal (5V) = Relay OFF
 */

// Define the digital pins connected to the relay board IN pins.
const int relayPins[] = {4, 6, 8, 10, 12};
const int numRelays = sizeof(relayPins) / sizeof(relayPins[0]);

// Time in milliseconds to keep the relay ON (1 second)
const int activationTime = 1000; 

void setup() {
  // Initialize Serial communication for debugging and status messages
  Serial.begin(9600);
  Serial.println("--- 5-Channel Relay Test Started ---");
  Serial.println("Relay logic: Active-LOW (LOW = ON)");

  // Initialize all relay pins as outputs and ensure they are all OFF (HIGH) initially.
  for (int i = 0; i < numRelays; i++) {
    pinMode(relayPins[i], OUTPUT);
    
    // Set HIGH to keep the relay initially OFF (Active-LOW logic)
    digitalWrite(relayPins[i], HIGH); 
    
    Serial.print("Initialized Pin D");
    Serial.print(relayPins[i]);
    Serial.println(" to OFF (HIGH)");
  }

  delay(2000); // Wait 2 seconds before starting the test cycle
}

void loop() {
  // Loop through each relay pin in the array
  for (int i = 0; i < numRelays; i++) {
    int currentPin = relayPins[i];
    
    // 1. Activate the Relay (Set LOW for Active-LOW module)
    digitalWrite(currentPin, LOW);
    Serial.print("-> Activating Relay on Pin D");
    Serial.print(currentPin);
    Serial.println(" (LOW = ON). Green LED should be lit.");
    
    // Wait for the specified activation time
    delay(activationTime); 

    // 2. Deactivate the Relay (Set HIGH for Active-LOW module)
    digitalWrite(currentPin, HIGH);
    Serial.print("<- Deactivating Relay on Pin D");
    Serial.print(currentPin);
    Serial.println(" (HIGH = OFF). Green LED should be off.");

    // Short pause before testing the next relay
    delay(500); 
  }

  Serial.println("--- Test Cycle Complete. Repeating in 3 seconds. ---");
  delay(3000); // Wait 3 seconds before starting the entire cycle again
}
