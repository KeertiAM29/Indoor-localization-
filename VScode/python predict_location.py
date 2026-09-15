import serial
import numpy as np
import time
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ── Training Data ────────────────────────────────────────────────

data_A = [
    # Room101 samples
    -52, -51, -53, -50, -52, -54, -51, -53, -52, -50,
    # Room102 samples
    -75, -76, -74, -77, -75, -73, -76, -74, -75, -76,
    # Corridor samples
    -63, -64, -62, -65, -63, -61, -64, -62, -63, -64,
]

data_B = [
    # Room101
    -76, -75, -77, -74, -76, -78, -75, -77, -76, -74,
    # Room102
    -51, -52, -50, -53, -51, -49, -52, -50, -51, -52,
    # Corridor
    -62, -63, -61, -64, -62, -60, -63, -61, -62, -63,
]

labels = ['Room101'] * 10 + ['Room102'] * 10 + ['Corridor'] * 10

X = list(zip(data_A, data_B))
y = labels

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

knn = KNeighborsClassifier(n_neighbors=3, metric='euclidean')
knn.fit(X_train, y_train)

acc = accuracy_score(y_test, knn.predict(X_test)) * 100
print(f"✅ Model trained | Accuracy: {acc:.1f}%")
print("─" * 50)

# ── Connect to ESP32 ─────────────────────────────────────────────

COM_PORT  = "COM3"    # ← your port
BAUD_RATE = 115200

print(f"🔌 Connecting to {COM_PORT}...")

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=3)
    time.sleep(2)
    print(f"✅ Connected! Waiting for data...\n")
    print("─" * 50)

    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        if not line.startswith("CSV:"):
            if line:
                print(f"  [ESP32] {line}")
            continue

        try:
            values = line.replace("CSV:", "").split(",")
            rssi_a = int(values[0])
            rssi_b = int(values[1])
        except:
            continue

        prediction = knn.predict([[rssi_a, rssi_b]])[0]
        proba = knn.predict_proba([[rssi_a, rssi_b]])[0]
        confidence = max(proba) * 100
        classes = knn.classes_

        print(f"\n  📡 BeaconA: {rssi_a} dBm  |  BeaconB: {rssi_b} dBm")
        print(f"  📍 Location   : {prediction}")
        print(f"  🎯 Confidence : {confidence:.1f}%")
        print(f"  📊 All scores : ", end="")
        for cls, prob in zip(classes, proba):
            print(f"{cls}: {prob*100:.0f}%  ", end="")
        print(f"\n{'─' * 50}")

except serial.SerialException as e:
    print(f"\n❌ Cannot connect to {COM_PORT}")
    print(f"   → Make sure ESP32 #3 is plugged in")
    print(f"   → Make sure Arduino Serial Monitor is CLOSED")
    print(f"   → Check the correct COM port")
    print(f"\n   Error: {e}")

except KeyboardInterrupt:
    print("\n\n🛑 Stopped by user.")
    if 'ser' in locals():
        ser.close()
    print("✅ Done.")