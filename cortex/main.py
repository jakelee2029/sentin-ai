"""
Sentin-AI Cortex - AI Processing Core

Event-driven orchestrator for Snapdragon processor
Sleeps until awakened by Lizard Brain hazard detection
"""

import sys
import time
import json
import yaml
import serial
from pathlib import Path
from datetime import datetime

# Import Cortex modules
sys.path.append(str(Path(__file__).parent))

from flame_detection.inference import FlameInference, CameraCapture
from gas_analysis.bme688_ai import BME688Analyzer
from alert_system.notifier import AlertDispatcher


class SentinCortex:
    """Main orchestrator for AI fire verification"""
    
    def __init__(self, config_path="integration/config.yaml"):
        """
        Initialize Cortex system
        
        Args:
            config_path: Path to system configuration
        """
        print("=" * 60)
        print("Sentin-AI Cortex - AI Fire Verification System")
        print("=" * 60)
        
        self.config = self._load_config(config_path)
        self.state = "idle"
        
        # Initialize components
        print("\n[1/5] Initializing flame detection...")
        self.flame_detector = self._init_flame_detector()
        
        print("[2/5] Initializing camera...")
        self.camera = self._init_camera()
        
        print("[3/5] Initializing gas analyzer...")
        self.gas_analyzer = self._init_gas_analyzer()
        
        print("[4/5] Initializing alert system...")
        self.alert_dispatcher = AlertDispatcher(config_path)
        
        print("[5/5] Connecting to Lizard Brain...")
        self.ipc_serial = self._init_ipc()
        
        print("\n✓ Cortex initialization complete")
        print(f"  State: {self.state}")
        print(f"  Waiting for signals from Lizard Brain...\n")
    
    def _load_config(self, config_path):
        """Load system intelligence"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _init_flame_detector(self):
        """Initialize CNN flame detection"""
        model_path = self.config['ai']['flame_detection']['model_path']
        threshold = self.config['ai']['flame_detection']['confidence_threshold']
        
        if not Path(model_path).exists():
            print(f"  ⚠ Model not found: {model_path}")
            print(f"    Run: python cortex/flame_detection/train.py --data <dataset>")
            return None
        
        return FlameInference(model_path, threshold)
    
    def _init_camera(self):
        """Initialize USB camera (Logitech Brio 101)"""
        res = self.config['sensors']['camera']['resolution']
        fps = self.config['sensors']['camera']['fps']
        
        try:
            camera = CameraCapture(
                camera_id=0,
                resolution=tuple(res),
                fps=fps
            )
            camera.open()
            return camera
        except Exception as e:
            print(f"  ⚠ Camera initialization failed: {e}")
            print(f"    System will operate without visual verification")
            return None
    
    def _init_gas_analyzer(self):
        """Initialize BME688 AI gas analysis"""
        config_file = self.config['ai'].get('gas_classifier', {}).get('bme688_model')
        
        return BME688Analyzer(config_path=config_file)
    
    def _init_ipc(self):
        """Initialize serial communication with Lizard Brain"""
        port = self.config['ipc']['serial_port']
        baud = self.config['ipc']['baud_rate']
        
        try:
            ser = serial.Serial(port, baud, timeout=1)
            print(f"  ✓ Connected to Lizard Brain on {port}")
            return ser
        except Exception as e:
            print(f"  ⚠ IPC connection failed: {e}")
            print(f"    Running in standalone mode")
            return None
    
    def run(self):
        """Main event loop"""
        
        print("Cortex entering event loop...")
        print("Press Ctrl+C to exit\n")
        
        try:
            while True:
                # Check for messages from Lizard Brain
                if self.ipc_serial and self.ipc_serial.in_waiting:
                    message = self.ipc_serial.readline().decode('utf-8').strip()
                    self.handle_ipc_message(message)
                
                # Send heartbeat
                self.send_heartbeat()
                
                # Small sleep to prevent busywaiting
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\n⛔ Cortex shutdown requested")
            self.shutdown()
    
    def handle_ipc_message(self, message):
        """
        Process message from Lizard Brain
        
        Args:
            message: JSON string from STM32
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'alert':
                self.handle_alert(data)
            elif msg_type == 'sensor_data':
                self.handle_sensor_update(data)
            elif msg_type == 'heartbeat':
                pass  # Acknowledge but no action
            else:
                print(f"Unknown message type: {msg_type}")
        
        except json.JSONDecodeError:
            print(f"Invalid JSON from Lizard Brain: {message}")
    
    def handle_alert(self, alert_data):
        """
        Handle fire alert from Lizard Brain
        Wake up and verify with AI!
        
        Args:
            alert_data: Alert message from STM32
        """
        state = alert_data.get('state')
        reason = alert_data.get('reason', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"🚨 ALERT RECEIVED from Lizard Brain")
        print(f"   State: {state}")
        print(f"   Reason: {reason}")
        print(f"{'='*60}\n")
        
        self.state = "verifying"
        
        # Run AI verification
        verification_result = self.verify_fire()
        
        # Make decision
        if verification_result['fire_confirmed']:
            self.trigger_fire_alarm(verification_result)
        else:
            print("✓ AI verification: False alarm")
            self.state = "idle"
    
    def verify_fire(self):
        """
        Multi-modal AI verification
        
        Returns:
            dict with verification results
        """
        print("[AI Verification Protocol Initiated]")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'fire_confirmed': False,
            'confidence': 0.0,
            'evidence': {}
        }
        
        # Step 1: Visual verification
        print("  [1/3] Camera: Capturing frame...")
        if self.camera and self.flame_detector:
            frame = self.camera.read_frame()
            
            if frame is not None:
                detection = self.flame_detector.detect_flame(frame)
                result['evidence']['visual'] = detection
                
                print(f"        Flame detected: {detection['flame_detected']}")
                print(f"        Confidence: {detection['confidence']:.2%}")
                
                # Save evidence
                if detection['flame_detected']:
                    import cv2
                    evidence_dir = Path("logs/evidence")
                    evidence_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    evidence_path = evidence_dir / f"fire_{timestamp}.jpg"
                    cv2.imwrite(str(evidence_path), frame)
                    result['evidence']['image_path'] = str(evidence_path)
        
        # Step 2: Gas analysis
        print("  [2/3] Gas Sensor: Analyzing VOC signature...")
        gas_reading = self.gas_analyzer.read_sensor()
        
        if gas_reading:
            gas_classification = self.gas_analyzer.classify_voc_signature(gas_reading)
            result['evidence']['gas'] = gas_classification
            
            print(f"        VOC level: {gas_reading['voc_ppb']} ppb")
            print(f"        Fire signature: {gas_classification['is_fire']}")
            print(f"        Material: { gas_classification['material']}")
        
        # Step 3: Multi-modal fusion
        print("  [3/3] AI Fusion: Combining sensor data...")
        
        flame_detected = result['evidence'].get('visual', {}).get('flame_detected', False)
        gas_fire = result['evidence'].get('gas', {}).get('is_fire', False)
        
        # Both sensors must agree for confirmed fire
        if flame_detected and gas_fire:
            result['fire_confirmed'] = True
            result['confidence'] = result['evidence']['visual']['confidence']
            print("        ✓ FIRE CONFIRMED (dual sensor agreement)")
        elif flame_detected or gas_fire:
            result['fire_confirmed'] = False
            result['confidence'] = 0.5
            print("        ⚠ Inconclusive (sensors disagree)")
        else:
            result['fire_confirmed'] = False
            result['confidence'] = 0.0
            print("        ✓ All clear")
        
        return result
    
    def trigger_fire_alarm(self, verification_data):
        """
        Send verified fire alert through all channels
        
        Args:
            verification_data: Results from AI verification
        """
        self.state = "alarm"
        
        print("\n" + "="*60)
        print("🔥 VERIFIED FIRE - DISPATCHING ALERTS")
        print("="*60 + "\n")
        
        # Prepare alert data
        alert_data = {
            'uv_value': 'N/A',  # Would come from sensor_data
            'voc_ppb': verification_data['evidence'].get('gas', {}).get('voc_level', 'N/A'),
            'temperature': 'N/A',
            'flame_detected': True,
            'confidence': verification_data['confidence'],
            'material': verification_data['evidence'].get('gas', {}).get('material', 'Unknown')
        }
        
        # Get evidence image
        image_path = verification_data['evidence'].get('image_path')
        
        # Send alerts
        alert_results = self.alert_dispatcher.send_alert(
            'fire_confirmed',
            alert_data,
            image_path
        )
        
        print("\nAlert Status:")
        for channel, status in alert_results['channels'].items():
            icon = "✓" if status.get('success') else "✗"
            print(f"  {icon} {channel.upper()}: {status}")
    
    def handle_sensor_update(self, sensor_data):
        """Handle periodic sensor data from Lizard Brain"""
        # Could log to database, update dashboard, etc.
        pass
    
    def send_heartbeat(self):
        """Send periodic heartbeat to Lizard Brain"""
        if self.ipc_serial:
            try:
                self.ipc_serial.write(b'{"type":"heartbeat"}\n')
            except:
                pass
    
    def shutdown(self):
        """Clean shutdown"""
        print("Shutting down Cortex...")
        
        if self.camera:
            self.camera.close()
        
        if self.ipc_serial:
            self.ipc_serial.close()
        
        print("✓ Cortex offline")


if __name__ == "__main__":
    """Entry point"""
    
    cortex = SentinCortex()
    cortex.run()
