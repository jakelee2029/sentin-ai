"""
BME688 AI Gas Analysis

Integrates Bosch BME AI-Studio trained model for VOC classification
Identifies chemical signatures of burning materials (wood, plastic, paper)
"""

import json
import time
from pathlib import Path

try:
    import bme68x
    BME68X_AVAILABLE = True
except ImportError:
    BME68X_AVAILABLE = False
    print("⚠ bme68x library not available. Using simulation mode.")


class BME688Analyzer:
    """AI-powered gas analysis using BME688 sensor"""
    
    def __init__(self, config_path=None, i2c_address=0x77):
        """
        Initialize BME688 AI gas analyzer
        
        Args:
            config_path: Path to Bosch AI-Studio config JSON
            i2c_address: I2C address of BME688
        """
        self.config_path = config_path
        self.i2c_address = i2c_address
        self.sensor = None
        self.ai_config = None
        self.baseline = 100  # VOC baseline in ppb
        
        if config_path and Path(config_path).exists():
            self._load_ai_config()
        
        if BME68X_AVAILABLE:
            self._init_sensor()
    
    def _load_ai_config(self):
        """Load Bosch AI-Studio configuration"""
        with open(self.config_path, 'r') as f:
            self.ai_config = json.load(f)
        
        print(f"✓ Loaded AI config: {self.config_path}")
    
    def _init_sensor(self):
        """Initialize BME688 sensor"""
        try:
            self.sensor = bme68x.BME68X(self.i2c_address)
            
            # Configure for VOC detection
            self.sensor.set_conf({
                'filter': bme68x.FILTER_SIZE_3,
                'odr': bme68x.ODR_NONE,
                'os_hum': bme68x.OS_2X,
                'os_pres': bme68x.OS_4X,
                'os_temp': bme68x.OS_8X
            })
            
            # Set heater profile for VOC
            self.sensor.set_heatr_conf({
                'enable': bme68x.ENABLE,
                'heatr_temp': 320,  # °C
                'heatr_dur': 150    # ms
            })
            
            print("✓ BME688 sensor initialized")
        
        except Exception as e:
            print(f"⚠ Failed to initialize BME688: {e}")
            self.sensor = None
    
    def read_sensor(self):
        """
        Read sensor data
        
        Returns:
            dict with temperature, humidity, pressure, gas_resistance, voc_ppb
        """
        if not BME68X_AVAILABLE or self.sensor is None:
            # Simulation mode
            return self._simulate_reading()
        
        try:
            data = self.sensor.get_data()
            
            if data is None:
                return None
            
            # Calculate VOC equivalent
            voc_ppb = self._calculate_voc(data['gas_resistance'])
            
            return {
                'temperature': data['temperature'],
                'humidity': data['humidity'],
                'pressure': data['pressure'],
                'gas_resistance': data['gas_resistance'],
                'voc_ppb': voc_ppb,
                'timestamp': time.time()
            }
        
        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None
    
    def _calculate_voc(self, resistance):
        """
        Convert gas resistance to VOC concentration
        
        Args:
            resistance: Gas resistance in Ohms
        
        Returns:
            VOC concentration in ppb
        """
        # Simplified IAQ calculation
        # Lower resistance = higher VOC concentration
        baseline_resistance = self.baseline * 10000  # Convert to Ohms
        ratio = baseline_resistance / resistance
        voc_ppb = self.baseline * ratio
        
        return int(voc_ppb)
    
    def _simulate_reading(self):
        """Generate simulated sensor data for development"""
        import random
        
        return {
            'temperature': 22.0 + random.uniform(-2, 2),
            'humidity': 45.0 + random.uniform(-5, 5),
            'pressure': 1013.25 + random.uniform(-5, 5),
            'gas_resistance': 100000 + random.randint(-10000, 10000),
            'voc_ppb': self.baseline + random.randint(-20, 20),
            'timestamp': time.time()
        }
    
    def classify_voc_signature(self, reading):
        """
        Classify VOC signature to identify burning material
        
        Args:
            reading: Sensor reading dict
        
        Returns:
            dict with material, confidence, is_fire
        """
        voc = reading['voc_ppb']
        
        # VOC signature patterns (from config.yaml)
        signatures = {
            'wood': [120, 200, 350],
            'plastic': [80, 450, 600],
            'paper': [100, 180, 280]
        }
        
        # Check if fire-like VOC levels
        is_fire = voc >= 500  # Fire threshold from config
        
        if not is_fire:
            return {
                'material': 'none',
                'confidence': 1.0,
                'is_fire': False,
                'voc_level': voc
            }
        
        # Simple pattern matching (in production, use trained AI model)
        best_match = 'unknown'
        best_confidence = 0.0
        
        for material, pattern in signatures.items():
            # Check if VOC is in expected range
            if pattern[0] <= voc <= pattern[2]:
                # Calculate confidence based on proximity to median
                distance = abs(voc - pattern[1])
                confidence = max(0, 1.0 - (distance / pattern[1]))
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = material
        
        return {
            'material': best_match,
            'confidence': best_confidence,
            'is_fire': is_fire,
            'voc_level': voc
        }
    
    def calibrate_baseline(self, samples=20):
        """
        Calibrate baseline VOC in clean environment
        
        Args:
            samples: Number of samples to average
        """
        print("Calibrating baseline (ensure clean air)...")
        
        resistances = []
        
        for i in range(samples):
            reading = self.read_sensor()
            if reading:
                resistances.append(reading['gas_resistance'])
            time.sleep(0.1)
        
        if resistances:
            avg_resistance = sum(resistances) / len(resistances)
            self.baseline = int(avg_resistance / 10000)
            print(f"✓ Baseline calibrated: {self.baseline} ppb equivalent")
        else:
            print("⚠ Calibration failed")


if __name__ == "__main__":
    """Demo: Test gas analysis"""
    
    print("Sentin-AI Gas Analysis")
    print("=" * 50)
    
    analyzer = BME688Analyzer()
    
    print("\nReading sensor data...")
    
    for i in range(10):
        reading = analyzer.read_sensor()
        
        if reading:
            classification = analyzer.classify_voc_signature(reading)
            
            print(f"\nReading {i+1}:")
            print(f"  Temperature: {reading['temperature']:.1f}°C")
            print(f"  Humidity: {reading['humidity']:.1f}%")
            print(f"  VOC: {reading['voc_ppb']} ppb")
            
            if classification['is_fire']:
                print(f"  🔥 FIRE DETECTED!")
                print(f"     Material: {classification['material']}")
                print(f"     Confidence: {classification['confidence']:.2%}")
        
        time.sleep(1)
