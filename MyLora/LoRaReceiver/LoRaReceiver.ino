#include <SPI.h>
#include <LoRa.h>
#include "MD5.h"

const char RECEIVER_ID = '0';//CHANGE THIS TO PROGRAM INDIVIDUAL RECEIVERS
char *PASSWORD = "1230";//for now our passcode is "123<(int)ID>"
String md5str = "";

void setup() {
  Serial.begin(9600);
  while (!Serial);
  delay(1000);//give the system a second to boot
  Serial.println("LoRa Receiver");
  if (!LoRa.begin(915E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }

 //now we want to generate our MD5 hash for this passcode
 unsigned char* hash = MD5::make_hash(PASSWORD);
 md5str = MD5::make_digest(hash, 16);//we compare this to the packet header
 free(hash); 
}

void loop() {
  // try to parse packet
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    // received a packet
    //Now we want to authenticate the data --> assure it is being processed by the correct receiver
    // read packet
    String packet = "";
    int count = 0;
    String validate = "";
    //parse through the data packet and extract each byte one at a time.
    while (LoRa.available()) {
      char b = (char)LoRa.read();
      if(count < 15)
      {
        validate += b;
        count++;
      }
      else
      {
        packet += b;  
      }
      //Serial.print(b);
    }
    //Serial.println();
    //Now we process the data, and assure it was meant for this receiver. If it was, print it. If not, do nothing.
    //Serial.println(validate);
    if(validate == md5str)
    {
      //print the data packet and the RSSI
      //Serial.println("Valid Data --> Correct destination reached");
      Serial.print("Received packet '");
      Serial.print(packet);
      Serial.print("' with RSSI ");
      Serial.println(LoRa.packetRssi()); 
    }
    else
    {
      //Serial.println("Invalid Data --> Confirm Reciever ID");  
    }
  }
}
