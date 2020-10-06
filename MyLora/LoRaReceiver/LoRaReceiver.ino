#include <SPI.h>
#include <LoRa.h>

const char RECEIVER_ID = '0';//CHANGE THIS TO PROGRAM INDIVIDUAL RECEIVERS

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("LoRa Receiver");

  if (!LoRa.begin(915E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
}

void loop() {
  // try to parse packet
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    // received a packet
    Serial.print("Received packet '");

    //Now we want to authenticate the data --> assure it is being processed by the correct receiver
    // read packet
    String packet = "";
    //parse through the data packet and extract each byte one at a time.
    while (LoRa.available()) {
      char b = (char)LoRa.read();
      packet += b;
      //Serial.print(b);
    }
    //Serial.println();
    //Now we process the data, and assure it was meant for this receiver. If it was, print it. If not, do nothing.
    char validate = packet[0];//grab the first character in the packet.
    //Serial.println(validate);
    if(validate == RECEIVER_ID)
    {
      //print the data packet and the RSSI
      //Serial.println("Valid Data --> Correct destination reached");
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
