# main_controller.py
import serial
import json
import threading
import time
from datetime import datetime
import queue
from vehicle_detector import VehicleDetector
from camera_manager import CameraManager
from sound_processor import SoundProcessor
import asyncio
import websockets

class SmartTrafficController:
    def __init__(self, arduino_port='COM3', baudrate=115200):
        # Arduino connection
        self.arduino = serial.Serial(arduino_port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino to initialize
        
        # Initialize components
        self.camera_manager = CameraManager()
        self.vehicle_detector = VehicleDetector()
        self.sound_processor = SoundProcessor()
        
        # Data storage
        self.traffic_data = {
            'state': 0,
            'vehicles': [0, 0, 0, 0],
            'emergency': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Threading
        self.running = True
        self.data_queue = queue.Queue()
        self.websocket_clients = set()
        
    def start(self):
        """Start all threads"""
        threads = [
            threading.Thread(target=self.arduino_communication_thread),
            threading.Thread(target=self.camera_processing_thread),
            threading.Thread(target=self.sound_processing_thread),
            threading.Thread(target=self.websocket_server_thread)
        ]
        
        for thread in threads:
            thread.daemon = True
            thread.start()
        
        print("Smart Traffic System Started")
        
        try:
            while True:
                time.sleep(1)
                self.print_status()
        except KeyboardInterrupt:
            self.stop()
    
    def arduino_communication_thread(self):
        """Handle Arduino serial communication"""
        while self.running:
            try:
                if self.arduino.in_waiting:
                    line = self.arduino.readline().decode('utf-8').strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.traffic_data.update(data)
                            self.traffic_data['timestamp'] = datetime.now().isoformat()
                            self.broadcast_to_websockets(self.traffic_data)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON from Arduino: {line}")
                
                # Send updates to Arduino
                if not self.data_queue.empty():
                    command = self.data_queue.get()
                    self.arduino.write(f"{command}\n".encode())
                    
            except Exception as e:
                print(f"Arduino communication error: {e}")
                time.sleep(0.1)
    
    def camera_processing_thread(self):
        """Process camera feeds for vehicle detection"""
        cameras = self.camera_manager.get_cameras()
        
        while self.running:
            try:
                for direction, camera in cameras.items():
                    frame = camera.read()
                    if frame is not None:
                        vehicle_count = self.vehicle_detector.detect_vehicles(frame)
                        
                        # Send update to Arduino
                        direction_map = {'north': 0, 'east': 1, 'south': 2, 'west': 3}
                        if direction in direction_map:
                            command = f"VEHICLE:{direction_map[direction]}:{vehicle_count}"
                            self.data_queue.put(command)
                
                time.sleep(0.5)  # Process at 2 FPS
                
            except Exception as e:
                print(f"Camera processing error: {e}")
                time.sleep(1)
    
    def sound_processing_thread(self):
        """Process audio for emergency vehicle detection"""
        while self.running:
            try:
                is_emergency = self.sound_processor.detect_emergency_siren()
                
                if is_emergency and not self.traffic_data.get('emergency', False):
                    print("Emergency vehicle detected!")
                    self.data_queue.put("EMERGENCY")
                elif not is_emergency and self.traffic_data.get('emergency', False):
                    self.data_queue.put("NORMAL")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Sound processing error: {e}")
                time.sleep(1)
    
    def websocket_server_thread(self):
        """WebSocket server for real-time data"""
        asyncio.new_event_loop().run_until_complete(self.websocket_server())
    
    async def websocket_server(self):
        """WebSocket server implementation"""
        async def handler(websocket, path):
            self.websocket_clients.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                self.websocket_clients.remove(websocket)
        
        async with websockets.serve(handler, "localhost", 8765):
            await asyncio.Future()  # Run forever
    
    def broadcast_to_websockets(self, data):
        """Send data to all connected WebSocket clients"""
        message = json.dumps(data)
        for client in self.websocket_clients.copy():
            try:
                asyncio.run(client.send(message))
            except:
                self.websocket_clients.remove(client)
    
    def print_status(self):
        """Print current system status"""
        print(f"\rState: {self.traffic_data['state']} | "
              f"Vehicles: {self.traffic_data['vehicles']} | "
              f"Emergency: {self.traffic_data['emergency']}", end='')
    
    def stop(self):
        """Stop all threads and cleanup"""
        self.running = False
        self.arduino.close()
        self.camera_manager.cleanup()
        print("\nSystem stopped")

if __name__ == "__main__":
    # Update with your Arduino port
    controller = SmartTrafficController(arduino_port='COM3')
    controller.start()