# Deployment Guide

Step-by-step instructions for deploying Sentin-AI in production.

## Prerequisites

- [ ] Hardware assembled per [Hardware Setup Guide](hardware-setup.md)
- [ ] Arduino Uno Q with PlatformIO installed
- [ ] Python 3.8+ installed on Snapdragon side
- [ ] Network connectivity (Ethernet preferred)
- [ ] SMS/email credentials for alerts (optional)

## Phase 1: Firmware Upload (Lizard Brain)

### 1. Install PlatformIO

```bash
pip install platformio
```

### 2. Compile Firmware

```bash
cd lizard-brain
pio run
```

Expected output:
```
✓ Building .pio/build/uno_q/firmware.bin
Memory Usage:
  Flash: 45.2 KB / 512 KB (8.8%)
  RAM:   12.1 KB / 96 KB (12.6%)
```

### 3. Upload to Arduino

Connect Arduino via USB, then:

```bash
pio run --target upload
```

### 4. Verify Boot

Open serial monitor (115200 baud):

```bash
pio device monitor
```

You should see:
```json
{"boot":"initializing_sensors"}
{"boot":"complete","version":"1.0.0"}
```

## Phase 2: Install Cortex Software

### 1. Install Python Dependencies

```bash
cd cortex
pip install -r ../requirements.txt
```

### 2. Configure System

Edit `integration/config.yaml`:

```yaml
system:
  device_id: "your-unique-id"
  location: "Installation Location"

alerts:
  contacts:
    primary:
      phone: "+1-XXX-XXX-XXXX"
      email: "your@email.com"

network:
  uplink:
    endpoint: "https://your-cloud-endpoint.com/api/alert"
    api_key: "your-api-key"
```

### 3. Train Flame Detection Model (if needed)

If you have a custom flame dataset:

```bash
python cortex/flame_detection/train.py --data /path/to/dataset --epochs 10
```

Otherwise, use the pre-trained model (download from releases).

### 4. Start Cortex

```bash
python cortex/main.py
```

Expected output:
```
====================================
Sentin-AI Cortex - AI Fire Verification System
=======================================

[1/5] Initializing flame detection...
  ✓ Model loaded
[2/5] Initializing camera...
  ✓ Camera opened: 640x480 @ 30fps
[3/5] Initializing gas analyzer...
  ✓ BME688 sensor initialized
[4/5] Initializing alert system...
  ✓ Twilio initialized
[5/5] Connecting to Lizard Brain...
  ✓ Connected on COM3

✓ Cortex initialization complete
```

## Phase 3: Web Dashboard

### 1. Start Dashboard Server

In a new terminal:

```bash
cd integration/dashboard
python app.py
```

### 2. Access Dashboard

Open browser to: **http://localhost:8080**

You should see:
- Real-time sensor readings
- System status (NORMAL)
- AI verification status

## Phase 4: System Testing

### 1. Sensor Verification

From the dashboard, check:
- [ ] UV reading: 30-70 (normal indoor)
- [ ] VOC: 50-200 ppb (clean air)
- [ ] Temperature: Ambient
- [ ] Camera: Live feed visible

### 2. Calibration

Click **"Calibrate Sensors"** button. Wait 20 seconds.

Verify baselines are updated in console output.

### 3. Alarm Test

Click **"Test Alarm"** button.

Expected:
- Piezo buzzer sounds
- LED flashes
- Alert appears in dashboard log

### 4. Fire Simulation

Run simulator (safe way to test without actual fire):

```bash
python simulator/sensor_sim.py
```

This will generate realistic sensor patterns. The system should:
1. Detect elevated sensor readings
2. Wake Cortex for AI verification
3. Trigger alert if fire confirmed

## Phase 5: Integration Testing

### 1. End-to-End Alert Flow

Manually trigger a simulated fire:

```python
# Send test alert to Lizard Brain
import serial
ser = serial.Serial('COM3', 115200)
ser.write(b'{"type":"alert","state":STATE_ALARM,"reason":"manual_test"}\n')
```

Verify:
- [ ] Cortex wakes up
- [ ] Camera captures frame
- [ ] AI processes image
- [ ] Alert sent to all channels (SMS, email, uplink)

### 2. Network Resilience

1. Disconnect WiFi (if using)
2. Verify Ethernet uplink still functions
3. Check alert delivery via hardwired connection

## Production Checklist

- [ ] Device mounted in optimal location (see Hardware Guide)
- [ ] Ethernet cable secured with strain relief
- [ ] Backup power supply connected (UPS recommended)
- [ ] Alert contacts verified and tested
- [ ] Weekly self-test scheduled
- [ ] System logs monitored (check `logs/` directory)
- [ ] Fire department notification protocol established

## Monitoring & Maintenance

### Log Files

- `logs/sentin-ai.log` - System events
- `logs/alerts.jsonl` - Alert history
- `logs/evidence/` - Fire verification images

### Weekly Tasks

1. Review log files for anomalies
2. Test alarm via dashboard
3. Verify sensor calibration (check baselines)
4. Inspect physical connections

### Monthly Tasks

1. Clean camera lens
2. Verify Ethernet connectivity
3. Update firmware if new version available
4. Review and test alert contact list

## Troubleshooting

### Lizard Brain Not Responding

```bash
# Check serial connection
pio device list

# Re-upload firmware
pio run --target upload
```

### Cortex Can't Connect to Camera

**USB Camera Troubleshooting:**

```bash
# List available USB cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# Test specific camera ID
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera 0:', cap.isOpened()); cap.release()"
```

**Common solutions:**
1. Verify Logitech Brio 101 is connected via USB
2. Check USB hub has power (LED indicator)
3. Try different USB port
4. Adjust `camera_id` in `integration/config.yaml` if device ID changed
5. Ensure no other application is using the camera

### Alerts Not Sending

1. Check `integration/config.yaml` credentials
2. Verify network connectivity: `ping google.com`
3. Test SMS manually: `python cortex/alert_system/notifier.py`
4. Check logs for error messages

### False Alarms

If frequent false positives:

1. Recalibrate sensors (clean environment)
2. Adjust thresholds in `integration/config.yaml`
3. Move device away from cooking area / humidity sources
4. Increase AI confidence threshold (default: 0.85)

## Cloud Integration (Optional)

For remote monitoring and alerts:

1. Deploy cloud endpoint (AWS Lambda / Google Cloud Functions)
2. Configure endpoint in `config.yaml`
3. Implement webhook receiver for alerts
4. Set up database for historical data

Example endpoint (Python/Flask):

```python
@app.route('/api/alert', methods=['POST'])
def receive_alert():
    data = request.json
    # Log to database, trigger notifications, etc.
    return {'status': 'received'}
```

## Support & Community

- **Documentation**: `/docs` directory
- **Issues**: GitHub repository
- **Community**: Join Ridgewood Fire Safety Initiative

---

**Deployment Complete!** Your Sentin-AI system is now protecting your home.

*In memory of those who lost their homes. In service of those we can still save.*
