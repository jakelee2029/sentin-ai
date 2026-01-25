# Hardware Setup Guide

Complete wiring and assembly instructions for Sentin-AI fire verification system.

## Required Hardware

| Component | Model | Quantity | Purpose |
|-----------|-------|----------|---------|
| **Main Board** | Arduino Uno Q | 1 | Dual-brain processor (STM32 + Snapdragon) |
| **Gas Sensor** | Waveshare BME688 | 1 | AI-powered VOC detection |
| **Camera** | Logitech Brio 101 Full HD 1080p USB | 1 | Visual flame verification |
| **UV Sensor** | UV-C Flame Detector | 1 | Fire radiation detection |
| **Ethernet Hub** | StarTech 3-Port USB-C with Gigabit | 1 | Critical hardwired uplink |
| **Piezo Buzzer** | 5V Active Buzzer | 1 | Alarm output |
| **Power Supply** | 5V 3A USB-C | 1 | System power |
| **Enclosure** | Fire-rated ABS | 1 | Housing |

## Wiring Diagram

### UV Sensor Connection

```
UV Sensor (Analog Output)
------------------------
VCC  ──→  Arduino 5V
GND  ──→  Arduino GND
OUT  ──→  Arduino A0
```

### BME688 Gas Sensor (I2C)

```
BME688 Module
-------------
VCC  ──→  Arduino 3.3V
GND  ──→  Arduino GND
SDA  ──→  Arduino Pin 4 (I2C SDA)
SCL  ──→  Arduino Pin 5 (I2C SCL)
```

> [!CAUTION]
> BME688 is 3.3V ONLY. Do not connect to 5V or the sensor will be damaged.

### Camera Connection (USB)

```
Logitech Brio 101
-----------------
Connect USB-A cable (5 ft / 1.5 m) to Arduino Uno Q USB port
(Connect via StarTech USB-C Hub if needed)

The camera will be auto-detected as device ID 0, 1, or 2
Depending on other connected USB devices
```

> [!TIP]
> To identify the camera device ID, run:
> ```bash
> python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
> ```

### Alarm Outputs

```
Piezo Buzzer
------------
+    ──→  Arduino Pin 9 (PWM)
-    ──→  Arduino GND

LED Indicator
-------------
+    ──→  Arduino Pin 13 (built-in LED)
```

### Ethernet Hub

```
StarTech USB-C Hub
------------------
USB-C  ──→  Arduino Uno Q USB-C port (Snapdragon side)
ETH    ──→  Your network router (use Cat6 cable)
```

> [!IMPORTANT]
> **Why Hardwired Ethernet?**
> 
> WiFi can fail during fires due to:
> - Power loss to router
> - Radio interference from flames
> - Signal degradation from smoke
> 
> Ethernet provides the ONLY reliable uplink in emergency conditions.

## Assembly Steps

### 1. Prepare Enclosure

- Drill mounting holes for Arduino Uno Q
- Create ventilation slots for BME688 (sensor needs air flow)
- Cut opening for camera lens
- Drill hole for Ethernet cable pass-through

### 2. Mount Components

1. Secure Arduino Uno Q to enclosure base with standoffs
2. Mount BME688 near ventilation slots
3. Position camera facing forward with clear view
4. Mount UV sensor with unobstructed exposure

### 3. Wire Connections

Follow wiring diagram above. Use:
- **Red wire**: Power (5V/3.3V)
- **Black wire**: Ground
- **Other colors**: Signal lines

> [!TIP]
> Label each wire with masking tape to avoid confusion during maintenance.

### 4. Connect Ethernet

1. Attach USB-C hub to Arduino Uno Q
2. Run Cat6 Ethernet cable to router
3. Secure cable with strain relief

### 5. Power Up

1. Connect 5V 3A power supply
2. Observe startup LED flash (200ms)
3. Check serial output for boot messages

## Testing & Calibration

### Initial Calibration

**CRITICAL**: Calibrate in a clean, fire-free environment.

```bash
# Connect via serial monitor (115200 baud)
# Send calibration command
{"type":"calibrate"}
```

Wait 20 seconds for baseline establishment.

### Self-Test Procedure

1. **UV Sensor Test**: Read baseline (should be 30-70 ADC units in indoor lighting)
2. **Gas Sensor Test**: VOC should be 50-200 ppb in clean air
3. **Camera Test**: Verify image capture via dashboard
4. **Alarm Test**: Trigger via web dashboard

### Weekly Maintenance

- Clean camera lens with microfiber cloth
- Verify Ethernet connection is secure
- Test alarm sound
- Review system logs

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| No serial output | USB not connected | Check USB cable |
| BME688 not found | Wrong voltage / I2C address | Verify 3.3V, check address (0x77) |
| UV always high | Sensor facing light | Reposition away from direct lighting |
| Camera no image | USB cable loose | Reconnect USB cable, check device ID |
| No Ethernet | Hub not powered | Check USB-C Power Delivery |

## Safety Certifications

> [!CAUTION]
> This is a **prototype device**. For production deployment:
> - UL/ETL fire alarm certification required
> - Local building codes must be followed
> - Professional installation recommended
> - Does NOT replace code-mandated smoke detectors

## Placement Guidelines

**Optimal Locations**:
- Near ceiling (heat rises)
- Central hallway with visibility to multiple rooms
- Away from HVAC vents (prevents false readings)
- Within 50 feet of router (for Ethernet)

**Avoid**:
- Kitchens (cooking fumes cause false alarms)
- Bathrooms (humidity affects sensors)
- Direct sunlight (UV interference)

---

**Questions?** Refer to [API Reference](api-reference.md) or check the [Deployment Guide](deployment-guide.md).
