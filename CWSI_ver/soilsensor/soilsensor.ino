// This sketch handles five soil moisture sensors connected to A1 through A5.
// It responds to commands 'A', 'B', 'C', 'D', or 'E' by sending back the corresponding moisture percentage.

// --- Configuration ---
const long BAUD_RATE = 9600;

// Function to map the raw 10-bit analog reading (0-1023) to 
// a moisture percentage (e.g., 0.0 to 100.0).
float mapToMoisture(int analogValue) {
  // NOTE: Calibrate these values for your specific sensor!
  // Example: 0 (dry) maps to 0%, 600 (wet) maps to 100%.
  long mappedValue = map(analogValue, 767, 463, 0, 100); 
  
  if (mappedValue < 0) mappedValue = 0;
  if (mappedValue > 1000) mappedValue = 1000;
  
  // Return the result as a float percentage (e.g., 75.3)
  return mappedValue / 10.0;
}

void setup() {
  Serial.begin(BAUD_RATE); 
  // Wait for the serial port to be ready
  while (!Serial); 
  
  // Initialize all relevant analog pins (A1 through A5)
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  pinMode(A4, INPUT);
  pinMode(A5, INPUT);
}

void loop() {
  // Check if data is available to be read from the serial port
  if (Serial.available() > 0) {
    // Read the incoming data until a newline character is received
    String command = Serial.readStringUntil('\n'); 
    command.trim(); // Clean up any extra whitespace/CR/LF
    
    // We only care about the first character as the command ID
    char sensorID = command.charAt(0);
    
    int pinToRead = -1;
    float moisturePercent = -1.0;
    
    // 1. Determine which soil moisture sensor pin was requested
    switch (sensorID) {
      case 'A': pinToRead = A0; break;
      case 'B': pinToRead = A1; break;
      case 'C': pinToRead = A2; break;
      case 'D': pinToRead = A3; break;
      case 'E': pinToRead = A4; break;
      default:
        Serial.print("ERROR: Unknown command received: ");
        Serial.println(command);
        // Send a dummy error value
        Serial.println("-1.0"); 
        return; 
    }

    // 2. Read the selected soil moisture sensor pin
    int analogReading = analogRead(pinToRead);
    
    // 3. Convert the raw reading to a readable percentage
    moisturePercent = mapToMoisture(analogReading);
    
    // 4. Send ONLY the moisture percentage back, followed by a newline
    Serial.println(moisturePercent, 2); 

    // Print status to serial monitor for debugging
    Serial.print("-> Command ");
    Serial.print(sensorID);
    Serial.print(": Sent moisture value ");
    Serial.println(analogReading);
  }
}
