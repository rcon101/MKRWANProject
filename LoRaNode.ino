//#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <MKRWAN.h>

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 32 // OLED display height, in pixels

// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
#define OLED_RESET     -1 
int counter = 0;
LoRaModem modem;
String eui;
//Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
void setup() {
    Serial.begin(9600);
    //while (!Serial);
    Wire.begin(SDA,SCL);
    Serial.println("LoRa Sender");
    pinMode(RFM_TCXO,OUTPUT);
    pinMode(RFM_SWITCH,OUTPUT);
    pinMode(LED_BUILTIN,OUTPUT);
    LoRa.setPins(SS,RFM_RST,RFM_DIO0);
    if (!LoRa.begin(915E6)) {
        Serial.println("Starting LoRa failed!");
    while (1);
    }
    
 // modem.begin(US915);
 // Serial.print("Device EUI is: ");
  //eui = modem.deviceEUI();
  //Serial.println(eui);


  
}

void loop() {


  Serial.print("Sending packet: ");
  Serial.println(counter);

  // send packet
  LoRa.beginPacket();
  LoRa.print(eui);
  LoRa.endPacket();

  counter++;

  delay(1000);
}
