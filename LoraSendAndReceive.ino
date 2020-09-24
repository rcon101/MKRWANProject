/*
  Lora Send And Receive
  This sketch demonstrates how to send and receive data with the MKR WAN 1300 LoRa module.
  This example code is in the public domain.

  Edits by Ryan Conte, Wireless Biosensing Laboratory, UNH Undergraduate Research
*/

#include <MKRWAN.h>
#include <ArduinoLowPower.h>

LoRaModem modem;
int seconds = 0;

// Uncomment if using the Murata chip as a module
// LoRaModem modem(Serial1);

#include "arduino_secrets.h"
// Please enter your sensitive data in the Secret tab or arduino_secrets.h
//currently configured for prototyping with a single MKR1300 board. As it stands we have to get one of each of these from ttn for each unique device flash.
String appEui = "70B3D57ED0034ED8";
String appKey = "1C5093587252CD73F45B08EAE6599F92";
String devAddr = "2602242F";
String nwkSKey = "CD2B4A81C409F9B5A7F154CDAB700C3B";
String appSKey = "B06ED62B9D34C4E7C851CBEE13B6C30B";

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial);
  Serial.println("Starting modem...");
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
    //Serial.print("Atttempting to connect to gateway...(Attempt ");
    count++;
    Serial.print(count);
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
  //Serial.println("Enter a message to send to the application server: ");
  String msg = "Hello World";
  /*while(Serial.available())
  {
    char c = Serial.read();//get a single byte from the Serial Buffer
    msg += c;
  }//creates msg
  */
  /*Serial.println();
  Serial.print("Sending: " + msg + " - ");
  for (unsigned int i = 0; i < msg.length(); i++) {
    Serial.print(msg[i] >> 4, HEX);
    Serial.print(msg[i] & 0xF, HEX);
    Serial.print(" ");
  }
  Serial.println();
  */
  int err;
  Serial.println("Transmitting message");
  modem.beginPacket();
  modem.print(msg);
  err = modem.endPacket(true);
  if (err > 0) {
    Serial.println("Message sent correctly!");
  } else {
    Serial.println("Error sending message :(");
  }
  Serial.println("Deep Sleeping for 10 seconds...");
  //delay(200);//allow time for downlink thread to finish
  //modem.sleep();//sleeping the modem actually makes the module draw MORE POWER? Could be my application, but this was the only thing I added and +4mA was the result
  //LowPower.deepSleep(5000);
  delay(5000);
}
