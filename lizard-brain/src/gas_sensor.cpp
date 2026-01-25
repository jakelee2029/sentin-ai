/**
 * BME688 AI Gas Sensor Module
 * 
 * Communicates with Bosch BME688 via I2C
 * Detects VOC signatures of combustion materials
 */

#include "gas_sensor.h"
#include <Wire.h>
#include <Adafruit_BME680.h>

// BME688 sensor object
static Adafruit_BME680 bme;
static bool sensor_initialized = false;

// Baseline tracking for anomaly detection
static uint16_t voc_baseline = VOC_BASELINE;
static uint32_t last_calibration_time = 0;

/**
 * Initialize BME688 gas sensor
 */
bool gas_init() {
    Wire.begin(PIN_GAS_SDA, PIN_GAS_SCL);
    
    if (!bme.begin(BME688_I2C_ADDR)) {
        Serial.println("ERROR: BME688 not found!");
        return false;
    }
    
    // Configure sensor oversampling and filter
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150); // 320°C for 150ms (optimized for VOC detection)
    
    sensor_initialized = true;
    
    // Initial calibration
    delay(100);
    gas_calibrate();
    
    return true;
}

/**
 * Calibrate gas sensor baseline
 */
void gas_calibrate() {
    if (!sensor_initialized) return;
    
    uint32_t sum = 0;
    uint8_t samples = 20;
    
    for (uint8_t i = 0; i < samples; i++) {
        if (bme.performReading()) {
            sum += bme.gas_resistance / 1000; // Convert to kOhm
        }
        delay(100);
    }
    
    voc_baseline = sum / samples;
    last_calibration_time = millis();
}

/**
 * Read gas sensor and populate readings structure
 */
bool gas_read(GasReading* reading) {
    if (!sensor_initialized || reading == NULL) {
        return false;
    }
    
    if (!bme.performReading()) {
        reading->fault = true;
        return false;
    }
    
    reading->voc_resistance = bme.gas_resistance;
    reading->temperature = bme.temperature;
    reading->humidity = bme.humidity;
    reading->pressure = bme.pressure / 100.0; // Convert to hPa
    reading->fault = false;
    
    // Calculate VOC equivalent (simplified IAQ calculation)
    // Lower resistance = higher VOC concentration
    float resistance_ratio = (float)voc_baseline / (bme.gas_resistance / 1000.0);
    reading->voc_ppb = VOC_BASELINE * resistance_ratio;
    
    return true;
}

/**
 * Determine sensor status based on gas reading
 */
SensorStatus gas_get_status() {
    GasReading reading;
    
    if (!gas_read(&reading)) {
        return SENSOR_FAULT;
    }
    
    if (reading.voc_ppb >= VOC_CRITICAL_THRESHOLD) {
        return SENSOR_CRITICAL;
    } else if (reading.voc_ppb >= VOC_FIRE_THRESHOLD) {
        return SENSOR_WARNING;
    } else {
        return SENSOR_OK;
    }
}

/**
 * Check if gas sensor detects fire signature
 */
bool gas_detect_fire() {
    return gas_get_status() >= SENSOR_WARNING;
}

/**
 * Get baseline value for diagnostics
 */
uint16_t gas_get_baseline() {
    return voc_baseline;
}

/**
 * Check if sensor needs recalibration (every 24 hours)
 */
bool gas_needs_calibration() {
    return (millis() - last_calibration_time) > (24UL * 60 * 60 * 1000);
}

/**
 * Self-test routine
 */
bool gas_self_test() {
    GasReading reading;
    
    if (!gas_read(&reading)) {
        return false;
    }
    
    // Basic sanity checks
    bool temp_ok = (reading.temperature > -40 && reading.temperature < 85);
    bool humidity_ok = (reading.humidity >= 0 && reading.humidity <= 100);
    bool pressure_ok = (reading.pressure > 300 && reading.pressure < 1100);
    
    return temp_ok && humidity_ok && pressure_ok && !reading.fault;
}
