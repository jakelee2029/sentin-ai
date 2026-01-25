"""
Hardware Sensor Simulator

Simulates UV, gas, and camera sensors for development without physical hardware
Supports realistic fire scenarios for testing
"""

import random
import time
import math
from enum import Enum


class SimulationMode(Enum):
    """Simulation scenarios"""
    NORMAL = "normal"
    SMOLDERING_FIRE = "smoldering"
    ELECTRICAL_FIRE = "electrical"
    FALSE_ALARM_TOAST = "toast"
    GRADUAL_FIRE = "gradual"


class SensorSimulator:
    """Simulates all Sentin-AI sensors"""
    
    def __init__(self, mode=SimulationMode.NORMAL):
        """
        Initialize simulator
        
        Args:
            mode: Simulation mode (scenario)
        """
        self.mode = mode
        self.start_time = time.time()
        self.noise_level = 0.05  # 5% noise
        
        # Baseline values
        self.baselines = {
            'uv': 50,
            'voc': 100,
            'temperature': 22.0,
            'humidity': 45.0
        }
        
        # Scenario parameters
        self.scenario_active = False
        self.scenario_start_time = 0
    
    def start_scenario(self):
        """Start the configured scenario"""
        self.scenario_active = True
        self.scenario_start_time = time.time()
        print(f"📊 Starting scenario: {self.mode.value}")
    
    def get_elapsed_time(self):
        """Get time since scenario started (seconds)"""
        if not self.scenario_active:
            return 0
        return time.time() - self.scenario_start_time
    
    def read_uv_sensor(self):
        """
        Simulate UV sensor reading
        
        Returns:
            UV ADC value (0-1023)
        """
        baseline = self.baselines['uv']
        noise = random.gauss(0, baseline * self.noise_level)
        
        if not self.scenario_active:
            return int(baseline + noise)
        
        elapsed = self.get_elapsed_time()
        
        if self.mode == SimulationMode.SMOLDERING_FIRE:
            # Slow UV increase (smoldering doesn't produce much UV initially)
            value = baseline + (elapsed * 5) + noise
        
        elif self.mode == SimulationMode.ELECTRICAL_FIRE:
            # Rapid UV spike
            value = baseline + (elapsed * 30) + noise
        
        elif self.mode == SimulationMode.FALSE_ALARM_TOAST:
            # No UV from toast
            value = baseline + noise
        
        elif self.mode == SimulationMode.GRADUAL_FIRE:
            # Exponential growth
            value = baseline * math.exp(elapsed * 0.1) + noise
        
        else:
            value = baseline + noise
        
        return int(min(1023, max(0, value)))
    
    def read_gas_sensor(self):
        """
        Simulate BME688 gas sensor
        
        Returns:
            dict with voc_ppb, temperature, humidity, pressure
        """
        noise_voc = random.gauss(0, self.baselines['voc'] * self.noise_level)
        noise_temp = random.gauss(0, 0.5)
        noise_humidity = random.gauss(0, 2.0)
        
        voc = self.baselines['voc']
        temp = self.baselines['temperature']
        humidity = self.baselines['humidity']
        
        if self.scenario_active:
            elapsed = self.get_elapsed_time()
            
            if self.mode == SimulationMode.SMOLDERING_FIRE:
                # High VOC from incomplete combustion
                voc = 100 + (elapsed * 60) + noise_voc
                temp = 22 + (elapsed * 2) + noise_temp
            
            elif self.mode == SimulationMode.ELECTRICAL_FIRE:
                # Extremely high VOC (burning plastic)
                voc = 100 + (elapsed * 100) + noise_voc
                temp = 22 + (elapsed * 5) + noise_temp
            
            elif self.mode == SimulationMode.FALSE_ALARM_TOAST:
                # Moderate VOC but no real fire signature
                voc = 100 + 200 + noise_voc  # Constant elevated level
                temp = 22 + noise_temp
            
            elif self.mode == SimulationMode.GRADUAL_FIRE:
                # Realistic fire development curve
                voc = 100 * math.exp(elapsed * 0.15) + noise_voc
                temp = 22 + (elapsed * 3) + noise_temp
        
        return {
            'voc_ppb': int(min(2000, max(0, voc))),
            'temperature': round(temp + noise_temp, 1),
            'humidity': round(humidity + noise_humidity, 1),
            'pressure': round(1013.25 + random.gauss(0, 2), 2),
            'gas_resistance': int(100000 / (voc / 100))  # Inverse relationship
        }
    
    def generate_camera_frame(self, width=640, height=480):
        """
        Generate simulated camera frame
        
        Args:
            width: Frame width
            height: Frame height
        
        Returns:
            numpy array (for realistic testing, use actual flame images)
        """
        import numpy as np
        
        # Create base frame (dark room)
        frame = np.random.randint(20, 40, (height, width, 3), dtype=np.uint8)
        
        if self.scenario_active and self.mode != SimulationMode.FALSE_ALARM_TOAST:
            elapsed = self.get_elapsed_time()
            
            # Add "flame" region (orange/red glow)
            if elapsed > 2:  # Flames appear after 2 seconds
                center_x = width // 2
                center_y = int(height * 0.7)
                radius = int(min(width, height) * 0.2 * min(1.0, elapsed / 10))
                
                y, x = np.ogrid[:height, :width]
                mask = (x - center_x)**2 + (y - center_y)**2 <= radius**2
                
                # Orange/red flame colors
                frame[mask] = [30, 100, 255]  # BGR: orange
        
        return frame


class FireScenarioRunner:
    """Runs automated fire scenarios for testing"""
    
    def __init__(self):
        self.simulator = SensorSimulator()
    
    def run_scenario(self, mode, duration=30):
        """
        Run a fire scenario for testing
        
        Args:
            mode: SimulationMode scenario
            duration: How long to run (seconds)
        """
        print("="*60)
        print(f"Fire Scenario: {mode.value.upper()}")
        print("="*60)
        
        self.simulator.mode = mode
        self.simulator.start_scenario()
        
        start = time.time()
        
        while time.time() - start < duration:
            elapsed = time.time() - start
            
            # Read sensors
            uv = self.simulator.read_uv_sensor()
            gas = self.simulator.read_gas_sensor()
            
            # Determine status
            uv_fire = uv >= 150
            gas_fire = gas['voc_ppb'] >= 500
            
            status = "🔥 FIRE" if (uv_fire and gas_fire) else "⚠️ ALERT" if (uv_fire or gas_fire) else "✓ Clear"
            
            print(f"[{elapsed:5.1f}s] UV:{uv:4d} VOC:{gas['voc_ppb']:4d}ppb Temp:{gas['temperature']:5.1f}°C | {status}")
            
            time.sleep(1)
        
        print(f"\n✓ Scenario complete\n")


if __name__ == "__main__":
    """Demo: Run all fire scenarios"""
    
    print("\n" + "="*60)
    print("Sentin-AI Sensor Simulator")
    print("="*60 + "\n")
    
    runner = FireScenarioRunner()
    
    # Test each scenario
    scenarios = [
        (SimulationMode.NORMAL, 10),
        (SimulationMode.FALSE_ALARM_TOAST, 15),
        (SimulationMode.SMOLDERING_FIRE, 20),
        (SimulationMode.ELECTRICAL_FIRE, 15),
        (SimulationMode.GRADUAL_FIRE, 25)
    ]
    
    for mode, duration in scenarios:
        runner.run_scenario(mode, duration)
        time.sleep(2)
    
    print("All scenarios complete!")
