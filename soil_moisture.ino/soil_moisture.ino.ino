const int DRY_VALUE = 767; 
const int WET_VALUE = 463; 

int selectedAnalogPinIndex = -1;

void setup() {
  Serial.begin(9600);
  Serial.println("--- DFRobot Soil Moisture Sensor Reader ---");
  Serial.println("Enter a number (0-4) to read sensor connected to Analog Pin A0-A4.");
  Serial.println("e.g., Enter '2' to read sensor on A2.");
}

int calculateMoisturePercentage(int rawReading) {
  long moisturePercentage = map(rawReading, WET_VALUE, DRY_VALUE, 100, 0);
  return constrain(moisturePercentage, 0, 100);
}

void loop() {
  if (Serial.available() > 0) {
    char inputChar = Serial.read();

    selectedAnalogPinIndex = inputChar - '0';

    if (selectedAnalogPinIndex >= 0 && selectedAnalogPinIndex <= 4) {
      int analogPin = selectedAnalogPinIndex; 

      int rawReading = analogRead(analogPin);
      
      int percentage = calculateMoisturePercentage(rawReading);

      Serial.println("------------------------------------------");
      Serial.print("Reading Sensor on Analog Pin A");
      Serial.print(selectedAnalogPinIndex);
      Serial.println(":");
      Serial.print("Raw ADC Value: ");
      Serial.println(rawReading);
      Serial.print("Moisture Percentage: ");
      Serial.print(percentage);
      Serial.println("%");
      Serial.println("------------------------------------------");
      
    } else {
      Serial.print("Invalid input: '");
      Serial.print(inputChar);
      Serial.println("'. Please enter a number between 0 and 4.");
    }
  }
  
  delay(10); 
}
