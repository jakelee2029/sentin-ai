"""
IPC Bridge - Bidirectional Serial Communication

Bridges Lizard Brain (STM32) and Cortex (Snapdragon)
Handles JSON message protocol with error recovery
"""

import serial
import json
import time
import threading
from queue import Queue


class IPCBridge:
    """Serial communication bridge between dual processors"""
    
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200):
        """
        Initialize IPC bridge
        
        Args:
            port: Serial port (COM3 on Windows, / dev/ttyUSB0 on Linux)
            baud_rate: Communication speed
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.running = False
        
        # Message queues
        self.tx_queue = Queue()
        self.rx_queue = Queue()
        
        # Threads
        self.tx_thread = None
        self.rx_thread = None
        
        # Heartbeat tracking
        self.last_heartbeat_sent = 0
        self.last_heartbeat_received = 0
        self.heartbeat_interval = 1.0  # seconds
    
    def connect(self):
        """Open serial connection"""
        try:
            self.serial_conn = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=1
            )
            print(f"✓ IPC Bridge connected: {self.port} @ {self.baud_rate}")
            return True
        
        except Exception as e:
            print(f"✗ IPC connection failed: {e}")
            return False
    
    def start(self):
        """Start TX/RX threads"""
        if not self.serial_conn:
            raise RuntimeError("Serial connection not established")
        
        self.running = True
        
        # Start transmit thread
        self.tx_thread = threading.Thread(target=self._tx_worker, daemon=True)
        self.tx_thread.start()
        
        # Start receive thread
        self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.rx_thread.start()
        
        print("✓ IPC Bridge threads started")
    
    def stop(self):
        """Stop all threads and close connection"""
        self.running = False
        
        if self.tx_thread:
            self.tx_thread.join(timeout=2)
        
        if self.rx_thread:
            self.rx_thread.join(timeout=2)
        
        if self.serial_conn:
            self.serial_conn.close()
        
        print("✓ IPC Bridge stopped")
    
    def _tx_worker(self):
        """Transmit thread - sends messages from queue"""
        while self.running:
            try:
                # Send heartbeat periodically
                if time.time() - self.last_heartbeat_sent >= self.heartbeat_interval:
                    self.send_message({"type": "heartbeat"})
                    self.last_heartbeat_sent = time.time()
                
                # Send queued messages
                if not self.tx_queue.empty():
                    message = self.tx_queue.get(timeout=0.1)
                    self._write_json(message)
                else:
                    time.sleep(0.01)
            
            except Exception as e:
                print(f"TX error: {e}")
    
    def _rx_worker(self):
        """Receive thread - reads messages and queues them"""
        buffer = ""
        
        while self.running:
            try:
                if self.serial_conn.in_waiting:
                    data = self.serial_conn.read(
                        self.serial_conn.in_waiting
                    ).decode('utf-8', errors='ignore')
                    
                    buffer += data
                    
                    # Process complete lines (JSON messages)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            self._handle_received_line(line)
                else:
                    time.sleep(0.01)
            
            except Exception as e:
                print(f"RX error: {e}")
    
    def _handle_received_line(self, line):
        """Parse and queue received message"""
        try:
            message = json.loads(line)
            
            # Update heartbeat timestamp
            if message.get('type') == 'heartbeat':
                self.last_heartbeat_received = time.time()
            
            self.rx_queue.put(message)
        
        except json.JSONDecodeError:
            print(f"Invalid JSON received: {line}")
    
    def _write_json(self, data):
        """Write JSON message to serial port"""
        try:
            json_str = json.dumps(data) + '\n'
            self.serial_conn.write(json_str.encode('utf-8'))
        except Exception as e:
            print(f"Write error: {e}")
    
    def send_message(self, message):
        """
        Queue message for transmission
        
        Args:
            message: Dict to send as JSON
        """
        self.tx_queue.put(message)
    
    def receive_message(self, timeout=None):
        """
        Get next received message
        
        Args:
            timeout: Max time to wait (None = non-blocking)
        
        Returns:
            Message dict or None
        """
        try:
            return self.rx_queue.get(timeout=timeout)
        except:
            return None
    
    def is_connected(self):
        """Check if remote processor is responsive"""
        time_since_heartbeat = time.time() - self.last_heartbeat_received
        return time_since_heartbeat < 5.0  # 5 second timeout


if __name__ == "__main__":
    """Demo: Test IPC bridge"""
    
    print("Sentin-AI IPC Bridge Test")
    print("=" * 50)
    
    # Create bridge (adjust port for your system)
    bridge = IPCBridge(port="COM3")  # or "/dev/ttyUSB0" on Linux
    
    if bridge.connect():
        bridge.start()
        
        print("\nListening for messages (press Ctrl+C to quit)...")
        
        try:
            while True:
                msg = bridge.receive_message(timeout=1.0)
                
                if msg:
                    print(f"Received: {msg}")
                
                # Show connection status
                if bridge.is_connected():
                    print(".", end="", flush=True)
                else:
                    print("⚠ Lizard Brain not responding", end="\r")
        
        except KeyboardInterrupt:
            print("\n\nStopping...")
            bridge.stop()
