/*
Limonata Firmware
Ross Lee
September 2023
*/

#include "Arduino.h"
#include <max6675.h>
#if defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
  String boardType = "Arduino Mega";
#elif defined(__ARDUINO_ARCH_STM32) || defined(ARDUINO_GIGA)
  String boardType = "Arduino Giga";
#else
  String boardType = "Unknown board";
#endif

// TODO: implement debugging option?
//const bool DEBUG = false;

const String version = "0.0.0"; // firmware version
const long baudRate = 115200; // serial baud rate
const char sp = ' '; // command separator
const char nl = '\n'; // command terminator

// TODO: Figure out what pins on an Arduino will correspond to the
// sensors
const int pinRedTempDO    = 50;
const int pinRedTempCS    = 53;
const int pinRedTempCLK   = 52;
const int pinQ            = 9;

// Temperature alarm boundaries
const int limRedTemp = 50; // degrees Celsius
// TODO: Add LEDs and speaker alarm
// Global variables
char Buffer[64];
int buffer_index = 0;
String cmd;
float val;
int alarmStatus; // TODO: Add in parts for the alarm

float P = 255; // Power limit in PWM
float Q = 0; // Last value written to the red vessel, the reactor

boolean newData = false; // Boolean flag for new command
int nTempSamples = 10; // Number of temperature samples for each temperature measurement



void readCommand() {
  while (Serial && (Serial.available() > 0) && (newData == false)) {
    int byte = Serial.read();
    if ((byte != '\r') && (byte != nl) && (buffer_index < 64)) {
      Buffer[buffer_index] = byte;
      buffer_index++;
    }
    else {
      newData = true;
    }
  }   
}

// for debugging with the serial monitor in Arduino IDE
void echoCommand() {
  if (newData) {
    Serial.write("Received Command: ");
    Serial.write(Buffer, buffer_index);
    Serial.write(nl);
    Serial.flush();
  }
}


inline float readTemperature(int pinDO, int pinCS, int pinCLK){
  MAX6675 thermocouple(pinCLK, pinCS, pinDO);
  float temperature = 0.0;
  for (int i=0; i < nTempSamples; i++){
    temperature += thermocouple.readCelsius();
  }
  return temperature/float(nTempSamples);
}


void parseCommand(void){
  if (newData){
    String read_ = String(Buffer);
    int idx = read_.indexOf(sp);
    cmd = read_.substring(0, idx);
    cmd.trim();
    cmd.toUpperCase();

    String data = read_.substring(idx + 1);
    data.trim();
    val = data.toFloat();

    memset(Buffer, 0, sizeof(Buffer));
    buffer_index = 0;
    newData = false;
  }
}


void sendResponse(String message){
  Serial.println(message);
}


void sendFloatResponse(float val){
  Serial.println(String(val, 3));
}


void sendBinaryResponse(float val){
  byte *b = (byte*)&val;
  Serial.write(b, 4);
}


void dispatchCommand(void){
  if (cmd == "A"){
    setHeater(0);
    sendResponse("Start");
  }
  else if (cmd == "P"){
    P = max(0, min(255, val));
    sendResponse(String(P));
  }
  else if (cmd == "Q"){
    setHeater(val);
    sendFloatResponse(Q);
  }
  else if (cmd == "SCAN"){
    sendFloatResponse(readTemperature(pinRedTempDO, pinRedTempCS, pinRedTempCLK));
    sendFloatResponse(Q);
  }
  else if (cmd == "T"){
    sendFloatResponse(readTemperature(pinRedTempDO, pinRedTempCS, pinRedTempCLK));
  }
  else if (cmd == "VERSION"){
    sendResponse("Limonata Firmware " + version + " " + boardType);
  }
  else if (cmd == "X"){
    setHeater(0);
    sendResponse("Stop");
  }
  else if (cmd.length() > 0){
    setHeater(0);
    sendResponse(cmd);
  }
  Serial.flush();
  cmd = "";
}


void setHeater(float qval){
  Q = max(0., min(qval, 100.));
  analogWrite(pinQ, (Q*P)/100);
}


void setup() {
  analogReference(EXTERNAL);
  while (!Serial){
    ;
  }
  Serial.begin(baudRate);
  Serial.flush();
  setHeater(0);
  //ledTimeout = millis() + 1000;
}


void loop() {
  readCommand();
  //if (DEBUG) echoCommand();
  parseCommand();
  dispatchCommand();
}
