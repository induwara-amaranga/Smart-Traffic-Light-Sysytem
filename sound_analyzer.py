import numpy as np
import pyaudio
import threading
from scipy import signal
from collections import deque
import time

class EmergencyVehicleDetector:
    def __init__(self, sample_rate=44100, chunk_size=4096):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        
        # Emergency vehicle frequency patterns (Hz)
        self.siren_frequencies = [
            (400, 1200),   # Ambulance siren range
            (300, 800),    # Fire truck horn
            (500, 1500),   # Police siren
        ]
        
        self.is_detecting = False
        self.detection_callback = None
        self.audio_buffer = deque(maxlen=100)
        
    def start_detection(self, callback_function):
        """
        Start real-time audio analysis for emergency vehicles
        """
        self.detection_callback = callback_function
        self.is_detecting = True
        
        # Open audio stream
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        print("Emergency vehicle detection started...")
    
    def stop_detection(self):
        """
        Stop audio detection
        """
        self.is_detecting = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Process audio data in real-time
        """
        if self.is_detecting:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            self.audio_buffer.append(audio_data)
            
            # Analyze for emergency vehicle patterns
            threading.Thread(target=self._analyze_audio, 
                           args=(audio_data.copy(),), daemon=True).start()
        
        return (None, pyaudio.paContinue)
    
    def _analyze_audio(self, audio_data):
        """
        Analyze audio data for emergency vehicle signatures
        """
        # Compute FFT
        fft = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        magnitude = np.abs(fft)
        
        # Find dominant frequencies
        peak_indices = signal.find_peaks(magnitude, height=np.max(magnitude)*0.1)[0]
        peak_frequencies = np.abs(freqs[peak_indices])
        
        # Check for emergency vehicle patterns
        emergency_detected = False
        vehicle_type = None
        
        for freq_range in self.siren_frequencies:
            low_freq, high_freq = freq_range
            matching_peaks = [f for f in peak_frequencies 
                            if low_freq <= f <= high_freq]
            
            if len(matching_peaks) >= 2:  # Multiple peaks in siren range
                emergency_detected = True
                if freq_range == (400, 1200):
                    vehicle_type = "Ambulance"
                elif freq_range == (300, 800):
                    vehicle_type = "Fire Truck"
                elif freq_range == (500, 1500):
                    vehicle_type = "Police"
                break
        
        # Additional pattern analysis for siren modulation
        if emergency_detected:
            # Check for characteristic siren sweep pattern
            if self._detect_siren_sweep(audio_data):
                if self.detection_callback:
                    self.detection_callback(vehicle_type, peak_frequencies)
    
    def _detect_siren_sweep(self, audio_data):
        """
        Detect characteristic frequency sweep of emergency sirens
        """
        # Compute spectrogram for time-frequency analysis
        f, t, Sxx = signal.spectrogram(audio_data, self.sample_rate)
        
        # Look for frequency sweeps typical of sirens
        for i in range(len(t)-1):
            spectrum_current = Sxx[:, i]
            spectrum_next = Sxx[:, i+1]
            
            # Find peak frequencies at current and next time
            peak_current = f[np.argmax(spectrum_current)]
            peak_next = f[np.argmax(spectrum_next)]
            
            # Check for significant frequency change (sweep)
            freq_change = abs(peak_next - peak_current)
            if freq_change > 50:  # Significant frequency sweep
                return True
        
        return False

# Emergency detection callback function
def on_emergency_detected(vehicle_type, frequencies):
    """
    Callback function when emergency vehicle is detected
    """
    print(f"EMERGENCY DETECTED: {vehicle_type}")
    print(f"Dominant frequencies: {frequencies[:3]}")
    
    # Here you would trigger the traffic light priority system
    # This connects to the main traffic controller