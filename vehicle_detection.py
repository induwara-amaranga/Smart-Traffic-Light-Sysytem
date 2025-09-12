# vehicle_detector.py
import cv2
import numpy as np
from collections import deque

class VehicleDetector:
    def __init__(self):
        # Initialize YOLO or simple detector
        self.use_yolo = False
        
        try:
            # Try to load YOLO (optional)
            self.net = cv2.dnn.readNet('yolov4.weights', 'yolov4.cfg')
            self.classes = open('coco.names').read().strip().split('\n')
            self.vehicle_classes = ['car', 'truck', 'bus', 'motorbike', 'bicycle']
            self.use_yolo = True
        except:
            print("YOLO not found, using simple motion detection")
        
        # Simple detector fallback
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        self.vehicle_tracker = {}
        self.next_id = 0
        
    def detect_vehicles(self, frame):
        """Detect vehicles in frame"""
        if self.use_yolo:
            return self._detect_yolo(frame)
        else:
            return self._detect_simple(frame)
    
    def _detect_yolo(self, frame):
        """YOLO-based detection"""
        height, width = frame.shape[:2]
        
        # Create blob
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        # Get detections
        outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())
        
        # Process detections
        vehicles = []
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5 and self.classes[class_id] in self.vehicle_classes:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    vehicles.append({
                        'x': center_x - w//2,
                        'y': center_y - h//2,
                        'w': w,
                        'h': h,
                        'class': self.classes[class_id]
                    })
        
        return len(vehicles)
    
    def _detect_simple(self, frame):
        """Simple motion-based detection"""
        # Preprocess
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Background subtraction
        fg_mask = self.bg_subtractor.apply(blur)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and count vehicles
        vehicle_count = 0
        min_area = 500  # Minimum area to consider as vehicle
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                
                # Basic vehicle shape filter
                if 0.5 < aspect_ratio < 4.0:
                    vehicle_count += 1
        
        return min(vehicle_count, 10)  # Cap at 10 vehicles

# camera_manager.py
import cv2
import numpy as np

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.virtual_mode = True  # Use virtual cameras for demo
        
    def get_cameras(self):
        """Initialize cameras for each direction"""
        if self.virtual_mode:
            # Create virtual cameras (colored frames for demo)
            self.cameras = {
                'north': VirtualCamera('North', (255, 0, 0)),
                'east': VirtualCamera('East', (0, 255, 0)),
                'south': VirtualCamera('South', (0, 0, 255)),
                'west': VirtualCamera('West', (255, 255, 0))
            }
        else:
            # Real camera indices (update based on your setup)
            camera_indices = {'north': 0, 'east': 1, 'south': 2, 'west': 3}
            for direction, idx in camera_indices.items():
                try:
                    cap = cv2.VideoCapture(idx)
                    if cap.isOpened():
                        self.cameras[direction] = cap
                except:
                    print(f"Camera {direction} not available")
        
        return self.cameras
    
    def cleanup(self):
        """Release all cameras"""
        for camera in self.cameras.values():
            if hasattr(camera, 'release'):
                camera.release()

class VirtualCamera:
    """Virtual camera for testing without real cameras"""
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.frame_count = 0
        
    def read(self):
        """Generate synthetic frames with moving vehicles"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = self.color
        
        # Add random vehicles
        vehicle_count = np.random.randint(0, 5)
        for i in range(vehicle_count):
            x = np.random.randint(50, 590)
            y = np.random.randint(50, 430)
            cv2.rectangle(frame, (x, y), (x+50, y+30), (255, 255, 255), -1)
        
        # Add text
        cv2.putText(frame, f"{self.name} Camera", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        self.frame_count += 1
        return frame

# sound_processor.py
import numpy as np
import pyaudio
import struct

class SoundProcessor:
    def __init__(self, sample_rate=44100, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.emergency_frequencies = [700, 800, 900, 1000]  # Common siren frequencies
        self.threshold = 0.3
        
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        except:
            print("Audio input not available, using simulation")
            self.stream = None
    
    def detect_emergency_siren(self):
        """Detect emergency siren in audio stream"""
        if self.stream is None:
            # Simulate random emergency detection
            return np.random.random() < 0.01  # 1% chance
        
        try:
            # Read audio data
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_data = struct.unpack(f'{self.chunk_size}h', data)
            audio_array = np.array(audio_data) / 32768.0
            
            # FFT analysis
            fft = np.fft.fft(audio_array)
            frequencies = np.fft.fftfreq(self.chunk_size, 1/self.sample_rate)
            magnitudes = np.abs(fft)
            
            # Check for emergency frequencies
            for freq in self.emergency_frequencies:
                freq_idx = np.argmin(np.abs(frequencies - freq))
                if magnitudes[freq_idx] > self.threshold:
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def cleanup(self):
        """Cleanup audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()