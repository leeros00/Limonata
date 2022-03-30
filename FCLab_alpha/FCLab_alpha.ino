/*
 * 
 * NOTE:
 * While the original code was intended for the TCLab, the main goal now of this file is to build a flow controller with Arduino
 * All the notes after these asterixes are based on the notes given from the TCLab-sketch.ino file.
 * What we will need to do is examine the firmware and software in detail to understand how the methods work.
 * Of utmost importance is to first dissect and comment the firmware so we know how all methods are called. 
 * Then, we will examine how the Python files are called via Dr. Hedengren's software.
 * Once we understand how everything is compiled and called, we will be able to create our own methods for the flow controller.
 * 
 * n
  TCLab Temperature Control Lab Firmware
  Jeffrey Kantor, Bill Tubbs, John Hedengren, Shawn Summey
  February 2021

  This firmware provides a high level interface to the Temperature Control Lab. The
  firmware scans the serial port for commands. Commands are case-insensitive. Any
  unrecognized command results in sleep model. Each command returns a result string.

  A         software restart. Returns "Start".
  LED float set LED to float for 10 sec. range 0 to 100. Returns actual float
  pumpPower float  set pwm limit on heater 1, range 0 to 255. Default 200. Returns pumpPower.
  valvePower float  set pwm limit on heater 2, range 0 to 255. Default 100. Returns valvePower.
  pumpQ float  set Heater 1, range 0 to 100. Returns value of pumpQ.
  valveQ float  set Heater 2, range 0 to 100. Returns value of valveQ.
  pumpQB float set Heater 1, range 0 to 100. Returns value of pumpQ as a 32-bit float.
  valveQB float set Heater 2, range 0 to 100. Returns value of valveQ as a 32-bit float.
  R1        get value of Heater 1, range 0 to 100
  R2        get value of Heater 2, range 0 to 100
  SCAN      get values T1 T2 pumpQ pumpQ in line delimited values
  T1        get Temperature T1. Returns value of T1 in °C.
  T2        get Temperature T2. Returns value of T2 in °C.
  T1B       get Temperature T1. Returns value of T1 in °C as a 32-bit float.
  T2B       get Temperature T2. Returns value of T2 in °C as a 32-bit float.
  VER       get firmware version string
  X         stop, enter sleep mode. Returns "Stop"

  Limits on the heater power can be configured with the constants below.

  Status is indicated by LED1 on the Temperature Control Lab. Status conditions are:

      LED1        LED1
      Brightness  State
      ----------  -----
      dim         steady     Normal operation, heaters off
      bright      steady     Normal operation, heaters on
      dim         blinking   High temperature alarm on, heaters off
      bright      blinking   High temperature alarm on, heaters on

  The Temperature Control Lab shuts down the heaters if it receives no host commands
  during a timeout period (configure below), receives an "X" command, or receives
  an unrecognized command from the host.

  Constants are used to configure the firmware.

  Changelog ordered by Semantic Version
  
      1.0.1 first version included in the tclab package
      1.1.0 added R1 and R2 commands to read current heater values
            changed heater values to units of percent of full power
            added pumpPower and valvePower commands to set heater power limits
            changed readCommand to avoid busy states
            changed simplified LED status model
      1.2.0 added LED command
      1.2.1 fixed reset heater values on close
            added version history
      1.2.2 changed version string for better display by TCLab
      1.2.3 changed baudrate to from 9600 to 115200
      1.3.0 added SCAN function 
            added board type in version string
      1.4.0 changed pumpQ and valveQ to float from int
      1.4.1 fixed missing Serial.flush() at end of command loop
      1.4.2 fixed bug with X command
      1.4.3 deprecated use of Arduino IDE Version < 1.0.0
      1.5.0 removed webusb
      1.6.0 changed temperature to average 10 measurements to reduce noise
      2.0.0 added binary communications.
            added T1B and T2B commands return 32-bit float
            added pumpQB and valveQB commands return 32-bit float confirmation of heater setting
            added calculation to use 1.75 AREF to match TMP36 voltage range 
      2.0.1 added updates to Notre Dame and BYU versions of this firmware
            changed version history to standard change log practices

*/


// Note: This part is for including the necessary Arduino recognition files.
// My best guess is that it somehow identifies the microcontroller and spits
// out the type of Arduino connected. We will want this for the FCLab.

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

// TO DO: Figure out what they mean by 'Enable debugging output'.
// Why does it need to be 'false'?

// Enable debugging output
const bool DEBUG = false;

// TO DO: We probably don't need the version, for now.
// Or, we could just say that the vers is like 0.0.1 or something,
// because this is basically the alpha.

// Questions: Why do we need to establish the baud serial as such?
// Also, why do we need the command separator and terminators? 
// Where is this called in the .py files?

// constants
const String vers = "0.0.0";   // version of this firmware
const long baud = 115200;      // serial baud rate
const char sp = ' ';           // command separator
const char nl = '\n';          // command terminator

// TO DO: After we get a good design for wiring the Arduino to a power source
// and MOSFET driver with the 12 V DC pump, we will need write the 
// correct pins for the PWM.

// pin numbers corresponding to signals on the TC Lab Shield
const int pinFlowMeter = 2;  // flow meter
const int pinPumpQ     = 3;  // pump power
const int pinValveQ    = 5;  // control valve
const int pinAgitatorQ = 6;  // CSTR agitator/stir bar
const int pinLED1      = 12; // LED1

// TO DO: Change this part to be appropriate for flow control ie. flowrate, pressure
// temperature alarm limits
const int limVdot1   = 50;       // flow high alarm (arbitrary for now)

// LED1 levels
const int hiLED   =  60;       // hi LED
const int loLED   = hiLED/16;  // lo LED

// TO DO: Figure out what the buffer and indices mean
// figure out why the floats are initialized the way they are.
// figure out what the boolean means/is for.

// global variables
char Buffer[64];               // buffer for parsing serial input
int buffer_index = 0;          // index for Buffer
String cmd;                    // command
float val;                     // command value
int ledStatus;                 // 1: loLED
                               // 2: hiLED
                               // 3: loLED blink
                               // 4: hiLED blink
long ledTimeout = 0;           // when to return LED to normal operation
float LED = 100;               // LED override brightness
float pumpPower = 200;                // heater 1 power limit in units of pwm. Range 0 to 255
float valvePower = 100;                // heater 2 power limit in units in pwm, range 0 to 255
float pumpQ = 0;                  // last value written to heater 1 in units of percent
float valveQ = 0;                  // last value written to heater 2 in units of percent
float agitatorQ = 0;
int alarmStatus;               // hi flow alarm status
boolean newData = false;       // boolean flag indicating new command
int n =  10;                   // number of samples for each temperature measurement


// TO DO: What does this readCommand() function do?

// What do 'Serial' and 'Serial.available()' do? What is the significance of > 0?
// if (Serial) (or if(SerialUSB) on the Due) indicates whether or not the USB CDC serial connection is open. 
// if (Serial.available() > 0) means proceed/true if there is any data received (ie, not 0).
// So the first line means that while there is a serial connection and it is receiving data

// What is newData and why does newData have to be false in the conditions?
// newData is a flag of some kind to proceed. See here: https://forum.arduino.cc/t/serial-input-basics-updated/382007

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

// TO DO: For the flow controller lab, we will want this to be edited for a flow meter.
// Or, even better yet, we use this type of method as a basis for designing all of our 
// sensors, like flow meters, pressure sensors, etc. The datasheet params will be different,
// but the concept should be pretty similar across the board, but we will likely need several of these
// functions for our various sensor applications.

// return average  of n reads of flow meter in [whatever units are given]
inline float readFlowRate(int pin) {
  float flow = 0.0;
  for (int i = 0; i < n; i++) {
    // TO DO: Adjust for the regression parameters from the flowmeter datasheet.
    flow += analogRead(pin)/7.5;    // use for 3.3v AREF, should give it L/min
    //flow += analogRead(pin) * 0.170898438 - 50.0;  // use for 1.75v AREF
  }
  return flow / float(n);
}

inline float readValve(int pin) {
  float valve = 0.0;
  for (int i = 0; i < n; i++) {
    // TO DO: Again, adjust for the regression parameters from the flowmeter datasheet.
    valve += analogRead(pin)*0.322265625 - 50.0;    // use for 3.3v AREF
    //valve += analogRead(pin) * 0.170898438 - 50.0;  // use for 1.75v AREF
  }
  return valve / float(n);
}

// TO DO: So many questions about this part...
// What does 'parse' mean in this context of an embedded circuit?
// Again, I'm failing to understand the buffer. What does it do??
// What is indexOf()?
// What is substring()?
// What is trim()?
// What is toUpperCase()?
// Why do we need to data.trim()? What does that do?
// What does memset() do?
// What does sizeof do? Why are we doing that to the buffer?

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

// TO DO: Figure out the exact syntax and meaning of the Serial.println() method

void sendResponse(String msg) {
  Serial.println(msg);
}

void sendFloatResponse(float val) {
  Serial.println(String(val, 3));
}

// TO DO: Try to remember what the significance of an asterix is in C++...(pointer??) and for the single '&'.
// What does Serial.write() do? I would think it would mean write something to the serial monitor, but what then,
// would be the difference between that and Serial.println()?

void sendBinaryResponse(float val) {
  byte *b = (byte*)&val;
  Serial.write(b, 4);  
}

// TO DO: Figure out the big picture behind dispatchCommand(). My guess is that it does just that--sends the command.
// BUT. We need to know exactly how this works. Even if that means being OCD and a pain in the ass about it. (:

// So I didn't even know you could put a void inside of a void method...what the heck does that do??

// What does millis() mean? Milliseconds? Why is the method added to other numbers...?

void dispatchCommand(void) {
  if (cmd == "A") {
    setPump(0);
    setControlValve(0);
    sendResponse("Start");
  }
  else if (cmd == "LED") {
    ledTimeout = millis() + 10000;
    LED = max(0, min(100, val));
    sendResponse(String(LED));
  }
  else if (cmd == "pumpPower") {
    pumpPower = max(0, min(255, val));
    sendResponse(String(pumpPower));
  }
  else if (cmd == "valvePower") {
    valvePower = max(0, min(255, val));
    sendResponse(String(valvePower));
  }
  else if (cmd == "pumpQ") {
    setPump(val);
    sendFloatResponse(pumpQ);
  }
  else if (cmd == "pumpQB") {
    setPump(val);
    sendBinaryResponse(pumpQ);
  }
  else if (cmd == "valveQ") {
    setControlValve(val);
    sendFloatResponse(valveQ);
  }
  else if (cmd == "valveQB") {
    setPump(val);
    sendBinaryResponse(valveQ);
  }
  else if (cmd == "R1") {
    sendFloatResponse(pumpQ);
  }
  else if (cmd == "R2") {
    sendFloatResponse(valveQ);
  }
  else if (cmd == "SCAN") {
    sendFloatResponse(readFlowRate(pinFlowMeter));
    sendFloatResponse(readValve(pinValveQ));
    sendFloatResponse(pumpQ);
    // TO DO: Necessary??
    sendFloatResponse(valveQ);
  }
  else if (cmd == "Vdot1") {
    sendFloatResponse(readFlowRate(pinFlowMeter));
  }
  else if (cmd == "Vdot1b") {
    sendBinaryResponse(readFlowRate(pinFlowMeter));
  }
  else if (cmd == "VER") {
    sendResponse("FlowE Firmware " + vers + " " + boardType);
  }
  else if (cmd == "X") {
    setPump(0);
    setControlValve(0);
    sendResponse("Stop");
  }
  else if (cmd.length() > 0) {
    setPump(0);
    setControlValve(0);
    sendResponse(cmd);
  }
  Serial.flush();
  cmd = "";
}

// TO DO: Potentially modify this to use a piezo buzzer to signal with sound too.

void checkAlarm(void) {
  if (readFlowRate(pinFlowMeter) > limVdot1) {
    alarmStatus = 1;
  }
  else {
    alarmStatus = 0;
  }
}

// TO DO: What status are we updating? Like the decision of the controller to a device (like a thermistor?)?

// What do cases do?

// What are the two arguments in analogWrite used for?

// What does 'switch' do??

// What EXACTLY does 'break' do?

// Remind me, what does the % operator do in C++?

void updateStatus(void) {
  // determine led status
  ledStatus = 1;
  if ((pumpQ > 0) or (valveQ > 0)) {
    ledStatus = 2;
  }
  if (alarmStatus > 0) {
    ledStatus += 2;
  }
  // update led depending on ledStatus
  if (millis() < ledTimeout) {        // override led operation
    analogWrite(pinLED1, LED);
  }
  else {
    switch (ledStatus) {
      case 1:  // normal operation, heaters off
        analogWrite(pinLED1, loLED);
        break;
      case 2:  // normal operation, heater on
        analogWrite(pinLED1, hiLED);
        break;
      case 3:  // high temperature alarm, heater off
        if ((millis() % 2000) > 1000) {
          analogWrite(pinLED1, loLED);
        } else {
          analogWrite(pinLED1, loLED/4);
        }
        break;
      case 4:  // high temperature alarm, heater on
        if ((millis() % 2000) > 1000) {
          analogWrite(pinLED1, hiLED);
        } else {
          analogWrite(pinLED1, loLED);
        }
        break;
    }   
  }
}

// TO DO: I could be wrong, but I think these are the types of functions that would
// take our serial information from Python to use as arguments. Find that out.
// Then, if that is the case, we will want to change this to function as a flow PWM.

// set Pump
void setPump(float qval) {
  pumpQ = max(0., min(qval, 100.));
  analogWrite(pinPumpQ, (pumpQ*pumpPower)/100);
}

// set Control Valve
void setControlValve(float qval) {
  valveQ = max(0., min(qval, 100.));
  analogWrite(pinValveQ, (valveQ*valvePower)/100);
}

// TO DO: Create a void function for the CSTR agitator control
// set CSTR Motor Control
void setAgitator(float qval) {
  agitatorQ = max(0., min(qval, 100.));
  analogWrite(pinValveQ, (valveQ*valvePower)/100);
}

// TO DO: This part will probably be basically the same as the TCLab.
// Find out what Serial.flush() means.
// We will probably need to get the setHeater() methods to be setFlow() or something like that.

// arduino startup
void setup() {
  analogReference(EXTERNAL);
  while (!Serial) {
    ; // wait for serial port to connect.
  }
  Serial.begin(baud);
  Serial.flush();
  setPump(0);
  setControlValve(100);
  setAgitator(0);
  ledTimeout = millis() + 1000;
}

// TO DO (or rather, NOT DO): This part will likely be very similar to the TCLab. 
// When it comes to installing the firmware manually, do we literally just need to verify and
// upload it like we would with any other Arduino sketch or is there another way we will need
// to install the firmware?

// arduino main event loop
void loop() {
  readCommand();
  if (DEBUG) echoCommand();
  parseCommand();
  dispatchCommand();
  checkAlarm();
  updateStatus();
}
