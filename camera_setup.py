import cv2
import requests
import json
from urllib.parse import urlparse

class CameraManager:
    def __init__(self):
        self.camera_sources = {}
        self.active_camera = None
    
    def add_mobile_camera(self, name, ip_address, port=8080):
        """
        Add mobile phone camera via IP Webcam app
        """
        url = f"http://{ip_address}:{port}/video"
        self.camera_sources[name] = {
            'type': 'ip_camera',
            'url': url,
            'status_url': f"http://{ip_address}:{port}/sensors.json"
        }
    
    def add_usb_camera(self, name, device_index=0):
        """
        Add USB camera
        """
        self.camera_sources[name] = {
            'type': 'usb_camera',
            'device_index': device_index
        }
    
    def connect_camera(self, camera_name):
        """
        Connect to specified camera
        """
        if camera_name not in self.camera_sources:
            print(f"Camera {camera_name} not found")
            return False
        
        camera_info = self.camera_sources[camera_name]
        
        if camera_info['type'] == 'ip_camera':
            try:
                # Test connection first
                response = requests.get(camera_info['status_url'], timeout=5)
                if response.status_code == 200:
                    self.active_camera = cv2.VideoCapture(camera_info['url'])
                    print(f"Connected to IP camera: {camera_name}")
                    return True
            except requests.RequestException:
                print(f"Failed to connect to IP camera: {camera_name}")
                return False
        
        elif camera_info['type'] == 'usb_camera':
            self.active_camera = cv2.VideoCapture(camera_info['device_index'])
            if self.active_camera.isOpened():
                print(f"Connected to USB camera: {camera_name}")
                return True
            else:
                print(f"Failed to connect to USB camera: {camera_name}")
                return False
        
        return False
    
    def get_frame(self):
        """
        Get current frame from active camera
        """
        if self.active_camera and self.active_camera.isOpened():
            ret, frame = self.active_camera.read()
            if ret:
                return frame
        return None
    
    def get_mobile_camera_info(self, ip_address, port=8080):
        """
        Get mobile camera sensor information
        """
        try:
            url = f"http://{ip_address}:{port}/sensors.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return json.loads(response.text)
        except requests.RequestException as e:
            print(f"Error getting camera info: {e}")
        return None
    
    def release_camera(self):
        """
        Release camera resources
        """
        if self.active_camera:
            self.active_camera.release()
            self.active_camera = None
            print("Camera released")

# Example usage and setup guide
def setup_mobile_camera():
    """
    Interactive setup for mobile camera
    """
    print("Mobile Camera Setup Guide:")
    print("1. Install 'IP Webcam' app on Android phone")
    print("2. Open the app and tap 'Start Server'")
    print("3. Note the IP address displayed (e.g., 192.168.1.100)")
    print("4. Ensure phone and computer are on same WiFi network")
    
    camera_manager = CameraManager()
    
    # Get IP address from user
    ip_address = input("Enter mobile phone IP address: ").strip()
    if not ip_address:
        ip_address = "192.168.1.100"  # Default for testing
    
    # Add and test mobile camera
    camera_manager.add_mobile_camera("mobile_phone", ip_address)
    
    if camera_manager.connect_camera("mobile_phone"):
        print("Mobile camera connected successfully!")
        
        # Test frame capture
        frame = camera_manager.get_frame()
        if frame is not None:
            cv2.imshow("Mobile Camera Test", frame)
            cv2.waitKey(2000)  # Show for 2 seconds
            cv2.destroyAllWindows()
            print("Camera test successful!")
        else:
            print("Failed to capture frame")
    else:
        print("Mobile camera connection failed")
        print("Troubleshooting:")
        print("- Check IP address is correct")
        print("- Ensure IP Webcam app is running")
        print("- Verify WiFi connection")
    
    camera_manager.release_camera()
    return camera_manager