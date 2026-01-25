/**
 * BME688 Gas Sensor Header
 */

#ifndef GAS_SENSOR_H
#define GAS_SENSOR_H

#include <Arduino.h>
#include "config.h"

// Gas reading structure
struct GasReading {
    uint32_t voc_resistance;  // Raw resistance in Ohms
    uint16_t voc_ppb;         // VOC concentration in ppb
    float temperature;         // Temperature in °C
    float humidity;           // Relative humidity in %
    float pressure;           // Atmospheric pressure in hPa
    bool fault;               // Sensor fault flag
};

// Function prototypes
bool gas_init();
void gas_calibrate();
bool gas_read(GasReading* reading);
SensorStatus gas_get_status();
bool gas_detect_fire();
uint16_t gas_get_baseline();
bool gas_needs_calibration();
bool gas_self_test();

#endif // GAS_SENSOR_H
