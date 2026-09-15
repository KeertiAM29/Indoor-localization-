#include <BLEDevice.h>
#include <BLEAdvertising.h>

void setup() {
  Serial.begin(115200);
  BLEDevice::init("BeaconB");

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x06);
  BLEDevice::startAdvertising();

  Serial.println("Beacon B is broadcasting...");
}

void loop() {
  delay(1000);
}
