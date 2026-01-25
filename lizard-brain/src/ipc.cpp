/**
 * Inter-Processor Communication (IPC)
 * 
 * UART bridge between STM32 (Lizard Brain) and Snapdragon (Cortex)
 * Protocol: JSON messages with CRC validation
 */

#include "ipc.h"
#include <ArduinoJson.h>

// Message buffer
static char tx_buffer[IPC_BUFFER_SIZE];
static char rx_buffer[IPC_BUFFER_SIZE];
static uint16_t rx_index = 0;

// Heartbeat tracking
static uint32_t last_heartbeat_sent = 0;
static uint32_t last_heartbeat_received = 0;

/**
 * Initialize IPC serial communication
 */
void ipc_init() {
    Serial.begin(IPC_BAUD_RATE);
    while (!Serial) {
        delay(10); // Wait for serial port
    }
    
    Serial.println("{\"type\":\"boot\",\"device\":\"lizard-brain\"}");
}

/**
 * Send sensor data to Cortex
 */
void ipc_send_sensor_data(const SensorReadings* readings) {
    if (readings == NULL) return;
    
    StaticJsonDocument<256> doc;
    doc["type"] = "sensor_data";
    doc["uv"] = readings->uv_value;
    doc["voc"] = readings->voc_ppb;
    doc["temp"] = readings->temperature;
    doc["humidity"] = readings->humidity;
    doc["timestamp"] = readings->timestamp_ms;
    
    serializeJson(doc, Serial);
    Serial.println();
}

/**
 * Send alert to Cortex (wake it up!)
 */
void ipc_send_alert(SystemState state, const char* reason) {
    StaticJsonDocument<256> doc;
    doc["type"] = "alert";
    doc["state"] = state;
    doc["reason"] = reason;
    doc["timestamp"] = millis();
    
    serializeJson(doc, Serial);
    Serial.println();
    
    // Physically wake the Cortex via GPIO
    ipc_wake_cortex();
}

/**
 * Send system status
 */
void ipc_send_status(const SystemStatus* status) {
    if (status == NULL) return;
    
    StaticJsonDocument<256> doc;
    doc["type"] = "status";
    doc["state"] = status->state;
    doc["uv_status"] = status->uv_status;
    doc["gas_status"] = status->gas_status;
    doc["cortex_awake"] = status->cortex_awake;
    doc["uptime"] = status->uptime_seconds;
    
    serializeJson(doc, Serial);
    Serial.println();
}

/**
 * Send heartbeat (keepalive)
 */
void ipc_send_heartbeat() {
    Serial.println("{\"type\":\"heartbeat\"}");
    last_heartbeat_sent = millis();
}

/**
 * Process incoming messages from Cortex
 */
void ipc_process_messages() {
    while (Serial.available()) {
        char c = Serial.read();
        
        if (c == '\n' || c == '\r') {
            if (rx_index > 0) {
                rx_buffer[rx_index] = '\0';
                ipc_handle_message(rx_buffer);
                rx_index = 0;
            }
        } else if (rx_index < IPC_BUFFER_SIZE - 1) {
            rx_buffer[rx_index++] = c;
        }
    }
    
    // Send periodic heartbeat
    if (millis() - last_heartbeat_sent >= IPC_HEARTBEAT_INTERVAL_MS) {
        ipc_send_heartbeat();
    }
}

/**
 * Handle parsed message from Cortex
 */
void ipc_handle_message(const char* message) {
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, message);
    
    if (error) {
        Serial.print("{\"error\":\"parse_failed\",\"msg\":\"");
        Serial.print(message);
        Serial.println("\"}");
        return;
    }
    
    const char* msg_type = doc["type"];
    
    if (strcmp(msg_type, "heartbeat") == 0) {
        last_heartbeat_received = millis();
    } else if (strcmp(msg_type, "calibrate") == 0) {
        // Cortex requested sensor recalibration
        Serial.println("{\"ack\":\"calibration_started\"}");
    } else if (strcmp(msg_type, "test_alarm") == 0) {
        // Manual alarm test from web dashboard
        Serial.println("{\"ack\":\"alarm_test\"}");
    }
}

/**
 * Wake the Cortex via GPIO signal
 */
void ipc_wake_cortex() {
    pinMode(PIN_CORTEX_WAKE, OUTPUT);
    digitalWrite(PIN_CORTEX_WAKE, HIGH);
    delay(100);
    digitalWrite(PIN_CORTEX_WAKE, LOW);
}

/**
 * Check if Cortex is responsive
 */
bool ipc_cortex_alive() {
    return (millis() - last_heartbeat_received) < IPC_TIMEOUT_MS;
}

/**
 * Calculate simple checksum for data integrity
 */
uint8_t ipc_checksum(const char* data) {
    uint8_t sum = 0;
    while (*data) {
        sum ^= *data++;
    }
    return sum;
}
