#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <ArduinoJson.h>

#define SERVICE_UUID        "12345678-1234-1234-1234-123456789012"
#define CHARACTERISTIC_UUID "87654321-4321-4321-4321-210987654321"

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;  // Track connection status
bool oldDeviceConnected = false;  // Track previous connection status

// Custom Server Callbacks to manage connection and disconnection events
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Device connected");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Device disconnected");
    // Restart advertising to allow the device to reconnect
    pServer->getAdvertising()->start();
    Serial.println("Restarting advertising...");
  }
};

void setup() {
  Serial.begin(115200);

  // Initialize BLE Device
  BLEDevice::init("ESP32_S3_Bluetooth");

  // Print the BLE device address
  String deviceAddress = BLEDevice::getAddress().toString().c_str();
  Serial.println("Device Address: " + deviceAddress);

  // Create BLE Server and set callbacks
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());  // Attach the server callbacks

  // Create BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_NOTIFY
  );

  // Start the service
  pService->start();

  // Configure and start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinInterval(100);
  pAdvertising->setMaxInterval(200);
  pAdvertising->start();

  Serial.println("BLE device is ready and advertising...");
  randomSeed(analogRead(0));  // Seed random number generator
}

void loop() {
  // Check if a device is connected
  if (deviceConnected) {
    // Create a JSON object
    StaticJsonDocument<128> doc;
    doc["value1"] = random(1, 11);  // Generate random value from 1 to 10
    doc["value2"] = random(1, 11);
    doc["value3"] = random(1, 11);
    doc["value4"] = random(1, 11);

    // Serialize JSON to a string
    String jsonString;
    serializeJson(doc, jsonString);

    // Ensure JSON size is within BLE limits
    if (jsonString.length() > 512) {
      Serial.println("Error: JSON string exceeds BLE characteristic limit.");
      return;
    }

    // Send the JSON string via BLE
    pCharacteristic->setValue(jsonString.c_str());
    pCharacteristic->notify();  // Notify connected device

    Serial.println("Data sent: " + jsonString);
    delay(1000);  // Transmit data every 1 second
  } else {
    // If the device was previously connected but now disconnected, log it
    if (oldDeviceConnected && !deviceConnected) {
      Serial.println("Device was connected but now disconnected.");
      oldDeviceConnected = deviceConnected;
    }
  }

  // Check if the device was previously disconnected and is now connected
  if (!oldDeviceConnected && deviceConnected) {
    Serial.println("Device was disconnected but now reconnected.");
    oldDeviceConnected = deviceConnected;
  }
}
