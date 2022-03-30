/*
Limonata* Chemical Printer Firmware 
Ross Lee
March 2022

*Note: Name is not set in stone, but rather is the first thing I thought of calling this thing because
Arduino is Italian, the first lab is making lemonade, and Firmata is what Arduino uses to read serial information...aka
Limon-at-a!!!

 */

# include "Arduino.h"

// determine board type
# if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
  String boardType = "Arduino Uno";
# elif defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega16U4__)
  String boardType = "Arduino Leonardo/Micro";
# elif defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
  String boardType = "Arduino Mega";
# else 
  String boardType = "Unknown board";
# endif

// enable the debugging output
const bool DEBUG = false;

// constants
const String vers = "0.0.0"; // firmware version
const long baud   = 115200;  // serial baud rate
const char sp     = ' ';     // command separator
const char nl     = '\n';    // command terminator

const int pinT         = 0;
const int pinFlow      = 2;
const int pinPumpQ     = 3;
const int pinValveQ    = 5;
const int pinAgitatorQ = 6;
const int pinLED       = 9;

// global variables
char Buffer[64];
int buffer_index = 0;
String cmd; 
float val;
int ledStatus;


long ledTimeout  = 0;
float LED        = 100;
float pumpP      = 0;
float valveP     = 0; // Because it is a fail close valve, it may be best to initialize at 255 at some point? 
float agitatorP  = 0;
int alarmStatus;
boolean newData  = false;
int n            = 10;

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

void echoCommand() {
  if (newData) {
    Serial.write("Received Command: ");
    Serial.write(Buffer, buffer_index);
    Serial.write(nl);
    Serial.flush();
  }
}

inline float readFlowRate(int pin) {
  float flow = 0.0;
  for (int i = 0; i < n; i++) {
    // TO DO: Adjust for the regression parameters from the flowmeter datasheet.
    flow += analogRead(pin)/7.5;  // to get it reading in L  // use for 3.3v AREF
  }
  return flow/float(n); // Why are we dividing by 10?? Average?
}

void parseCommand(void) {
  if (newData) {
    String read_ = String(Buffer);

    // separate command from associated data
    int idx = read_.indexOf(sp);
    cmd = read_.substring(0, idx);
    cmd.trim();
    cmd.toUpperCase();

    // extract data. toFloat() returns 0 on error
    String data = read_.substring(idx + 1);
    data.trim();
    val = data.toFloat();

    // reset parameter for next command
    memset(Buffer, 0, sizeof(Buffer));
    buffer_index = 0;
    newData = false;
  }
}

void sendResponse(String msg) {
  Serial.println(msg);
}

void sendFloatResponse(float val) {
  Serial.println(String(val, 3));
}

void sendBinaryResponse(float val) {
  byte *b = (byte*)&val;
  Serial.write(b, 4);  
}

void dispatchCommand(void){
  if (cmd == "A"){
    setPump(0);
    setControlValve(255);
    setAgitator(0);
    sendResponse("Start");
  }
  else if (cmd == "LED"){
    ledTimeout = millis() + 10000;
    LED = max(0, min(100, val));
    sendResponse(String(LED));
  }
  else if (cmd == "pumpP"){
    pumpP = max(0, min(255, val));
    sendResponse(String(pumpP));
  }
  else if (cmd == "valveP"){
    valveP = max(0, min(255, val));
    sendResponse(String(valveP));
  }
  else if (cmd == "agitatorP"){
    agitatorP = max(0, min(255, val));
    sendResponse(String(agitatorP));
  }
  else if (cmd == "pumpQ"){
    setPump(val);
    sendFloatResponse(pumpQ);
  }
  else if (cmd == "pumpQB"){
    setPump(val);
    sendBinaryResponse(pumpQ);
  }
  else if (cmd == "valveQ"){
    setValve(val);
    sendFloatResponse(valveQ);
  }
  else if (cmd == "valveQB"){
    setValve(val);
    sendBinaryResponse(valveQ);
  }
  else if (cmd == ""
  else if (cmd == "R1"){
    sendFloatResponse(
  }
}

void setPump(float qval){
  pumpQ = max(0., min(qval, 100.);
  analogWrite(pin
}
setControlValve(255);
setAgitator(0);

void setup() {
  analogReference(EXTERNAL);
  while (!Serial) {
    ; // wait for serial port to connect.
  }
  
  Serial.begin(baud);
  Serial.flush();
  setPump(0);
  setControlValve(0);
  setAgitator(0);
  
  ledTimeout = millis() + 1000;

}

void loop() {
  readCommand();
  if (DEBUG) echoCommand();
  parseCommand();
  dispatchCommand();
  checkAlarm();
  updateStatus();
}
