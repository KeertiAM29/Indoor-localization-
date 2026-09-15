# 🏠 IndoorLoc — Real-Time Indoor Localization System

> **Live Demo →** [https://indoorloc.onrender.com/](https://indoorloc.onrender.com/)  
> *(Replace this link after deploying to Render)*

---

## 📌 Overview

IndoorLoc is a real-time indoor localization system built using **ESP32**, **BLE Beacons**, and a **KNN Machine Learning model**. It tracks a person's location inside a building by analyzing RSSI (signal strength) values from two BLE beacons and predicts which room they are in — displayed on a live web dashboard.

---

## 🎯 Features

- 📡 **Real-time RSSI data** from 2 BLE beacons via ESP32
- 🤖 **KNN Classifier** for room prediction with confidence scoring
- 🗺️ **Live floor plan map** with animated location marker
- 📊 **Sparkline charts** showing signal history
- 🔄 **Auto-reconnect** — dashboard updates the moment ESP32 connects
- 🎬 **Demo mode** — runs with simulated data when no hardware connected
- 📱 Responsive dark-mode dashboard

---

## 🏗️ System Architecture

```
BLE Beacon A ──┐
               ├──► ESP32 (scans RSSI) ──► Serial/USB ──► Python Flask Server ──► Web Dashboard
BLE Beacon B ──┘                                           (KNN Prediction)        (Live UI)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Microcontroller | ESP32 DevKit V1 |
| Communication | BLE (Bluetooth Low Energy) |
| ML Model | K-Nearest Neighbors (scikit-learn) |
| Backend | Python, Flask |
| Frontend | HTML, CSS, Vanilla JS |
| Deployment | Render.com |

---

## 📁 Project Structure

```
├── dashboard/        # Flask app, ML model, Web UI
├── hardware/         # ESP32 beacon & scanner sketches
├── VScode/           # Prediction scripts
└── README.md

---

## 🚀 Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python app.py

# Open browser
http://localhost:5000
```

> Connect ESP32 via USB — the dashboard switches from Demo to Live mode automatically.

---

## 📡 ESP32 Serial Format

The ESP32 sketch should send data in this format:
```
CSV:-65,-72
CSV:-52,-76
```
Where values are RSSI readings from Beacon A and Beacon B.

---

## 🎓 ML Model Details

- **Algorithm:** K-Nearest Neighbors (k=3, Euclidean distance)
- **Features:** [RSSI_BeaconA, RSSI_BeaconB]
- **Classes:** Room101, Room102, Corridor
- **Training samples:** 30 (10 per class)

---

## 👩‍💻 Author

**Keerti Mahantshetti**  
5th Semester Project — Indoor Localization using BLE & Machine Learning
