#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

BLEScan* pBLEScan;

#define BUFFER_SIZE 10  // increased from 5 to 10 for better accuracy

int bufferA[BUFFER_SIZE] = {0};
int bufferB[BUFFER_SIZE] = {0};
int indexA = 0, indexB = 0;

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
  }
};

// ── Sort helper for median ───────────────────────────────────────
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

// ── Median filter — removes spike outliers ───────────────────────
int getMedian(int* buffer, int size) {
  int temp[BUFFER_SIZE];
  int count = 0;

  // Copy only non-zero values
  for (int i = 0; i < size; i++) {
    if (buffer[i] != 0) {
      temp[count++] = buffer[i];
    }
  }

  if (count == 0) return 0;

  sortArray(temp, count);
  return temp[count / 2];  // middle value
}

// ── Weighted average — recent readings count more ────────────────
int getWeightedAverage(int* buffer, int size) {
  int totalWeight = 0, weightedSum = 0, count = 0;

  for (int i = 0; i < size; i++) {
    if (buffer[i] != 0) {
      int weight = i + 1;  // newer index = higher weight
      weightedSum += buffer[i] * weight;
      totalWeight += weight;
      count++;
    }
  }

  return (count > 0) ? weightedSum / totalWeight : 0;
}

// ── Kalman filter ────────────────────────────────────────────────
float kalmanA = -70.0, kalmanB = -70.0;
float kalmanGain = 0.25;  // lowered from 0.4 → smoother

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
  pBLEScan->setInterval(80);   // tightened for faster sampling
  pBLEScan->setWindow(79);
  Serial.println("Scanner ready...");
  Serial.println("Warming up... please wait 5 seconds");
  delay(5000);  // warm-up time to fill buffer before sending data
}

void loop() {
  pBLEScan->start(4, false);  // 4 seconds scan for more samples
  pBLEScan->clearResults();

  int medA = getMedian(bufferA, BUFFER_SIZE);
  int medB = getMedian(bufferB, BUFFER_SIZE);

  int wAvgA = getWeightedAverage(bufferA, BUFFER_SIZE);
  int wAvgB = getWeightedAverage(bufferB, BUFFER_SIZE);

  if (medA != 0 && medB != 0) {
    kalmanA = kalmanFilter(kalmanA, wAvgA);
    kalmanB = kalmanFilter(kalmanB, wAvgB);

    int finalA = (int)kalmanA;
    int finalB = (int)kalmanB;

    // Full debug output
    Serial.println("─────────────────────────────────────────");
    Serial.print("BeaconA  Raw: ");
    Serial.print(bufferA[(indexA - 1 + BUFFER_SIZE) % BUFFER_SIZE]);
    Serial.print("  Median: ");
    Serial.print(medA);
    Serial.print("  WAvg: ");
    Serial.print(wAvgA);
    Serial.print("  Final: ");
    Serial.println(finalA);

    Serial.print("BeaconB  Raw: ");
    Serial.print(bufferB[(indexB - 1 + BUFFER_SIZE) % BUFFER_SIZE]);
    Serial.print("  Median: ");
    Serial.print(medB);
    Serial.print("  WAvg: ");
    Serial.print(wAvgB);
    Serial.print("  Final: ");
    Serial.println(finalB);

    // CSV line for Python
    Serial.print("CSV:");
    Serial.print(finalA);
    Serial.print(",");
    Serial.println(finalB);

  } else {
    if (medA == 0) Serial.println("BeaconA not found");
    if (medB == 0) Serial.println("BeaconB not found");
  }

  delay(300);
}