// Arduino Pump Controller Sketch
// This sketch listens for a single sensor ID (e.g., "A") from the Raspberry Pi. 
// Receiving a valid ID serves as the direct command to activate the corresponding pump
// for a fixed duration. The RPi handles all CWSI decision logic.

#include <string.h>

// --- Configuration ---
const int PUMP_PINS[] = {8, 9, 10, 11, 12}; 
const char* PUMP_COMMANDS = "ABCDE"; 

// FIXED duration for pump activation
const float PUMP_DURATION = 5.0; 

// --- Setup ---
void setup() {
  Serial.begin(9600);
  
  // Set all pump pins as outputs and ensure pumps start OFF (HIGH if Active LOW relay)
  for (int i = 0; i < 5; i++) {
    pinMode(PUMP_PINS[i], OUTPUT);
    digitalWrite(PUMP_PINS[i], HIGH); // Assumes Active LOW relay (HIGH = OFF)
  }
  Serial.println("Pump Controller Ready. Send format: ID (e.g., A) for watering.");
}

// Function to activate the pump for a specific, timed duration (using hardcoded PUMP_DURATION).
void activatePumpTimed(int pinIndex, char command) {
    long durationMillis = (long)PUMP_DURATION * 1000;
    
    // Turn pump ON (Active LOW)
    digitalWrite(PUMP_PINS[pinIndex], LOW); 
    Serial.print("Pump "); Serial.print(command);
    Serial.print(" ACTIVATED for "); Serial.print(PUMP_DURATION); Serial.println(" seconds.");
    
    // Block the Arduino for the duration.
    delay(durationMillis);
    
    // Turn pump OFF (Active LOW)
    digitalWrite(PUMP_PINS[pinIndex], HIGH); 
    Serial.print("Pump "); Serial.print(command); Serial.println(" DEACTIVATED.");
}

// --- Loop ---
void loop() {
  if (Serial.available() > 0) {
    // Read only the first character (the pump ID)
    char command = Serial.read(); 
    
    // Find which pump pin index corresponds to the command
    int sensorIndex = -1;
    for (int i = 0; i < 5; i++) {
      if (PUMP_COMMANDS[i] == command) {
        sensorIndex = i;
        break;
      }
    }
    
    if (sensorIndex != -1) {
      // If a valid ID is received, activate the pump immediately.
      activatePumpTimed(sensorIndex, command); 
    } else {
        Serial.print("Received invalid command: ");
        Serial.println(command);
    }
  }
}
