/*
  Lora Send And Receive
  This sketch demonstrates how to send and receive data with the MKR WAN 1300 LoRa module.
  This example code is in the public domain.

  Edits by Ryan Conte, Wireless Biosensing Laboratory, UNH Undergraduate Research
*/

#include <MKRWAN.h>

LoRaModem modem;
int seconds = 0;

// Uncomment if using the Murata chip as a module
// LoRaModem modem(Serial1);

#include "arduino_secrets.h"
// Please enter your sensitive data in the Secret tab or arduino_secrets.h
//currently configured for prototyping with a single MKR1300 board. As it stands we have to get one of each of these from ttn for each unique device flash.
String appEui = "70B3D57ED0022BC0";
String appKey = "4921DA14704F4C2A5CAE6314C154F8FB";
String devAddr = "2602242F";
String nwkSKey = "CD2B4A81C409F9B5A7F154CDAB700C3B";
String appSKey = "B06ED62B9D34C4E7C851CBEE13B6C30B";

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial);
  
  // change this to your regional band (eg. US915, AS923, ...)
  if (!modem.begin(US915)) {
    Serial.println("Failed to start module");
    while (1) {}
  }
  Serial.print("Your module version is: ");
  Serial.println(modem.version());
  Serial.print("Your device EUI is: ");
  Serial.println(modem.deviceEUI());
  /*if(!(modem.power(PABOOST, 0))){
    Serial.println("Failed to change power settings");  
  }
  //if(!dataRate( dr)*/

  //Attempt to connect to a network until it goes through. Never seems to connect on the first attempt
  int connected = 0;
  int count = 1;
  long start = 0;
  long finish = 0;
  double elapsed = 0;
  while (!connected) {
    Serial.print("Atttempting to connect to gateway...(Attempt ");
    Serial.print(count++);
    Serial.println(")");
    start = millis();
    connected = modem.joinOTAA(appEui, appKey, modem.deviceEUI());//need to make my own join function because this is not working right. Takes too long
    //connected = modem.joinABP(devAddr, nwkSKey, appSKey);
    finish = millis();
    elapsed = (int)(((double)(finish - start))/1000.0);
    if(!connected)
    {
      Serial.print("Connection attempt timed out after ");
      Serial.print(elapsed - 1);
      Serial.println(" seconds.");
      modem.restart();
      modem.begin(US915);
      /*if(!(modem.power(PABOOST, 0))){
        Serial.println("Failed to change power settings");  
      }*/
    }
    else//connected==1 
    //****Seems to take exactly 13 seconds when it connects successfully. Kinda odd, going to see if I can change it to only wait for 15 seconds instead of 60****
    {
      Serial.print("Connected to gateway! Connected in ");
      Serial.print(elapsed + 15*(count-2));
      Serial.println(" seconds. Now routing data to application server...");
    }
  }


  
  // Set poll interval to 60 secs.
  modem.minPollInterval(60);
  // NOTE: independently by this setting the modem will
  // not allow to send more than one message every 2 minutes,
  // this is enforced by firmware and can not be changed.
}

void loop() 
{
  if(seconds % 10 == 0)
  {
    seconds++;  
    Serial.println();
    
    String msg = "Hello World!";
  
    Serial.println();
    Serial.print("Sending: " + msg + " - ");
    for (unsigned int i = 0; i < msg.length(); i++) {
      Serial.print(msg[i] >> 4, HEX);
      Serial.print(msg[i] & 0xF, HEX);
      Serial.print(" ");
    }
    Serial.println();
  
    int err;
    modem.beginPacket();
    modem.print(msg);
    err = modem.endPacket(true);
    if (err > 0) {
      Serial.println("Message sent correctly!");
    } else {
      Serial.println("Error sending message :(");
    }
    delay(1000);
    if (!modem.available()) {
      Serial.println("No downlink message received at this time.");
      return;
    }
    char rcv[64];
    int i = 0;
    while (modem.available()) {
      rcv[i++] = (char)modem.read();
    }
    Serial.print("Received: ");
    for (unsigned int j = 0; j < i; j++) {
      Serial.print(rcv[j] >> 4, HEX);
      Serial.print(rcv[j] & 0xF, HEX);
      Serial.print(" ");
    }
    Serial.println();
  }
  else//wait till a 10 second mark
  {
    seconds++;
    delay(1000);  
  }
}
