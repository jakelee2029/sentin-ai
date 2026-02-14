# Sentin-AI 🔥
## Next-Generation Fire Verification System

**Project Ridgewood** - Preventing tragedy through edge AI sensor fusion.

> **Support the Ridgewood Relief Fund**: [GoFundMe Campaign](https://www.gofundme.com/f/rebuilding-ridgewood-support-4-families-after-fire)

### Mission

On January 6, 2026, many families in Ridgewood lost their homes to a devastating fire. Sentin-AI is our response: an advanced fire safety node that uses Artificial Intelligence to detect fires faster and more accurately than standard smoke detectors.

### The Innovation: Multi-Modal Sensor Fusion

Sentin-AI mimics human senses to verify fires before alerting:

- **👁️ Vision (The Eyes)**: CNN identifies flame shapes and movement
- **👃 Olfaction (The Nose)**: AI gas sensing detects burning materials' chemical signatures  
- **⚡ Spectral Analysis (The Reflex)**: UV sensors detect fire-specific radiation

### Dual-Brain Architecture

**Lizard Brain (STM32)**: Safety-critical real-time sensor polling (50ms cycle). Never sleeps. Always triggers alarm.

**Cortex (Snapdragon)**: AI processing awakened by hazard detection. Verifies fire via camera and sends alerts with photographic evidence.

### Hardware Requirements

- **Arduino Uno Q** - Hybrid board with STM32 + Snapdragon cores
- **Waveshare BME688** - AI gas sensor trained on fire VOC signatures
- **Logitech Brio 101 Full HD 1080p USB Camera** - Visual flame verification
- **UV Sensor** - Fire radiation detection
- **StarTech 3-Port USB-C Hub with Gigabit Ethernet** - Critical hardwired uplink

### Quick Start

#### 1. Install Dependencies

```bash
# Python dependencies (Cortex)
pip install -r requirements.txt

# PlatformIO for Arduino (Lizard Brain)
pip install platformio
```

#### 2. Configure System

Edit `integration/config.yaml` with your settings:
- Alert contact information
- Network configuration  
- Sensor calibration thresholds

#### 3. Upload Lizard Brain Firmware

```bash
cd lizard-brain
pio run --target upload
```

> **Note**: PlatformIO will automatically download and install all required libraries (ArduinoJson, Wire, Adafruit BME680, etc.) during the first build.

#### 4. Start Cortex AI System

```bash
cd cortex
python main.py
```

#### 5. Launch Web Dashboard

```bash
cd integration/dashboard
python app.py
```

Access at: `http://localhost:8080`

### Development Without Hardware

Use the simulator for testing:

```bash
python simulator/test_harness.py --scenario=all
```

### Project Structure

```
sentin-ai/
├── lizard-brain/      # STM32 safety-critical code (C++)
├── cortex/            # Snapdragon AI processing (Python)
├── integration/       # IPC bridge & web dashboard
├── simulator/         # Virtual hardware for testing
└── docs/              # Hardware setup & deployment guides
```

### Documentation

- [Hardware Setup Guide](docs/hardware-setup.md) - Wiring and assembly
- [Deployment Guide](docs/deployment-guide.md) - Installation procedures
- [API Reference](docs/api-reference.md) - System interfaces

### Impact & Support

This project demonstrates that edge AI can bring industrial-grade safety to residential homes for under $200.

**Community Action**: Development is tied to the [Ridgewood Fire Relief Fund](https://www.gofundme.com/f/rebuilding-ridgewood-support-4-families-after-fire) supporting displaced families.

### License

MIT License - Build upon this technology to protect your community.

---

*In memory of those who lost their homes. In service of those we can still save.*
