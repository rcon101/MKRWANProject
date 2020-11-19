/**
 * @file LoRaP2P_RX.ino
 * @author rakwireless.com
 * @brief Receiver node for LoRa point to point communication
 * @version 0.1
 * @date 2020-08-21
 * 
 * @copyright Copyright (c) 2020
 * 
 * @note RAK5005-O GPIO mapping to RAK4631 GPIO ports
 * IO1 <-> P0.17 (Arduino GPIO number 17)
 * IO2 <-> P1.02 (Arduino GPIO number 34)
 * IO3 <-> P0.21 (Arduino GPIO number 21)
 * IO4 <-> P0.04 (Arduino GPIO number 4)
 * IO5 <-> P0.09 (Arduino GPIO number 9)
 * IO6 <-> P0.10 (Arduino GPIO number 10)
 * SW1 <-> P0.01 (Arduino GPIO number 1)
 */
#include <Arduino.h>
#include <SX126x-RAK4630.h>  //http://librarymanager/All#SX126x
#include <LoRaWan-RAK4630.h>
#include <SPI.h>

// Function declarations
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr);
void OnRxTimeout(void);
void OnRxError(void);

#ifdef NRF52_SERIES
#define LED_BUILTIN 35
#endif

// Define LoRa P2P parameters
#define RF_FREQUENCY 915000000	// Hz
#define TX_OUTPUT_POWER 22		// dBm
#define LORA_BANDWIDTH 0		// [0: 125 kHz, 1: 250 kHz, 2: 500 kHz, 3: Reserved]
#define LORA_SPREADING_FACTOR 7 // [SF7..SF12]
#define LORA_CODINGRATE 1		// [1: 4/5, 2: 4/6,  3: 4/7,  4: 4/8]
#define LORA_PREAMBLE_LENGTH 8	// Same for Tx and Rx
#define LORA_SYMBOL_TIMEOUT 0	// Symbols
#define LORA_FIX_LENGTH_PAYLOAD_ON false
#define LORA_IQ_INVERSION_ON false
#define RX_TIMEOUT_VALUE 3000
#define TX_TIMEOUT_VALUE 3000
#define APP_JOIN_SEND_INTERVAL 10000//[ms]

//define LoRaWAN Parameters
bool doOTAA = true;
#define SCHED_MAX_EVENT_DATA_SIZE APP_TIMER_SCHED_EVENT_DATA_SIZE /**< Maximum size of scheduler events. */
#define SCHED_QUEUE_SIZE 60                      /**< Maximum number of events in the scheduler queue. */
#define LORAWAN_DATERATE DR_0                   /*LoRaMac datarates definition, from DR_0 to DR_5*/
#define LORAWAN_TX_POWER TX_POWER_5                 /*LoRaMac tx power definition, from TX_POWER_0 to TX_POWER_15*/
#define JOINREQ_NBTRIALS 3                      /**< Number of trials for the join request. */
DeviceClass_t gCurrentClass = CLASS_A;                /* class definition*/
lmh_confirm gCurrentConfirm = LMH_CONFIRMED_MSG;          /* confirm/unconfirm packet definition*/
uint8_t gAppPort = LORAWAN_APP_PORT;                /* data port*/

static lmh_param_t lora_param_init = {LORAWAN_ADR_ON, LORAWAN_DATERATE, LORAWAN_PUBLIC_NETWORK, JOINREQ_NBTRIALS, LORAWAN_TX_POWER, LORAWAN_DUTYCYCLE_OFF};

// Foward declaration for LoRaWAN interrupt handlers
static void lorawan_has_joined_handler(void);
static void lorawan_rx_handler(lmh_app_data_t *app_data);
static void lorawan_confirm_class_handler(DeviceClass_t Class);
static void send_lora_frame(void);

/**@brief Structure containing LoRaWan callback functions, needed for lmh_init()
*/
static lmh_callback_t lora_callbacks = {BoardGetBatteryLevel, BoardGetUniqueId, BoardGetRandomSeed,
                    lorawan_rx_handler, lorawan_has_joined_handler, lorawan_confirm_class_handler};//

//OTAA keys
uint8_t nodeDeviceEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x30 };
uint8_t nodeAppEUI[8] = { 0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x03, 0x4E, 0xD8 };
uint8_t nodeAppKey[16] = { 0xE4, 0x80, 0xB2, 0xB7, 0xC4, 0x21, 0xB4, 0x1A, 0xED, 0x30, 0x1C, 0x64, 0x70, 0x2D, 0x7F, 0x95 };

// Private defination
#define LORAWAN_APP_DATA_BUFF_SIZE 64                     /**< buffer size of the data to be transmitted. */
#define LORAWAN_APP_INTERVAL 20000                        /**< Defines for user timer, the application data transmission interval. 20s, value in [ms]. */
static uint8_t m_lora_app_data_buffer[LORAWAN_APP_DATA_BUFF_SIZE];        //< Lora user application data buffer.
static lmh_app_data_t m_lora_app_data = {m_lora_app_data_buffer, 0, 0, 0, 0}; //< Lora user application data structure.


//Radio Event handler --> assign interrupt handlers to this in setup()
static RadioEvents_t RadioEvents;

//Buffers and other global vars
static uint8_t RcvBuffer[64];//buffer for single packet
String packets [256];//packet buffer that will dump to app server every APP_JOIN_SEND_INTERVAL ms
uint32_t bufferSize = 0;
int count_success = 0, count_fail = 0;

TimerEvent_t appTimer;

void setup()
{

	// Initialize LoRa chip.
	lora_rak4630_init();

	// Initialize Serial for debug output
	Serial.begin(115200);
	while (!Serial)
	{
		delay(10);
	}
  TimerInit(&appTimer, joinAndSend);
  TimerSetValue(&appTimer, APP_JOIN_SEND_INTERVAL);
  TimerStart(&appTimer);
	rxMode();//program starts in RX mode
}

void loop()
{
  //handles IRQ and then yields, pretty much handing over control to the Radio drivers at this point for the remainder of the program
	// Handle Radio events
	Radio.IrqProcess();
	// We are on FreeRTOS, give other tasks a chance to run
	delay(100);
	yield();
}

//connect radio to App Server, Send all buffered packets, and return to RX state
void joinAndSend(void)
{
  Serial.println("Attempting to join network...");
  // Setup the EUIs and Keys
  lmh_setDevEui(nodeDeviceEUI);
  lmh_setAppEui(nodeAppEUI);
  lmh_setAppKey(nodeAppKey);

  // Initialize LoRaWan
  int err_code = lmh_init(&lora_callbacks, lora_param_init, doOTAA);
  if (err_code != 0)
  {
    Serial.printf("lmh_init failed - %d\n", err_code);
  }
  
  // Start Join procedure
  lmh_join();
  while(lmh_join_status_get() != LMH_SET)//while not connected
  {
    Radio.IrqProcess();
    delay(100);
    yield();
  }
  //this is where we send each packet. For now we are just sending "Hello!" <bufferSize> times
  //we will need to provide an update to the send_lora_frame function to allow for passing of a String for the packet
  /*for(int i = 0; i < bufferSize; i++)
  {
    send_lora_frame();
    delay(100);
  }*/
  send_lora_frame();//demo single send for debugging
  delay(100);
  
  //the end of this function sets the timer back to the original interval and starts it from 0.
  TimerSetValue(&appTimer, APP_JOIN_SEND_INTERVAL);
  TimerStart(&appTimer);
  //return to rxMode
  rxMode();
}

//configures the radio to recieve continuously on the RX port.
void rxMode(void)
{
  Serial.println("=====================================");
  Serial.println("LoRaP2P Rx Test");
  Serial.println("=====================================");

  // Initialize the Radio callbacks
  RadioEvents.TxDone = NULL;
  RadioEvents.RxDone = OnRxDone;
  RadioEvents.TxTimeout = NULL;
  RadioEvents.RxTimeout = OnRxTimeout;
  RadioEvents.RxError = OnRxError;
  RadioEvents.CadDone = NULL;

  // Initialize the Radio
  Radio.Init(&RadioEvents);

  // Set Radio channel
  Radio.SetChannel(RF_FREQUENCY);

  // Set Radio RX configuration
  Radio.SetRxConfig(MODEM_LORA, LORA_BANDWIDTH, LORA_SPREADING_FACTOR,
            LORA_CODINGRATE, 0, LORA_PREAMBLE_LENGTH,
            LORA_SYMBOL_TIMEOUT, LORA_FIX_LENGTH_PAYLOAD_ON,
            0, true, 0, 0, LORA_IQ_INVERSION_ON, true);

  // Start LoRa
  Serial.println("Starting Radio.Rx");
  Radio.Rx(RX_TIMEOUT_VALUE);//continuously receive on RX port until we are interrupted after the timeout has been reached
}


void lorawan_has_joined_handler(void)
{
  Serial.println("OTAA Mode, Network Joined!");
}

void lorawan_rx_handler(lmh_app_data_t *app_data)
{
  Serial.printf("LoRa Packet received on port %d, size:%d, rssi:%d, snr:%d, data:%s\n",
          app_data->port, app_data->buffsize, app_data->rssi, app_data->snr, app_data->buffer);
}

void lorawan_confirm_class_handler(DeviceClass_t Class)
{
  Serial.printf("switch to class %c done\n", "ABC"[Class]);
  // Informs the server that switch has occurred ASAP
  m_lora_app_data.buffsize = 0;
  m_lora_app_data.port = gAppPort;
  lmh_send(&m_lora_app_data, gCurrentConfirm);
}

void send_lora_frame(void)
{
  if (lmh_join_status_get() != LMH_SET)
  {
    Serial.printf("Not joined, try again later");
    return;
  }

  uint32_t i = 0;
  memset(m_lora_app_data.buffer, 0, LORAWAN_APP_DATA_BUFF_SIZE);
  m_lora_app_data.port = gAppPort;
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffer[i++] = '0';
  m_lora_app_data.buffer[i++] = '|';
  m_lora_app_data.buffsize = i;

  lmh_error_status error = lmh_send(&m_lora_app_data, gCurrentConfirm);
  if (error == LMH_SUCCESS)
  {
    count_success++;
    Serial.printf("lmh_send ok count %d\n", count_success);
  }
  else
  {
    count_fail++;
    Serial.printf("lmh_send fail count %d\n", count_fail);
  }
}

/**@brief Function to be executed on Radio Rx Done event
 */
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr)
{
	Serial.println("OnRxDone");
	delay(10);
	memcpy(RcvBuffer, payload, size);
  String packet = "";

	Serial.printf("RssiValue=%d dBm, SnrValue=%d\n", rssi, snr);

	for (int idx = 0; idx < size; idx++)
	{
		Serial.printf("%02X ", RcvBuffer[idx]);
    packet += (char)RcvBuffer[idx];//concatenate each byte as a char to the packet String
	}
  packets[bufferSize++] = packet;//save the packetString to the packet Buffer
	Serial.println("");
	Radio.Rx(RX_TIMEOUT_VALUE);
}

/**@brief Function to be executed on Radio Rx Timeout event
 */
void OnRxTimeout(void)
{
	Serial.println("OnRxTimeout");
	Radio.Rx(RX_TIMEOUT_VALUE);
}

/**@brief Function to be executed on Radio Rx Error event
 */
void OnRxError(void)
{
	Serial.println("OnRxError");
	Radio.Rx(RX_TIMEOUT_VALUE);
}
