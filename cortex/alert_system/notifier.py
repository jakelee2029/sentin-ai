"""
Alert System - Multi-channel Notification Dispatcher

Sends verified fire alerts via:
- SMS (Twilio)
- Push notifications
- Email
- Ethernet uplink to cloud
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Optional Twilio for SMS
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠ Twilio not available. SMS alerts disabled.")


class AlertDispatcher:
    """Multi-channel alert system for fire verification"""
    
    def __init__(self, config_path="integration/config.yaml"):
        """
        Initialize alert dispatcher
        
        Args:
            config_path: Path to system configuration
        """
        self.config = self._load_config(config_path)
        self.twilio_client = None
        self.alert_history = []
        
        if TWILIO_AVAILABLE:
            self._init_twilio()
    
    def _load_config(self, config_path):
        """Load configuration from YAML"""
        import yaml
        
        if not Path(config_path).exists():
            print(f"⚠ Config not found: {config_path}")
            return self._default_config()
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _default_config(self):
        """Return default configuration"""
        return {
            'alerts': {
                'contacts': {
                    'primary': {
                        'name': 'Homeowner',
                        'phone': '+1-XXX-XXX-XXXX',
                        'email': 'owner@example.com'
                    }
                },
                'channels': {
                    'sms': False,
                    'push': True,
                    'email': True,
                    'ethernet_uplink': True
                }
            },
            'network': {
                'uplink': {
                    'endpoint': 'https://sentin-cloud.example.com/api/alert',
                    'api_key': 'your-api-key-here'
                }
            }
        }
    
    def _init_twilio(self):
        """Initialize Twilio client for SMS"""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if account_sid and auth_token:
            self.twilio_client = Client(account_sid, auth_token)
            print("✓ Twilio initialized for SMS alerts")
        else:
            print("⚠ Twilio credentials not found (set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)")
    
    def send_alert(self, alert_type, data, image_path=None):
        """
        Send multi-channel alert
        
        Args:
            alert_type: 'fire_confirmed', 'potential_hazard', 'test'
            data: Alert data dict with sensor readings
            image_path: Optional path to verification image
        
        Returns:
            dict with status of each channel
        """
        timestamp = datetime.now().isoformat()
        
        alert_message = self._format_alert_message(alert_type, data, timestamp)
        
        results = {
            'timestamp': timestamp,
            'alert_type': alert_type,
            'channels': {}
        }
        
        # SMS Alert
        if self.config['alerts']['channels']['sms']:
            results['channels']['sms'] = self._send_sms(alert_message)
        
        # Email Alert
        if self.config['alerts']['channels']['email']:
            results['channels']['email'] = self._send_email(alert_message, image_path)
        
        # Push Notification
        if self.config['alerts']['channels']['push']:
            results['channels']['push'] = self._send_push(alert_message)
        
        # Ethernet Uplink (Critical hardwired connection)
        if self.config['alerts']['channels']['ethernet_uplink']:
            results['channels']['ethernet'] = self._send_uplink(alert_type, data, image_path)
        
        # Log alert
        self.alert_history.append(results)
        self._save_alert_log(results)
        
        return results
    
    def _format_alert_message(self, alert_type, data, timestamp):
        """Format alert message for human readability"""
        
        if alert_type == 'fire_confirmed':
            severity = "🚨 FIRE CONFIRMED"
        elif alert_type == 'potential_hazard':
            severity = "⚠️ POTENTIAL HAZARD"
        else:
            severity = "ℹ️ SYSTEM TEST"
        
        message = f"""
{severity}
Time: {timestamp}

Sensor Data:
- UV Level: {data.get('uv_value', 'N/A')}
- VOC: {data.get('voc_ppb', 'N/A')} ppb
- Temperature: {data.get('temperature', 'N/A')}°C

AI Verification:
- Flame Detected: {data.get('flame_detected', 'N/A')}
- Confidence: {data.get('confidence', 0):.1%}
- Material: {data.get('material', 'Unknown')}

IMMEDIATE ACTION REQUIRED
Call 911 if not already alerted
Evacuate premises immediately
        """.strip()
        
        return message
    
    def _send_sms(self, message):
        """Send SMS alert via Twilio"""
        if not self.twilio_client:
            return {'success': False, 'error': 'Twilio not configured'}
        
        try:
            contact = self.config['alerts']['contacts']['primary']
            
            msg = self.twilio_client.messages.create(
                body=message,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=contact['phone']
            )
            
            return {'success': True, 'sid': msg.sid}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_email(self, message, image_path=None):
        """Send email alert (placeholder - implement with your email service)"""
        
        contact = self.config['alerts']['contacts']['primary']
        
        # In production, integrate with SendGrid, AWS SES, etc.
        print(f"📧 Email alert to: {contact['email']}")
        print(message)
        
        return {'success': True, 'placeholder': True}
    
    def _send_push(self, message):
        """Send push notification (placeholder - implement with FCM/APNS)"""
        
        # In production, integrate with Firebase Cloud Messaging
        print(f"📱 Push notification sent")
        
        return {'success': True, 'placeholder': True}
    
    def _send_uplink(self, alert_type, data, image_path=None):
        """
        Send alert to cloud via hardwired Ethernet
        This is the CRITICAL path - never relies on WiFi
        """
        
        endpoint = self.config['network']['uplink']['endpoint']
        api_key = self.config['network']['uplink']['api_key']
        
        payload = {
            'device_id': self.config.get('system', {}).get('device_id', 'unknown'),
            'alert_type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'sensor_data': data
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Send JSON alert
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            # Upload image if provided
            if image_path and Path(image_path).exists():
                files = {'image': open(image_path, 'rb')}
                requests.post(
                    f"{endpoint}/image",
                    files=files,
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=10
                )
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code
            }
        
        except Exception as e:
            print(f"⚠ Uplink failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_alert_log(self, alert_data):
        """Save alert to local log file"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "alerts.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(alert_data) + '\n')


if __name__ == "__main__":
    """Demo: Test alert system"""
    
    print("Sentin-AI Alert System Test")
    print("=" * 50)
    
    dispatcher = AlertDispatcher()
    
    # Simulate fire alert
    test_data = {
        'uv_value': 250,
        'voc_ppb': 650,
        'temperature': 35.5,
        'flame_detected': True,
        'confidence': 0.92,
        'material': 'wood'
    }
    
    print("\nSending test alert...")
    results = dispatcher.send_alert('fire_confirmed', test_data)
    
    print("\nAlert Status:")
    for channel, status in results['channels'].items():
        success = "✓" if status.get('success') else "✗"
        print(f"  {success} {channel}: {status}")
