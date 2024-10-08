#include <max6675.h>

/*
Limonata Firmware
Ross Lee
September 2024

First, many thanks to all who contributed to this firmware or at least,
inspired it. This would include a list of, but not limited to, John
Hedengren, Jeffrey Kantor, and all those who helped create the TCLab.

This project is loosely based on the TCLab, except it is effectively 
a flexible prototyping device - a hybrid CSTR/batch reactor.  
This firmware interfaces to the Limonata Potenza device at a high level
via scanning the serial port for commands. Commands are case-insensitive and
unrecognized commands result in sleep model, just like the TCLab. Each
command returns a resulting string. 

// TODO: Finish commentary
  A   software restart. Returns "Start".
  LED float
*/

// TODO: Include library compatibility for STM32 boards, particularly
// the Arduino Giga and STM32H5 and STM32H7.
#include "Arduino.h"
#if defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
  String boardType = "Arduino Mega";
#elif defined(__ARDUINO_ARCH_STM32) || defined(ARDUINO_GIGA)
  String boardType = "Arduino Giga";
#else
  String boardType = "Unknown board";
#endif
#include <max6675.h>
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
const int pinRedHeaterQ   = 9;

// Temperature alarm boundaries
const int limRedTemp = 50; // degrees Celsius

// TODO: Add LEDs and speaker alarm

// Global variables
char Buffer[64];
int bufferIndex = 0;
String cmd;
float val;
int alarmStatus; // TODO: Add in parts for the alarm

float redHeaterP = 255; // Power limit in PWM
float redHeaterQ = 0; // Last value written to the red vessel, the reactor

boolean newData = false; // Boolean flag for new command
int nTempSamples = 10; // Number of temperature samples for each temperature measurement


void readCommand() {
  while (Serial && (Serial.available() > 0) && (newData = false)) {
    int byte = Serial.read();
    if ((byte != '\r') && (byte != nl) && (bufferIndex < 64)) {
      Buffer[bufferIndex] = byte;
      bufferIndex++;
    }
    else {
      newData = true;
    }
  }
}

// TODO: Consider adding in an echoCommand() for serial monitor debugging

void setRedHeater(float qVal) {
  redHeaterQ = max(0.0, min(qVal, 100.0));
  analogWrite(pinRedHeaterQ, (redHeaterQ*redHeaterP)/100);
}

inline float readTemperature(int pinDO, int pinCS, int pinCLK){
  MAX6675 thermocouple(pinCLK, pinCS, pinDO);
  float temperature = 0.0;
  for (int i=0; i < nTempSamples; i++){
    temperature += thermocouple.readCelsius();
  }
  return temperature/float(nTempSamples);
}

void parseCommand(void) {
  if (newData) {
    String read_ = String(Buffer);

    int i = read_.indexOf(sp);
    cmd = read_.substring(0, i);
    cmd.trim();
    cmd.toUpperCase();
    String data = read_.substring(i+1);
    data.trim();
    val = data.toFloat();
    
    memset(Buffer, 0, sizeof(Buffer));
    bufferIndex = 0;
    newData = false;
  }
}

void respond(String message) {
  Serial.println(message);
}

void floatRespond(float val) {
  Serial.println(String(val, 3));
}

void binaryRespond(float val) {
  byte *b = (byte*)&val;
  Serial.write(b, 4);
}

void doCommand(void) {
  if (cmd == "A") {
    setRedHeater(0);
    respond("Start");
  }
  else if (cmd == "redHeaterP") {
    redHeaterP = max(0, min(255, val));
    respond(String(redHeaterP));
  }
  else if (cmd == "redHeaterQ") {
    setRedHeater(val);
    floatRespond(redHeaterQ);
  }
  else if (cmd == "redHeaterQB") {
    setRedHeater(val);
    binaryRespond(redHeaterQ);
  }
  else if (cmd == "SCAN") {
    floatRespond(readTemperature(pinRedTempDO, pinRedTempCS, pinRedTempCLK));
    floatRespond(redHeaterQ);
  }
  else if (cmd == "redT") {
    floatRespond(readTemperature(pinRedTempDO, pinRedTempCS, pinRedTempCLK));
  }
  else if (cmd == "VERSION") {
    respond("Limonata Firmware " + version + " " + boardType);
  }
  else if (cmd == "X") {
    setRedHeater(0);
    respond("Stop");
  }
  else if (cmd.length() > 0) {
    setRedHeater(0);
    respond(cmd);
  }
  Serial.flush();
  cmd = "";
}


void setup() {
  while (!Serial){
    ;
  }
  Serial.begin(baudRate);
  Serial.flush();
  setRedHeater(0);
}

void loop() {
  readCommand();
  parseCommand();
  doCommand();
}
