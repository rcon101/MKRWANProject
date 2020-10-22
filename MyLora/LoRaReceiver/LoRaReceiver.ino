/**
 * Ryan Conte   -->   as of 10/15: 
 * 
 * Takes too long to connect on OTAA, maybe due to distance/antenna, also may be due to some timeout issues in the hardware
 * Once connected, does not always send correctly. It is seen by the gateway, but cannot get an ack from the application server.
 * I think this could be fixed by using our own application server instead of TTN.
 * 
 * As of now the only way to relay messages across the link layer is to listen on LoRa for packets, then connect to the gateway every so often and send
 * all of the saved data. Issue with this is missed data while transmitting to gateway, as well as too much power consumed trying to connect to the gateway
 * for a long time.
 * 
 * For MONDAY 10/19:
 * 5 nodes transmitting to 1 link layer node that transmits the data to the gateway
 * also program the ttn packet receiver to separate the data nicely --> this means we also need to come up with a format structure for each packet.
 * 
 * ^^DONE with 5 nodes part of this.
 * Connection is fine, but often cannot get an ack from the server when sending packets through the gateway. This results in lots of uncollected data while
 * the module is waiting for acks from the server. I think this could be solved by creating a two radio module for the link-layer. To my knowledge, it is not possible
 * to have the device both actively sending data to the gateway, and also receiving packets on the LoRa frequency bands from other nodes. To fix this, we could have
 * one radio connect at the start of the program, and then feed it data from the other radio through a hardware connection. This way we miss no data, and we do not have
 * to fully allocate our system to one major task at a time.
 * 
 * we have com up with an arbitrary data packet format, and are going to try and program the packet decoder to separate it that way.
 * 
 */




#include <SPI.h>
#include <LoRa.h>
#include <MKRWAN.h>
#include "MD5.h"

LoRaModem modem;

const char RECEIVER_ID = '0';//CHANGE THIS TO PROGRAM INDIVIDUAL RECEIVERS
char *PASSWORD = "1230";//for now our passcode is "123<(int)ID>"
String md5str = "";
int runtime = 0;
int startTime = 0;
String appEui = "70B3D57ED0034ED8";
String appKey = "413546B24A20423357D915EB1872DFD2";
String devAddr = "2602254A";
String nwkSKey = "3C25D4F27AD0270A46A45C1198B69673";
String appSKey = "75D18106131972B9A43B804F15B506EE";
const int BUFFER_SIZE = 256;
String *packetBuffer = new String[BUFFER_SIZE];
int bufferLen = 0;


void setup() {
  Serial.begin(115200);
  while (!Serial);
  startTime = millis();
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
 runtime += millis() - startTime; 
}

void loop() {
  startTime = millis();
  int connectingTime = 0;
  // try to parse packet
  int packetSize = LoRa.parsePacket();

  //packet processing:
  if (packetSize) {
    // received a packet
    //Serial.println("Received Packet");
    //Now we want to authenticate the data --> assure it is being processed by the correct receiver
    // read packet
    String packet = "";
    int count = 0;
    String validate = "";
    //parse through the data packet and extract each byte one at a time.
    while (LoRa.available()) {
      char b = (char)LoRa.read();
      if(count < 32)
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
      packetBuffer[bufferLen] = packet;
      bufferLen++;
    }
    else
    {
      Serial.println("Unauthorized Data Seen and Ignored"); 
    }
  }
  //we are going to connect to the gateway and send it all of our stored data.
  if( (runtime/1000)%20 == 0 && (bufferLen > 0))//every 30 seconds of runtime if there is any data packets in the buffer
  {
      connectingTime = millis();
      //connect to gateway through OTAA:
      Serial.println("gateway connect...");
      if(!modem.begin(US915))
      {
        Serial.println("Failed to start modem");
        while(1) {}
      }
      Serial.print("Device EUI: ");
      Serial.println(modem.deviceEUI());
      int connected = 0;
      while(!connected) 
      {
        Serial.println("Connecting...");
        connected = modem.joinOTAA(appEui, appKey, modem.deviceEUI());
        //connected = modem.joinABP(devAddr, nwkSKey, appSKey);
        if(!connected)
        {
          modem.restart();
          modem.begin(US915);
        }
        else//connected --> so we want to send it all our data then call LoRa.begin again to listen for more packets from our child nodes.
        {
          Serial.println("Connected to gateway!");
          Serial.print("Uploading contents of message buffer to the cloud: ");
          Serial.print(bufferLen);
          Serial.println(" messages to upload.");
            
          //print the contents of the buffer before uplink
          Serial.println("Contents of Buffer: ");
          for(int i = 0; i < bufferLen; i++)
          {
            String m = packetBuffer[i];
            Serial.print(i);
            Serial.print(": ");
            Serial.println(m);
          }

          for(int i = 0; i < bufferLen; i++)
          {
            int ack = 0;
            while(!ack){//send the packet until it is sent correctly
              String m = packetBuffer[i];
              Serial.print("Starting Packet...");
              modem.beginPacket();
              modem.print(m);
              Serial.print("waiting for ack from server...");
              int err = modem.endPacket(true);
              if( err > 0 )
              {
                Serial.println("Message Sent Correctly!");
                ack = 1;
                delay(100);//allow time for buffers to empty/fill
              }
              else
              {
                Serial.println("Error Sending Message :(");
                delay(5000);//allow time for downlink to be transmitted
              }
            }
          }
          Serial.print("Transmissions Complete...");
          Serial.println("Returning to Reciever State");
          LoRa.begin(915E6);//return to radio state
          bufferLen = 0;//assure we wait to get more packets before reconnecting to gateway for transmission.
          connectingTime = millis() - connectingTime;
        }
      } 
  }
  runtime += millis() - startTime - connectingTime;//don't account for time spent connected to gateway.
}
