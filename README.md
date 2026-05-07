# Smart Traffic Light System

> An AI-powered, real-time traffic management system that sees, hears, and thinks — so your city can breathe.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python)
![Arduino](https://img.shields.io/badge/Arduino-Compatible-teal?logo=arduino)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green?logo=opencv)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple)
![Three.js](https://img.shields.io/badge/Three.js-WebGL-black?logo=three.js)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What Is This?

Traditional traffic lights operate on fixed timers — they don't know if 30 cars are waiting or zero. This system changes that.

**Smart Traffic Light System** is a full-stack, IoT-enabled traffic controller that uses computer vision, audio signal processing, and real-time hardware control to make intersections intelligent. It watches live camera feeds to count vehicles, listens for emergency sirens, dynamically adjusts green light durations based on actual traffic density, and instantly clears the way for emergency vehicles — all in real time.

It bridges the physical and digital worlds: Python handles the AI on a computer, an Arduino controls the physical LEDs and sensors, and a browser-based 3D dashboard gives you a live view of the entire intersection.

---

## Features

| Capability | Details |
|---|---|
| **Vehicle Detection** | YOLOv8 nano model with MOG2 motion detection as fallback |
| **Emergency Detection** | FFT-based audio analysis detects ambulance, fire truck, and police sirens |
| **Dynamic Timing** | Green light duration scales from 10s to 30s based on vehicle count |
| **4-Way Intersection** | Manages North, East, South, and West simultaneously |
| **Arduino Control** | Serial communication drives real LED traffic lights and a servo gate |
| **Camera Flexibility** | USB webcams or IP cameras via the Android IP Webcam app |
| **Web Dashboard (2D)** | Interactive HTML/JS visualization with manual controls |
| **Web Dashboard (3D)** | Immersive Three.js scene with animated vehicles, lighting, and night mode |
| **WebSocket Updates** | Real-time data push to all connected browser clients |
| **Graceful Fallback** | Runs without a camera (virtual), without audio, or without Arduino |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT LAYER                             │
│                                                             │
│   USB/IP Cameras ──► Vehicle Detection (YOLO / MOG2)       │
│   Microphone     ──► Siren Analysis (FFT + Peak Detection)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              PYTHON CONTROLLER (main_traffic_controller.py) │
│                                                             │
│   • Threading: Camera, Sound, Arduino, WebSocket threads    │
│   • Queue-based inter-thread communication                  │
│   • 8-state traffic light finite state machine             │
│   • Emergency override logic                               │
└────────────────┬──────────────────────────┬─────────────────┘
                 │                          │
                 ▼                          ▼
┌───────────────────────┐    ┌─────────────────────────────────┐
│  Arduino (Serial USB) │    │  WebSocket Server (:8765)       │
│                       │    │                                 │
│  • 12 LED outputs     │    │  • Broadcasts JSON state        │
│  • 4 vehicle sensors  │    │  • Feeds both web dashboards    │
│  • Sound sensor       │    │                                 │
│  • Servo (emergency   │    └──────────────┬──────────────────┘
│    lane gate)         │                   │
└───────────┬───────────┘                   ▼
            │                  ┌────────────────────────────┐
            ▼                  │  Browser Clients           │
    Physical Traffic           │  index.html  (2D)          │
    Lights + Gate              │  index2.html (3D Three.js) │
                               └────────────────────────────┘
```

---

## How It Works

### 1. Traffic Timing Algorithm
Every camera frame (at 2 FPS) updates the vehicle count for each direction. The Python controller maps the highest count across all directions to a green phase duration:

```
0 vehicles  →  10 seconds green
10 vehicles →  30 seconds green
```

After each phase transition, the count decays by 3 (simulating vehicles clearing the intersection). The direction with the highest density gets priority on the next cycle.

### 2. Emergency Vehicle Detection
The audio analyzer runs a continuous FFT on the microphone input, scanning for frequency signatures of emergency sirens:

- **Ambulance**: 400–1200 Hz
- **Fire Truck**: 300–800 Hz  
- **Police**: 500–1500 Hz

On detection, the system immediately triggers `EMERGENCY_MODE`: all lights go red, the priority direction turns green, and the Arduino actuates the servo to open a physical emergency lane gate. The override times out after 30 seconds.

### 3. State Machine (8 States)
```
NORTH_GO → NORTH_YELLOW → EAST_GO → EAST_YELLOW →
SOUTH_GO → SOUTH_YELLOW → WEST_GO → WEST_YELLOW → (repeat)
                 ↕
          EMERGENCY_MODE (any time)
```

---

## Project Structure

```
Smart-Traffic-Light-Sysytem/
│
├── main_traffic_controller.py   # Central orchestration — start here
├── vehicle_detection.py         # YOLO + MOG2 detection, camera management
├── camera_setup.py              # IP and USB camera configuration
├── sound_analyzer.py            # Emergency siren frequency detection
├── requirements.txt             # Python dependencies
│
├── smart_traffic_arduino/
│   └── smart_traffic_arduino.ino   # Full Arduino firmware (12 LEDs + servo)
│
├── smrttraffic/
│   └── smrttraffic.ino             # Simplified version with LCD display
│
├── index.html                   # 2D browser dashboard
├── index2.html                  # 3D Three.js dashboard
└── yolov8n.pt                   # YOLOv8 nano model weights (~42 MB)
```

---

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Arduino Uno or Mega
- A USB webcam, or an Android phone with the [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) app
- A microphone (optional — for siren detection)

### Hardware Wiring (Arduino)

| Direction | Red | Yellow | Green |
|-----------|-----|--------|-------|
| North     | 2   | 3      | 4     |
| East      | 5   | 6      | 7     |
| South     | 8   | 9      | 10    |
| West      | 11  | 12     | 13    |

- Vehicle sensors: `A0` (North), `A1` (East), `A2` (South), `A3` (West)
- Sound sensor: `A4`
- Servo (emergency gate): `A5`

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Smart-Traffic-Light-System.git
cd Smart-Traffic-Light-System

# Install Python dependencies
pip install -r requirements.txt
```

### Arduino Setup

1. Open `smart_traffic_arduino/smart_traffic_arduino.ino` in the Arduino IDE
2. Select your board (Tools → Board → Arduino Uno/Mega)
3. Upload the sketch to your Arduino

### Configuration

Open `main_traffic_controller.py` and update the serial port to match your system:

```python
# Windows
arduino_port = 'COM3'

# macOS / Linux
arduino_port = '/dev/ttyUSB0'
```

For IP cameras, open `camera_setup.py` and set your phone's IP address:

```python
camera.add_ip_camera(ip='192.168.1.100', port=8080)
```

### Run

```bash
python main_traffic_controller.py
```

Then open `index2.html` in your browser for the full 3D dashboard, or `index.html` for the 2D view.

---

## Web Dashboards

### 2D Dashboard (`index.html`)
A clean, interactive intersection view with:
- Live traffic light state for all 4 directions
- Vehicle count controls (+/- buttons)
- Emergency mode toggle
- Real-time green phase timer display

### 3D Dashboard (`index2.html`)
A Three.js-powered immersive scene featuring:
- Full 3D junction with roads, crosswalks, buildings, and trees
- Animated vehicles (cars, buses, trucks) with headlights
- Realistic traffic light poles with glow effects
- Dynamic shadows and street lighting
- Night mode toggle
- Emergency vehicle simulation with flashing lights
- Live AI status, FPS counter, and detection rate display

---

## Tech Stack

| Layer | Technology |
|---|---|
| Computer Vision | OpenCV, YOLOv8 (Ultralytics), PyTorch |
| Audio Processing | PyAudio, NumPy FFT, SciPy Signal |
| Hardware Interface | PySerial (Arduino), Arduino C++ |
| Real-time Comms | WebSockets (`websockets` library) |
| Frontend | HTML5, CSS3, JavaScript, Three.js |
| Camera Input | OpenCV VideoCapture, HTTP (IP Webcam) |

---

## Running Without Hardware

The system degrades gracefully if hardware is not available:

- **No Arduino**: The Python controller runs the state machine in software only, and the web dashboards still update.
- **No Camera**: A `VirtualCamera` generates synthetic frames with random moving rectangles for testing.
- **No Microphone**: Audio analysis thread is skipped; emergency mode can still be triggered manually from the dashboard.

---

## Roadmap

- [ ] Multi-intersection coordination across a city grid
- [ ] License plate recognition for authorized vehicle fast-pass
- [ ] Cloud dashboard with historical traffic analytics
- [ ] Pedestrian detection and crosswalk timing
- [ ] MQTT support for large-scale IoT deployment
- [ ] Docker container for zero-configuration Python setup

---

## Contributing

Contributions are welcome. If you have ideas for better detection algorithms, hardware integrations, or dashboard improvements, open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch and open a Pull Request

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for the vehicle detection model
- [Three.js](https://threejs.org/) for the 3D visualization engine
- [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) Android app for wireless camera streaming
- The open-source computer vision and IoT communities whose tools made this possible

---

*Built to make intersections smarter, cities more livable, and emergency response faster.*
