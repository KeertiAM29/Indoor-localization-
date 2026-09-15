#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

BLEScan* pBLEScan;

#define BUFFER_SIZE 10

int bufferA[BUFFER_SIZE] = {0};
int bufferB[BUFFER_SIZE] = {0};
int bufferC[BUFFER_SIZE] = {0};
int indexA = 0, indexB = 0, indexC = 0;

class MyCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    String name = advertisedDevice.getName().c_str();
    int rssi = advertisedDevice.getRSSI();

    if (name == "BeaconA") {
      bufferA[indexA % BUFFER_SIZE] = rssi;
      indexA++;
    }
    if (name == "BeaconB") {
      bufferB[indexB % BUFFER_SIZE] = rssi;
      indexB++;
    }
    if (name == "BeaconC") {
      bufferC[indexC % BUFFER_SIZE] = rssi;
      indexC++;
    }
  }
};

void sortArray(int* arr, int size) {
  for (int i = 0; i < size - 1; i++) {
    for (int j = 0; j < size - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        int temp = arr[j];
        arr[j] = arr[j + 1];
        arr[j + 1] = temp;
      }
    }
  }
}

int getMedian(int* buffer, int size) {
  int temp[BUFFER_SIZE];
  int count = 0;
  for (int i = 0; i < size; i++) {
    if (buffer[i] != 0) temp[count++] = buffer[i];
  }
  if (count == 0) return 0;
  sortArray(temp, count);
  return temp[count / 2];
}

int getWeightedAverage(int* buffer, int size) {
  int totalWeight = 0, weightedSum = 0, count = 0;
  for (int i = 0; i < size; i++) {
    if (buffer[i] != 0) {
      int weight = i + 1;
      weightedSum += buffer[i] * weight;
      totalWeight += weight;
      count++;
    }
  }
  return (count > 0) ? weightedSum / totalWeight : 0;
}

float kalmanA = -70.0, kalmanB = -70.0, kalmanC = -70.0;
float kalmanGain = 0.25;

float kalmanFilter(float previous, float newReading) {
  return previous + kalmanGain * (newReading - previous);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyCallbacks(), true);
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(80);
  pBLEScan->setWindow(79);
  Serial.println("Scanner ready...");
  Serial.println("Warming up... please wait 5 seconds");
  delay(5000);
}

void loop() {
  pBLEScan->start(4, false);
  pBLEScan->clearResults();

  int medA = getMedian(bufferA, BUFFER_SIZE);
  int medB = getMedian(bufferB, BUFFER_SIZE);
  int medC = getMedian(bufferC, BUFFER_SIZE);

  int wAvgA = getWeightedAverage(bufferA, BUFFER_SIZE);
  int wAvgB = getWeightedAverage(bufferB, BUFFER_SIZE);
  int wAvgC = getWeightedAverage(bufferC, BUFFER_SIZE);

  if (medA != 0 && medB != 0 && medC != 0) {
    kalmanA = kalmanFilter(kalmanA, wAvgA);
    kalmanB = kalmanFilter(kalmanB, wAvgB);
    kalmanC = kalmanFilter(kalmanC, wAvgC);

    int finalA = (int)kalmanA;
    int finalB = (int)kalmanB;
    int finalC = (int)kalmanC;

    Serial.println("─────────────────────────────────────────");
    Serial.print("BeaconA  Raw: ");
    Serial.print(bufferA[(indexA - 1 + BUFFER_SIZE) % BUFFER_SIZE]);
    Serial.print("  Median: "); Serial.print(medA);
    Serial.print("  Final: "); Serial.println(finalA);

    Serial.print("BeaconB  Raw: ");
    Serial.print(bufferB[(indexB - 1 + BUFFER_SIZE) % BUFFER_SIZE]);
    Serial.print("  Median: "); Serial.print(medB);
    Serial.print("  Final: "); Serial.println(finalB);

    Serial.print("BeaconC  Raw: ");
    Serial.print(bufferC[(indexC - 1 + BUFFER_SIZE) % BUFFER_SIZE]);
    Serial.print("  Median: "); Serial.print(medC);
    Serial.print("  Final: "); Serial.println(finalC);

    // CSV for Python
    Serial.print("CSV:");
    Serial.print(finalA);
    Serial.print(",");
    Serial.print(finalB);
    Serial.print(",");
    Serial.println(finalC);

  } else {
    if (medA == 0) Serial.println("BeaconA not found");
    if (medB == 0) Serial.println("BeaconB not found");
    if (medC == 0) Serial.println("BeaconC not found");
  }

  delay(300);
}