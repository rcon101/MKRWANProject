#include <SPI.h>
#include <LoRa.h>
#include "MD5.h"

int counter = 0;

void setup() {
  Serial.begin(9600);
  //while (!Serial);

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
  LoRa.print(md5str);
  LoRa.print(": hello ");
  LoRa.print(counter);
  LoRa.endPacket();

  counter++;
  free(md5str);
  free(hash);
  delay(5000);
}
