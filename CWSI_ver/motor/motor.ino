const long BAUD_RATE = 9600;

// Motor Specifications (42SHDC3025 is typically 1.8 degrees per step)
const int STEPS_PER_REV = 200; 

const int STEP_PIN = 3; // Pin used to trigger the motor movement (pulses)
const int DIR_PIN = 2;  // Pin used to set the motor direction (HIGH/LOW)

// --- State Management ---
const int STEPS_PER_MOVE = 600; // The fixed steps for one regular move
const int MOVES = 5;     // Number of moves (1-5) before the reversal is triggered
const int TOTAL_STEPS = (STEPS_PER_MOVE * MOVES) - 100; 

int moveCount = 0; // Tracks the number of movements since last home

void setup() {
  Serial.begin(BAUD_RATE); 
  
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  Serial.println("Motor Controller Ready (42SHDC3025 Configured). Send 'M' to execute fixed move.");
}

void moveMotor(int steps, bool clockwise, int speedDelay) {
  // Set direction: HIGH for CW, LOW for CCW (or vice-versa, depending on wiring)
  digitalWrite(DIR_PIN, clockwise ? LOW : HIGH);
  
  // Execute steps by pulsing the STEP pin
  for (int i = 0; i < abs(steps); i++) {
    // Pulse HIGH
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(speedDelay); 
    
    // Pulse LOW
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(speedDelay); // Determines speed: lower delay = faster
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
      
      const int speedDelay = 700;     // speed
      
      // --- Check for Homing Condition FIRST (triggered by the 6th 'M') ---
      if (moveCount >= MOVES) {
          // This block runs when moveCount is 5 (on the 6th 'M' command)
          
          Serial.println("\n--- HOMING CYCLE STARTING (6th 'M' received) ---");
          Serial.print("Reversing");
          Serial.print(TOTAL_STEPS);
          Serial.println(" steps...");

          // Move the motor in the opposite direction to return to start
          const bool reverseDirection = false; // Counter-Clockwise
          moveMotor(TOTAL_STEPS, reverseDirection, speedDelay);
          
          moveCount = 0; 
          Serial.println("--- HOMING COMPLETE. Counter reset. ---\n");

      } else {
          // --- Execute Fixed Forward Movement (Moves 1 through 5) ---
          
          const bool direction = true;    // Clockwise
          
          Serial.print("Received 'M'. Executing move #");

          moveCount++;
          Serial.print(moveCount + 1); 
          Serial.print(" of "); Serial.print(MOVES);
          Serial.print(": "); Serial.print(STEPS_PER_MOVE);
          Serial.println(" steps...");
          
          moveMotor(STEPS_PER_MOVE, direction, speedDelay);
          
          Serial.println("Move complete.");
      }
    } else {
      Serial.print("Received unknown command: ");
      Serial.println(command);
    }
  }
}
