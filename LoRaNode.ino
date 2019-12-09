#include <SPI.h>
#include <LoRa.h>
#include <MKRWAN.h>

int counter = 0;
LoRaModem modem;
String eui;

void setup() {
  //Serial.begin(9600);
  //while (!Serial);

  //Serial.println("LoRa Sender");

  //now we need to spit the EUI to the user so we can save it and input it into the hub code for security
  //uncomment if using program with new device that hasn't been registered to the hub yet
  modem.begin(US915);
  //Serial.print("Device EUI is: ");
  eui = modem.deviceEUI();
  //Serial.println(eui);

  if (!LoRa.begin(915E6)) {
    //Serial.println("Starting LoRa failed!");
    while (1);
  }
  
}

void loop() {
  Serial.print("Sending packet: ");
  Serial.println(counter);

  // send packet
  LoRa.beginPacket();
  LoRa.print(eui);
  LoRa.endPacket();

  counter++;

  delay(5000);
}
