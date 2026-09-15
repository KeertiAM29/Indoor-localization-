import serial
import serial.tools.list_ports
import threading
import time
import csv
import os
import random
import math

from sklearn.neighbors import KNeighborsClassifier

# ============================================================
# TRAINING DATA
# ============================================================

data_A = [
    -52,-51,-53,-50,-52,-54,-51,-53,-52,-50,
    -75,-76,-74,-77,-75,-73,-76,-74,-75,-76,
    -63,-64,-62,-65,-63,-61,-64,-62,-63,-64
]

data_B = [
    -76,-75,-77,-74,-76,-78,-75,-77,-76,-74,
    -51,-52,-50,-53,-51,-49,-52,-50,-51,-52,
    -62,-63,-61,-64,-62,-60,-63,-61,-62,-63
]

labels = (
    ["Room101"] * 10 +
    ["Room102"] * 10 +
    ["Corridor"] * 10
)

X = list(zip(data_A, data_B))
y = labels

# ============================================================
# KNN MODEL
# ============================================================

knn = KNeighborsClassifier(n_neighbors=3, metric="euclidean")
knn.fit(X, y)
print("✅ KNN Model Loaded")

# ============================================================
# CSV LOGGER
# ============================================================

LOG_FILE = "localization_log.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp","RSSI_A","RSSI_B","Prediction","Confidence"])

# ============================================================
# MAP POSITIONS
# ============================================================

MAP_POSITIONS = {
    "Room101":  {"left": "10%", "top": "28%"},
    "Room102":  {"left": "31%", "top": "28%"},
    "Corridor": {"left": "44%", "top": "50%"}
}

# ============================================================
# SHARED DATA
# ============================================================

latest_data = {
    "beaconA":        None,
    "beaconB":        None,
    "location":       "UNKNOWN",
    "confidence":     0,
    "connection":     "DISCONNECTED",
    "system_state":   "DISCONNECTED",
    "beaconA_status": "LOST",
    "beaconB_status": "LOST",
    "accuracy_label": "No Signal",
    "map_position":   {"left": "44%", "top": "50%"},
    "timestamp":      0,
    "error_message":  "Initialising...",
    "mode":           "DEMO"
}

data_lock = threading.Lock()

# ============================================================
# HELPERS
# ============================================================

ESP32_KEYWORDS = [
    "cp210","ch340","ch341","ch343","htw",
    "uart","usb serial","usb-serial","esp32",
    "silicon labs","wch"
]

def find_esp32_port():
    try:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            desc = (port.description or "").lower()
            mfr  = (port.manufacturer or "").lower()
            if any(kw in desc + " " + mfr for kw in ESP32_KEYWORDS):
                return port.device
        if len(ports) == 1:
            return ports[0].device
    except Exception:
        pass
    return None

def signal_status(rssi):
    if rssi is None or rssi <= -90: return "LOST"
    elif rssi <= -75: return "WEAK"
    elif rssi <= -65: return "MEDIUM"
    return "STRONG"

def log_data(rssi_a, rssi_b, prediction, confidence):
    try:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                rssi_a, rssi_b, prediction, confidence
            ])
    except Exception:
        pass

def set_disconnected(reason="No ESP32 detected"):
    with data_lock:
        latest_data.update({
            "beaconA": None, "beaconB": None,
            "location": "UNKNOWN", "confidence": 0,
            "connection": "DISCONNECTED", "system_state": "DISCONNECTED",
            "beaconA_status": "LOST", "beaconB_status": "LOST",
            "accuracy_label": "No Signal",
            "map_position": {"left": "44%", "top": "50%"},
            "timestamp": round(time.time() * 1000),
            "error_message": reason
        })

# ============================================================
# DEMO SIMULATION
# Smoothly cycles through rooms with realistic RSSI values
# ============================================================

DEMO_SCENARIOS = [
    # (room,      rssi_a_base, rssi_b_base, duration_seconds)
    ("Room101",   -52,         -76,         8),
    ("Corridor",  -63,         -62,         6),
    ("Room102",   -75,         -51,         8),
    ("Corridor",  -63,         -62,         5),
    ("Room101",   -52,         -76,         7),
    ("Room102",   -75,         -51,         9),
    ("Corridor",  -63,         -62,         6),
]

def demo_simulation():
    """Runs when no ESP32 is connected. Generates realistic moving data."""
    print("🎬 Demo simulation mode started")
    scenario_index = 0
    scenario_start = time.time()

    while True:
        # Check if real ESP32 appeared — stop demo if so
        if find_esp32_port():
            print("✅ Real ESP32 detected — stopping demo simulation")
            return

        scenario = DEMO_SCENARIOS[scenario_index]
        room, base_a, base_b, duration = scenario

        # Add realistic noise
        noise_a = math.sin(time.time() * 0.7) * 2 + random.uniform(-1.5, 1.5)
        noise_b = math.sin(time.time() * 0.5) * 2 + random.uniform(-1.5, 1.5)
        rssi_a  = int(base_a + noise_a)
        rssi_b  = int(base_b + noise_b)

        # KNN predict
        prediction    = knn.predict([[rssi_a, rssi_b]])[0]
        probabilities = knn.predict_proba([[rssi_a, rssi_b]])[0]
        confidence    = round(max(probabilities) * 100, 1)

        with data_lock:
            latest_data.update({
                "beaconA":        rssi_a,
                "beaconB":        rssi_b,
                "location":       prediction,
                "confidence":     confidence,
                "connection":     "ONLINE",
                "system_state":   "TRACKING",
                "beaconA_status": signal_status(rssi_a),
                "beaconB_status": signal_status(rssi_b),
                "accuracy_label": "High Accuracy" if confidence >= 85 else "Medium Accuracy",
                "map_position":   MAP_POSITIONS.get(prediction, MAP_POSITIONS["Corridor"]),
                "timestamp":      round(time.time() * 1000),
                "error_message":  "",
                "mode":           "DEMO"
            })

        # Advance scenario after duration
        if time.time() - scenario_start >= duration:
            scenario_index  = (scenario_index + 1) % len(DEMO_SCENARIOS)
            scenario_start  = time.time()

        time.sleep(1)

# ============================================================
# REAL ESP32 SERIAL READER
# ============================================================

BAUD_RATE   = 115200
RETRY_DELAY = 3

def serial_reader():
    demo_thread_started = False

    while True:
        port = find_esp32_port()

        if port is None:
            # No ESP32 — start demo if not already running
            if not demo_thread_started:
                set_disconnected("Demo Mode — No ESP32 connected")
                with data_lock:
                    latest_data["mode"] = "DEMO"
                t = threading.Thread(target=demo_simulation, daemon=True)
                t.start()
                demo_thread_started = True
                print("⏳ No ESP32 found — running in demo mode")
            time.sleep(RETRY_DELAY)
            continue

        # ESP32 found — stop demo by letting serial take over
        demo_thread_started = False

        try:
            print(f"🔌 Connecting to {port}...")
            ser = serial.Serial(port, BAUD_RATE, timeout=5)
            time.sleep(2)
            print(f"✅ ESP32 Connected on {port}")

            with data_lock:
                latest_data["connection"]    = "ONLINE"
                latest_data["system_state"]  = "WAITING"
                latest_data["error_message"] = ""
                latest_data["mode"]          = "LIVE"

            consecutive_empty = 0

            while True:
                try:
                    raw = ser.readline()
                except Exception:
                    raise

                line = raw.decode("utf-8", errors="ignore").strip()

                if not line:
                    consecutive_empty += 1
                    if consecutive_empty >= 10:
                        with data_lock:
                            latest_data["connection"]   = "IDLE"
                            latest_data["system_state"] = "IDLE"
                    continue
                else:
                    consecutive_empty = 0

                if not line.startswith("CSV:"):
                    continue

                try:
                    values = line.replace("CSV:", "").split(",")
                    rssi_a = int(values[0])
                    rssi_b = int(values[1])
                except Exception:
                    continue

                prediction    = knn.predict([[rssi_a, rssi_b]])[0]
                probabilities = knn.predict_proba([[rssi_a, rssi_b]])[0]
                confidence    = round(max(probabilities) * 100, 1)

                log_data(rssi_a, rssi_b, prediction, confidence)

                with data_lock:
                    latest_data.update({
                        "beaconA":        rssi_a,
                        "beaconB":        rssi_b,
                        "location":       prediction,
                        "confidence":     confidence,
                        "connection":     "ONLINE",
                        "system_state":   "TRACKING",
                        "beaconA_status": signal_status(rssi_a),
                        "beaconB_status": signal_status(rssi_b),
                        "accuracy_label": "High Accuracy" if confidence >= 85 else "Medium Accuracy",
                        "map_position":   MAP_POSITIONS.get(prediction, MAP_POSITIONS["Corridor"]),
                        "timestamp":      round(time.time() * 1000),
                        "error_message":  "",
                        "mode":           "LIVE"
                    })

        except serial.SerialException as e:
            set_disconnected(f"Serial error: {str(e)}")
            print(f"❌ Serial error: {e}")
        except Exception as e:
            set_disconnected(f"Error: {str(e)}")
            print(f"❌ Error: {e}")
        finally:
            try:
                ser.close()
            except Exception:
                pass

        print(f"🔄 Retrying in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)

# ============================================================
# START THREAD
# ============================================================

threading.Thread(target=serial_reader, daemon=True).start()
print("🚀 Serial reader thread started")
