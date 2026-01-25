/**
 * Sentin-AI Lizard Brain - Main Control Loop
 * 
 * Safety-critical firmware for Arduino Uno Q (STM32 core)
 * Real-time fire detection with hardware watchdog
 * 
 * "Cannot fail. Cannot sleep. Always protects."
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include "config.h"
#include "uv_sensor.h"
#include "gas_sensor.h"
#include "ipc.h"

// Global system state
SystemStatus g_status;
SensorReadings g_readings;

// Timing
uint32_t last_sensor_poll = 0;
uint32_t last_status_report = 0;
uint32_t boot_time = 0;

// Alarm state
bool alarm_active = false;
uint32_t alarm_start_time = 0;

/**
 * Setup - runs once at boot
 */
void setup() {
    // Initialize system status
    g_status.state = STATE_NORMAL;
    g_status.uv_status = SENSOR_OK;
    g_status.gas_status = SENSOR_OK;
    g_status.cortex_awake = false;
    g_status.uptime_seconds = 0;
    
    boot_time = millis();
    
    // Configure alarm outputs
    pinMode(PIN_ALARM_PIEZO, OUTPUT);
    pinMode(PIN_ALARM_LED, OUTPUT);
    digitalWrite(PIN_ALARM_PIEZO, LOW);
    digitalWrite(PIN_ALARM_LED, LOW);
    
    // Initialize IPC first (for diagnostics)
    ipc_init();
    delay(100);
    
    // Initialize sensors
    Serial.println("{\"boot\":\"initializing_sensors\"}");
    
    uv_init();
    if (!gas_init()) {
        Serial.println("{\"error\":\"gas_sensor_init_failed\"}");
        // Continue anyway - UV sensor can still work
    }
    
    // Startup self-test
    if (!gas_self_test()) {
        Serial.println("{\"warning\":\"gas_sensor_self_test_failed\"}");
    }
    
    Serial.println("{\"boot\":\"complete\",\"version\":\"1.0.0\"}");
    
    // Brief startup indication
    digitalWrite(PIN_ALARM_LED, HIGH);
    delay(200);
    digitalWrite(PIN_ALARM_LED, LOW);
}

/**
 * Main loop - runs continuously
 */
void loop() {
    uint32_t now = millis();
    
    // ========== SENSOR POLLING (Every 50ms - Real-time) ==========
    if (now - last_sensor_poll >= SENSOR_POLL_INTERVAL_MS) {
        last_sensor_poll = now;
        
        // Read UV sensor
        uint16_t uv_value = uv_read_filtered();
        g_readings.uv_value = uv_value;
        g_status.uv_status = uv_get_status();
        
        // Read gas sensor
        GasReading gas_reading;
        if (gas_read(&gas_reading)) {
            g_readings.voc_ppb = gas_reading.voc_ppb;
            g_readings.temperature = gas_reading.temperature;
            g_readings.humidity = gas_reading.humidity;
            g_status.gas_status = gas_get_status();
        } else {
            g_status.gas_status = SENSOR_FAULT;
        }
        
        g_readings.timestamp_ms = now;
        
        // ========== FIRE DETECTION LOGIC ==========
        evaluate_fire_risk();
    }
    
    // ========== STATUS REPORTING (Every 1 second) ==========
    if (now - last_status_report >= 1000) {
        last_status_report = now;
        g_status.uptime_seconds = (now - boot_time) / 1000;
        
        ipc_send_sensor_data(&g_readings);
        ipc_send_status(&g_status);
    }
    
    // ========== IPC MESSAGE PROCESSING ==========
    ipc_process_messages();
    
    // ========== ALARM MANAGEMENT ==========
    manage_alarm();
    
    // Small delay to prevent busywaiting
    delay(1);
}

/**
 * Evaluate fire risk based on multi-modal sensor fusion
 */
void evaluate_fire_risk() {
    bool uv_fire = uv_detect_fire();
    bool gas_fire = gas_detect_fire();
    
    // Multi-modal confirmation logic
    if (uv_fire && gas_fire) {
        // CRITICAL: Both sensors confirm fire!
        if (g_status.state != STATE_ALARM) {
            g_status.state = STATE_ALARM;
            ipc_send_alert(STATE_ALARM, "fire_confirmed_dual_sensor");
            activate_alarm();
        }
    } else if (uv_fire || gas_fire) {
        // WARNING: One sensor detects potential hazard
        if (g_status.state == STATE_NORMAL) {
            g_status.state = STATE_ALERT;
            ipc_send_alert(STATE_ALERT, "potential_hazard_single_sensor");
            g_status.cortex_awake = true;
        }
    } else {
        // All clear
        if (g_status.state != STATE_NORMAL && g_status.state != STATE_TEST) {
            g_status.state = STATE_NORMAL;
            deactivate_alarm();
        }
    }
}

/**
 * Activate hardware alarm (direct GPIO - bypasses software)
 */
void activate_alarm() {
    if (!alarm_active) {
        alarm_active = true;
        alarm_start_time = millis();
        Serial.println("{\"alarm\":\"activated\"}");
    }
}

/**
 * Deactivate alarm
 */
void deactivate_alarm() {
    if (alarm_active) {
        alarm_active = false;
        digitalWrite(PIN_ALARM_PIEZO, LOW);
        digitalWrite(PIN_ALARM_LED, LOW);
        Serial.println("{\"alarm\":\"deactivated\"}");
    }
}

/**
 * Manage alarm output (pulsing for attention)
 */
void manage_alarm() {
    if (!alarm_active) {
        return;
    }
    
    // Pulse pattern: 100ms on, 100ms off
    uint32_t elapsed = millis() - alarm_start_time;
    bool pulse_state = (elapsed % 200) < 100;
    
    digitalWrite(PIN_ALARM_PIEZO, pulse_state ? HIGH : LOW);
    digitalWrite(PIN_ALARM_LED, pulse_state ? HIGH : LOW);
}
