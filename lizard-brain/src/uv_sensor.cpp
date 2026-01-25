/**
 * UV Flame Sensor Module
 * 
 * Detects UV-C radiation (185-260nm) characteristic of open flames.
 * Filters out fluorescent lighting and solar radiation.
 */

#include "uv_sensor.h"
#include "config.h"

// Static variables for filtering
static uint16_t rolling_baseline = UV_BASELINE;
static uint16_t readings_buffer[UV_FILTER_SIZE];
static uint8_t buffer_index = 0;
static bool calibrated = false;

/**
 * Initialize UV sensor
 */
void uv_init() {
    pinMode(PIN_UV_SENSOR, INPUT);
    
    // Initialize rolling buffer
    for (uint8_t i = 0; i < UV_FILTER_SIZE; i++) {
        readings_buffer[i] = UV_BASELINE;
    }
    
    // Calibration phase - establish baseline over 2 seconds
    delay(100);
    uv_calibrate();
}

/**
 * Calibrate UV baseline (run at startup in safe environment)
 */
void uv_calibrate() {
    uint32_t sum = 0;
    uint16_t samples = 40; // 2 seconds at 50ms interval
    
    for (uint16_t i = 0; i < samples; i++) {
        sum += analogRead(PIN_UV_SENSOR);
        delay(SENSOR_POLL_INTERVAL_MS);
    }
    
    rolling_baseline = sum / samples;
    calibrated = true;
}

/**
 * Read UV sensor with median filtering to reject noise
 */
uint16_t uv_read_raw() {
    return analogRead(PIN_UV_SENSOR);
}

/**
 * Read filtered UV value
 */
uint16_t uv_read_filtered() {
    // Add new reading to circular buffer
    readings_buffer[buffer_index] = uv_read_raw();
    buffer_index = (buffer_index + 1) % UV_FILTER_SIZE;
    
    // Calculate median (simple bubble sort for small array)
    uint16_t sorted[UV_FILTER_SIZE];
    memcpy(sorted, readings_buffer, sizeof(readings_buffer));
    
    for (uint8_t i = 0; i < UV_FILTER_SIZE - 1; i++) {
        for (uint8_t j = i + 1; j < UV_FILTER_SIZE; j++) {
            if (sorted[i] > sorted[j]) {
                uint16_t temp = sorted[i];
                sorted[i] = sorted[j];
                sorted[j] = temp;
            }
        }
    }
    
    // Return median value
    return sorted[UV_FILTER_SIZE / 2];
}

/**
 * Determine sensor status based on UV reading
 */
SensorStatus uv_get_status() {
    uint16_t reading = uv_read_filtered();
    
    if (reading >= UV_CRITICAL_THRESHOLD) {
        return SENSOR_CRITICAL;
    } else if (reading >= UV_FIRE_THRESHOLD) {
        return SENSOR_WARNING;
    } else {
        return SENSOR_OK;
    }
}

/**
 * Check if UV sensor detects fire signature
 */
bool uv_detect_fire() {
    return uv_get_status() >= SENSOR_WARNING;
}

/**
 * Get baseline value for diagnostics
 */
uint16_t uv_get_baseline() {
    return rolling_baseline;
}

/**
 * Check if sensor is calibrated
 */
bool uv_is_calibrated() {
    return calibrated;
}
