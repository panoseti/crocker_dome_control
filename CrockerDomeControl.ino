// Crocker Dome Control JRo 11/21/23
// Lower floor lights and fan, dome rotation
// com 4 is dome
#include <Encoder.h>
#include <SoftwareSerial.h>
#include <avr/wdt.h>

SoftwareSerial Serial1(5,4);                           // RX, TX may need to swap for HC-12 radio
String command;

int Fan = A1; int LL = A2; int DP = A3; int DN = A4;    // assigns pin A1-A4 to Relays
int PN = 9; int PS = 10; int PE = 11; int PW = 12;      // assigns pin 9-12 cardinal inputs
long oAZ = 0;
#define go2
#define prk
Encoder DomeEnc(2, 3);                                  // 360PPR Encoder For Dome Rotation

const unsigned long eventTime_1_LDR = 100; // interval in ms
const unsigned long eventTime_2_temp = 12000;
unsigned long previousTime_1 = 0;
unsigned long previousTime_2 = 0;

///////////////////////////////////VOID SETUP/////////////////////////////////////

void setup() {
  Serial.begin(9600); Serial1.begin(9600); Serial.println("Dome Control"); Serial1.println("Dome Control");                                     // Begin Serials
  pinMode(Fan, OUTPUT); pinMode(LL, OUTPUT); pinMode(DP, OUTPUT); pinMode(DN, OUTPUT);                        // Declares Relay Outputs
  pinMode(PN, INPUT_PULLUP); pinMode(PS, INPUT_PULLUP); pinMode(PE, INPUT_PULLUP); pinMode(PW, INPUT_PULLUP); // Magbetic Switch For Cardinals
  Fan, LOW; LL, LOW; DP, LOW; DN, LOW;}                                                                       // Take all relays low on reset

void(* resetFunc) (void) = 0; //declare reset function @ address 0

///////////////////////////////////////VOID LOOP/////////////////////////////////////////////

void loop() {

/////////////////////////////////////ENCODER READ////////////////////////////////////////////

long newPosition = DomeEnc.read(); if (newPosition < 0) DomeEnc.write (115199); else if (newPosition > 115199) DomeEnc.write (0);
long AZ = map(newPosition, 0, 115201, 0, 360); if (AZ != oAZ) {oAZ = AZ; Serial.print("Azimuth = "); Serial.println(AZ);}

///////////////////////////CARDINAL POINT MAGNETIC SWITCHES//////////////////////////////////

int sensorValN = digitalRead(9);  if (sensorValN == LOW) {DomeEnc.write (0);}      // Read the Magnetic switches for Cardinal points update
int sensorValS = digitalRead(10); if (sensorValS == LOW) {DomeEnc.write (28800);}  // Read the Magnetic switches for Cardinal points update
int sensorValE = digitalRead(11); if (sensorValE == LOW) {DomeEnc.write (57600);}  // Read the Magnetic switches for Cardinal points update This will likely be Park/Home
int sensorValW = digitalRead(12); if (sensorValW == LOW) {DomeEnc.write (86400);}  // Read the Magnetic switches for Cardinal points update

/////////////////////////////////////////GOTO & PARK///////////////////////////////////////////

go2  //newPosition = DomeEnc.read(); if (newPosition < 0) DomeEnc.write (115199); else if (newPosition > 115199) DomeEnc.write (0);

prk // goto 270

//resetFunc(); //call reset //Watchdog timer
//unsigned long currentTime = millis();
/* This is event 1 stuff */
//if( currentTime - previousTime_1 >= eventTime_1_LDR ){
  //Serial1.println ("WD1R");
  //Serial.println( analogRead(LDR) );
  /* Update the timing for the next event */
  //previousTime_1 = currentTime;

//}
// To Do: Event 2 timing
//if( currentTime - previousTime_2 >= eventTime_2_temp ){

  //Serial1.println ("WD2R");
  //Serial.println( analogRead(tempSensor) );
  /* Update the timing for the next event */
  //previousTime_2 = currentTime;
//}

///////////////////////////////////SHUTTER CONTROL TO POCO/////////////////////////////////////

if (Serial1.available()) {Serial.write(Serial1.read());}                           // If anything comes from Serial1 send to POCO

///////////////////////////////////SERIAL LISTEN COMMANDS//////////////////////////////////////

if (Serial.available()) {command = Serial.readStringUntil('\n'); command.trim();                       // Listen To POCO

///////////////////////////////////////////RELAYS//////////////////////////////////////////////

    if      (command.equals("SFO")) {digitalWrite (Fan, HIGH);}                                        // Seeing Fan On
    else if (command.equals("SFo")) {digitalWrite (Fan, LOW);}                                         // Seeing Fan Off
    else if (command.equals("FLO")) {digitalWrite (LL,  HIGH);}                                        // Floor Lights On
    else if (command.equals("FLo")) {digitalWrite (LL,  LOW);}                                         // Floor Lights Off
    else if (command.equals("+DO")) {digitalWrite (DN,  LOW); delay(1000); digitalWrite (DP, HIGH);}   // Dome Positive On
    else if (command.equals("+Do")) {digitalWrite (DP,  LOW);}                                         // Dome Positive Off
    else if (command.equals("-DO")) {digitalWrite (DP,  LOW); delay(1000); digitalWrite (DN, HIGH);}   // Dome Negative On
    else if (command.equals("-Do")) {digitalWrite (DN,  LOW);}                                         // Dome Negative Off
    else if (command.equals("PRK")) {digitalWrite (DN,  LOW);}                                         // Goto Park Position
    else if (command.equals("RDP")) {Serial.print("RDP = "); Serial.println(AZ);}                      // Report Dome Position
    else if (command.equals("RSD")) {Serial.print("RSD");}                                             // Reset Dome Controller

///////////////////////////////////////PASS THROUGH COMMANDS//////////////////////////////////

    else if (command.equals("WD1R")) {Serial1.println("WD1R");}                                          // Watchdog Timer 1 Reset
    else if (command.equals("WD2R")) {Serial1.println("WD2R");}                                           // Watchdog Timer 2 Reset
    else if (command.equals("LO"))    {Serial1.println("LO");}                                       // Upper Lights On
    else if (command.equals("Lo"))    {Serial1.println("Lo");}                                       // Upper Lights Off
    else if (command.equals("FO"))    {Serial1.println("FO");}                                       // Flatfield ON
    else if (command.equals("Fo"))    {Serial1.println("Fo");}                                       // Flatfield OFF
    else if (command.equals("USO"))   {Serial1.println("USO");}                                      // Upper Shutter Open
    else if (command.equals("USC"))   {Serial1.println("USC");}                                      // Upper Shutter Close
    else if (command.equals("LSO"))   {Serial1.println("LSO");}                                      // Lower Shutter Open
    else if (command.equals("LSC"))   {Serial1.println("LSC");}                                      // Lower Shutter Close
    else if (command.equals("RFO"))   {Serial1.println("RFO");}                                      // Rain Fly Open
    else if (command.equals("RFC"))   {Serial1.println("RFC");}                                      // Rain Fly Close
    else if (command.equals("CAP"))   {Serial1.println("CAP");}                                      // Cap The Dome
    else if (command.equals("CLS"))   {Serial1.println("CLS");}                                      // Close Both Shutters
    else if (command.equals("USS"))   {Serial1.println("USS");}                                      // Upper Shutter Stop
    else if (command.equals("LSS"))   {Serial1.println("LSS");}                                      // Lower Shutter Stop
    else if (command.equals("BSS"))   {Serial1.println("BSS");}                                      // Both Shutter Stop
    else if (command.equals("RUP"))   {Serial1.println("RUP");}                                      // Report Upper Position
    else if (command.equals("RLP"))   {Serial1.println("RLP");}                                      // Report Lower Position
    else if (command.equals("RBV"))   {Serial1.println("RBV");}                                      // Report Voltage Battery
    else if (command.equals("RCV"))   {Serial1.println("RCV");}                                      // Report Voltage Conroller
    else if (command.equals("RSC"))   {Serial1.println("RSC");}                                      // Reset Shutter Controller
    else {}}
    if (Serial1.available()) {command = Serial1.readStringUntil('\n'); command.trim();   // Listen To Shutter
    if (command.equals("WD1R"))   {Serial1.println("WD1R");}


    }}
