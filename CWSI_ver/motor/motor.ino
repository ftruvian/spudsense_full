const long BAUD_RATE = 9600;

// Motor Specifications (42SHDC3025 is typically 1.8 degrees per step)
const int STEPS_PER_REV = 200; 

// Driver Pins (Connect these to the Arduino Digital Pins)
// This is the standard wiring for A4988/DRV8825 drivers.
// NOTE: Pins were corrected to standard D8/D9 as 83 is not a valid Arduino pin.
const int STEP_PIN = 3; // Pin used to trigger the motor movement (pulses)
const int DIR_PIN = 2;  // Pin used to set the motor direction (HIGH/LOW)

// --- State Management ---
const int STEPS_PER_MOVE = 800; // The fixed steps for one regular move
const int HOMING_CYCLE = 5;     // Number of moves (1-5) before the reversal is triggered
// Total steps to reverse: 5 moves * 100 steps/move = 500 steps
const int CUMULATIVE_STEPS = STEPS_PER_MOVE * HOMING_CYCLE; 

volatile int moveCount = 0; // Tracks the number of movements since last home

// --- Setup ---
void setup() {
  Serial.begin(BAUD_RATE); 
  
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  Serial.println("Motor Controller Ready (42SHDC3025 Configured). Send 'M' to execute fixed move.");
}

// Function to move the motor a specific number of steps at a given speed
void moveMotor(int steps, bool clockwise, int delay_micros) {
  // Set direction: HIGH for CW, LOW for CCW (or vice-versa, depending on wiring)
  digitalWrite(DIR_PIN, clockwise ? HIGH : LOW);
  
  // Execute steps by pulsing the STEP pin
  for (int i = 0; i < abs(steps); i++) {
    // Pulse HIGH
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(delay_micros); 
    
    // Pulse LOW
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(delay_micros); // Determines speed: lower delay = faster
  }
}

// --- Loop ---
void loop() {
  // Check if data is available to be read from the serial port
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); 
    command.trim(); 
    
    char triggerCommand = command.charAt(0);
    
    // Check for the trigger command (M for Move)
    if (triggerCommand == 'M') {
      
      const int speedDelay = 800;     // Delay in microseconds (adjust this value to control speed)
      
      // --- Check for Homing Condition FIRST (triggered by the 6th 'M') ---
      if (moveCount >= HOMING_CYCLE) {
          // This block runs when moveCount is 5 (on the 6th 'M' command)
          
          Serial.println("\n--- HOMING CYCLE STARTING (6th 'M' received) ---");
          Serial.print("Reversing cumulative ");
          Serial.print(CUMULATIVE_STEPS);
          Serial.println(" steps...");

          // Move the motor in the opposite direction to return to start
          const bool reverseDirection = false; // Counter-Clockwise
          moveMotor(CUMULATIVE_STEPS, reverseDirection, speedDelay);
          
          moveCount = 0; // Reset counter
          Serial.println("--- HOMING COMPLETE. Counter reset. ---\n");

      } else {
          // --- Execute Fixed Forward Movement (Moves 1 through 5) ---
          
          const bool direction = true;    // Regular move direction (Clockwise)
          
          Serial.print("Received 'M'. Executing move #"); 
          Serial.print(moveCount + 1); // Print next move number (1-5)
          Serial.print(" of "); Serial.print(HOMING_CYCLE);
          Serial.print(": "); Serial.print(STEPS_PER_MOVE);
          Serial.println(" steps...");
          
          // Move the motor
          moveMotor(STEPS_PER_MOVE, direction, speedDelay);
          
          // Increment counter (0 -> 1, 4 -> 5)
          moveCount++;
          
          Serial.println("Move complete.");
      }
    } else {
      Serial.print("Received unknown command: ");
      Serial.println(command);
    }
  }
}
