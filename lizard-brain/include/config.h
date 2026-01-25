/**
 * Sentin-AI Lizard Brain - Safety-Critical Fire Detection
 * 
 * STM32 Microcontroller Core
 * Real-time sensor polling with hardware watchdog
 * Cannot fail. Cannot sleep. Always protects.
 */

#ifndef SENTIN_CONFIG_H
#define SENTIN_CONFIG_H

#include <Arduino.h>

// ============== HARDWARE PIN CONFIGURATION ==============

// UV Sensor (Analog Input)
#define PIN_UV_SENSOR A0

// Gas Sensor (I2C)
#define PIN_GAS_SDA 4
#define PIN_GAS_SCL 5
#define BME688_I2C_ADDR 0x77

// Alarm Output (Hardware Direct - Bypasses Software)
#define PIN_ALARM_PIEZO 9
#define PIN_ALARM_LED 13

// Inter-Processor Communication (UART to Snapdragon)
#define PIN_IPC_TX 1
#define PIN_IPC_RX 0
#define IPC_BAUD_RATE 115200

// Wake Signal to Cortex
#define PIN_CORTEX_WAKE 8

// ============== SAFETY THRESHOLDS ==============

// UV Sensor Thresholds (0-1023 ADC range)
#define UV_BASELINE 50
#define UV_FIRE_THRESHOLD 150
#define UV_CRITICAL_THRESHOLD 300

// Gas Sensor Thresholds (VOC in ppb)
#define VOC_BASELINE 100
#define VOC_FIRE_THRESHOLD 500
#define VOC_CRITICAL_THRESHOLD 1000

// Timing Constants
#define SENSOR_POLL_INTERVAL_MS 50     // 20Hz polling rate
#define WATCHDOG_TIMEOUT_MS 200        // Watchdog must be fed every 200ms
#define ALARM_PULSE_WIDTH_MS 100       // Piezo pulse duration

// ============== SYSTEM STATES ==============

enum SystemState {
    STATE_NORMAL = 0,
    STATE_ALERT = 1,      // Potential hazard detected
    STATE_ALARM = 2,      // Fire confirmed - ALARM!
    STATE_TEST = 3        // Self-test mode
};

enum SensorStatus {
    SENSOR_OK = 0,
    SENSOR_WARNING = 1,
    SENSOR_CRITICAL = 2,
    SENSOR_FAULT = 3
};

// ============== DATA STRUCTURES ==============

struct SensorReadings {
    uint16_t uv_value;
    uint16_t voc_ppb;
    float temperature;
    float humidity;
    uint32_t timestamp_ms;
};

struct SystemStatus {
    SystemState state;
    SensorStatus uv_status;
    SensorStatus gas_status;
    bool cortex_awake;
    uint32_t uptime_seconds;
};

// ============== TIMING ==============

// Calculate ticks for real-time scheduling
#define MS_TO_TICKS(ms) ((ms) / SENSOR_POLL_INTERVAL_MS)

#endif // SENTIN_CONFIG_H
