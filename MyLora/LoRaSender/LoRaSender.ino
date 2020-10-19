#include <SPI.h>
#include <LoRa.h>
#include "MD5.h"

int counter = 0;

void setup() {
  Serial.begin(115200);
  //while(!Serial);

  Serial.println("LoRa Sender");

  if (!LoRa.begin(915E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
}

void loop() {
  Serial.print("Sending packet: ");
  Serial.println(counter);

  // send packet
  LoRa.beginPacket();
  unsigned char* hash = MD5::make_hash("1230");
  char* md5str = MD5::make_digest(hash, 16);
  //LoRa.print(counter%2);//give us either 0 or 1
  String m = md5str;
  m += " hello ";
  m += counter;
  m += " from device 4";
  LoRa.print(m);
  LoRa.endPacket();

  counter++;
  free(md5str);
  free(hash);
  delay(5000);
}
