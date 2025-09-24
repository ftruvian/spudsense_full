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
#include <Wire.h>
#include <DFRobot_MLX90614.h>

DFRobot_MLX90614_I2C sensor;   // instantiate an object to drive our sensor

const int soilPins[] = {A0, A1, A2, A3};  // 4 soil moisture sensors
const int numSensors = sizeof(soilPins) / sizeof(soilPins[0]);
int currentSensor = 0;

void setup()
{
  Serial.begin(9600);
  
  // initialize the sensor
  while( NO_ERR != sensor.begin() ){
    Serial.println("Communication with device failed, please check connection");
    delay(3000);
  }
  Serial.println("Begin ok!");

  /** adjust sensor sleep mode select to enter or exit sleep mode, it's enter sleep mode by default
   *  true is to enter sleep mode
   *  false is to exit sleep mode (automatically exit sleep mode after power down and restart) */
  sensor.enterSleepMode();
  delay(50);
  sensor.enterSleepMode(false);
  delay(200);
}

void loop()
{
  // soil moisture sensors
  int moisture1 = analogRead(soilPins[currentSensor]);

  // moisture percentage
  float moistper1 = (moisture1 / 300) * 100;

  /**
   * get ambient temperature, unit is Celsius
   * return value range： -40.01 °C ~ 85 °C
   */
  float ambientTemp = sensor.getAmbientTempCelsius();

  /**
   * get temperature of object 1, unit is Celsius
   * return value range： 
   * @n  -70.01 °C ~ 270 °C(MLX90614ESF-DCI)
   * @n  -70.01 °C ~ 380 °C(MLX90614ESF-DCC)
   */
  float objectTemp = sensor.getObjectTempCelsius();

  // print measured data in Celsius
  Serial.print(ambientTemp); Serial.print(",");
  Serial.print(objectTemp); Serial.print(",");

  // print soil moisture
  Serial.println(moisture1);

  // print measured data in Fahrenheit
  // Serial.print("Ambient fahrenheit : "); Serial.print(ambientTemp*9/5 + 32); Serial.println(" F");
  // Serial.print("Object fahrenheit : ");  Serial.print(objectTemp*9/5 + 32);  Serial.println(" F");
  delay(5000);
}

