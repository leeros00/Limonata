# include "Arduino.h"

// determine board type
#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
  String boardType = "Arduino Uno";
#elif defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega16U4__)
  String boardType = "Arduino Leonardo/Micro";
#elif defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
  String boardType = "Arduino Mega";
#else 
  String boardType = "Unknown board";
#endif

// Enable debugging output
const bool DEBUG = false;

// constants
const String vers = "0.0.0";   // version of this firmware
const long baud = 115200;      // serial baud rate
const char sp = ' ';           // command separator
const char nl = '\n';          // command terminator

const int pinF = 2;
const int pinQ = 3;

volatile int count; // for the flow meter

// probably don't need alarm limits for now

char Buffer[64];
int buffer_index = 0;
String cmd;
float val;

float P = 200;
float Q = 0;
//float F = 0;

boolean newData = false;

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
    sendResponse("Start");
  }
  else if (cmd == "P"){
    P = max(0, min(255, val));
  }
  else if (cmd == "Q"){
    setPump(val);
    sendFloatResponse(Q);
  }
  else if (cmd == "QB"){
    setPump(val);
    sendBinaryResponse(Q);
  }
  else if (cmd == "R"){
    sendFloatResponse(Q);
  }
  else if (cmd == "SCAN"){
    sendFloatResponse(readFlowRate());
    sendFloatResponse(Q);
  }
  else if (cmd == "F"){
    sendFloatResponse(readFlowRate());
  }
  else if (cmd == "FB"){
    sendBinaryResponse(readFlowRate());
  }
  else if (cmd == "VER"){
    sendResponse("Limonata Firmware version 0.0.0" + boardType);
  }
  else if (cmd == "X"){
    setPump(0);
    sendResponse("Stop");
  }
  else if (cmd.length() > 0){
    setPump(0);
    sendResponse(cmd);
  }
  Serial.flush();
  cmd = "";
}

// checking alarm ain't necessary...yet.

// same with updating status with LED

void setPump(float qval){
  Q = max(0., min(qval, 100.));
  analogWrite(pinQ, (Q*P)/100);
}

void rpm(){
  count++;
}


const int sensorPin = 2; // input pin for the hall effect sensor
volatile unsigned long flowCount; // variable to store the flow count
unsigned long flowRate; // variable to store the flow rate
unsigned long lastTime; // variable to store the last time the interrupt was triggered

  // if (millis() - lastTime >= 200) { // check if 1 second has passed
  //   detachInterrupt(digitalPinToInterrupt(sensorPin)); // detach the interrupt to prevent further counts
  //   flowRate = (float)flowCount * 100 / 7.5; // calculate the flow rate
  //   Serial.print("Flow rate: "); // print the flow rate to the serial monitor
  //   Serial.print(flowRate);
  //   Serial.println(" L/min");
  //   flowCount = 0; // reset the flow count
  //   lastTime = millis(); // update the last time
  //   attachInterrupt(digitalPinToInterrupt(sensorPin), countPulse, RISING); // reattach the interrupt
  // }

void setDefaultFlowRateValue(int timeInterval=200){
  // The intention of this method is to basically compute the flow rate in the background
  // TO DO: Make the params variable so we can optimize our predictive ability for water and other fluids
  // TO DO: Consider optimizing the parameters for sensing/predicting the flow with ML
  if (millis() - lastTime >= timeInterval){
    detachInterrupt(digitalPinToInterrupt(sensorPin));
    // TO DO: Consider finding a way to tune/optimize the weights of the flow sensor
    flowRate = (float)flowCount*100/7.5 
    Serial.print("Flow rate: ");
    Serial.print(flowRate);
    Serial.println(" L/min");
    flowCount = 0;
    lastTime = millis();
    attachInterrupt(digitalPinToInterrupt(sensorPin), countPulse, RISING);
  }
}

inline float readFlowRate(unsigned long longFlowRate=flowRate){
  // This method simply returns the most current flowRate value set by
  // Converting it to a float.
  // TO DO: Consider using a double, considering the precision.
  float floatFlowRate = (float)longFlowRate;
  return floatFlowRate;
}






// // TO DO: See if this conversion works for other apparati once we make more. 
// inline float readFlowRate(int pin){
//   float F = 0;
//   for (int i = 0; i < n; i++){
//     highTime = pulseIn(pin, HIGH);
//     lowTime  = pulseIn(pin, LOW);
//     period = lowTime + highTime;
//     freq = -period;
//     F = (freq*4.5)/2312.95;
//   }
//   return F/float(n); // L/min is the default
// }

void setup() {
  analogReference(EXTERNAL);
  
  while (!Serial){
    ; // This is where we wait for the serial port to connect.
  }
  Serial.begin(baud);
  Serial.flush();
  setPump(0);
  // Not sure if this will work...
  pinMode(pinF, INPUT);
  //attachInterrupt(0, rpm, RISING);
  
}
count = 0;
void loop() {
  readCommand();
  if (DEBUG) echoCommand();
  parseCommand();
  // TO DO: Consider figuring the optimal place for setDefaultFlowRateValue()
  setDefaultFlowRateValue();
  dispatchCommand();
  // TO DO: Figure out how fast this api loops irrespective of command presence...
  // If it loops irrespective of command, then we can count pulses irrespective of command for the flow meter
  Serial.println(count);
  count++;
}
