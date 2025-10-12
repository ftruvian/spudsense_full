/*!
 * @file        getData.ino
 * @brief       this demo demonstrates how to put the sensor enter/exit sleep mode and get temperature data measured by sensor
 * @copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license     The MIT License (MIT)
 * @author      [qsjhyy](yihuan.huang@dfrobot.com)
 * @version     V1.0
 * @date        2021-08-09
 * @url         https://github.com/DFRobot/DFRobot_MLX90614
 */
#include <DFRobot_MLX90614.h>

DFRobot_MLX90614_I2C sensor;   // instantiate an object to drive our sensor

void setup()
{
 Serial.begin(9600); 
  // Wait for the serial port to be ready
  while (!Serial); 

  if (!sensor.begin()) {
    Serial.println("Error connecting to MLX90614 sensor. Check wiring.");
  } 
}

void loop()
{
  if (Serial.available() > 0) {

  String command = Serial.readStringUntil('\n'); 
  command.trim(); 

  float ambientTemp = sensor.getAmbientTempCelsius();
  float objectTemp = sensor.getObjectTempCelsius();
  //print values
  Serial.print(ambientTemp, 2);
  Serial.print(",");
  Serial.println(objectTemp, 2);
  //
  }
}
