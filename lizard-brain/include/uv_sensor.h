/**
 * UV Flame Sensor Header
 */

#ifndef UV_SENSOR_H
#define UV_SENSOR_H

#include <Arduino.h>
#include "config.h"

// Filter parameters
#define UV_FILTER_SIZE 5  // Median filter window

// Function prototypes
void uv_init();
void uv_calibrate();
uint16_t uv_read_raw();
uint16_t uv_read_filtered();
SensorStatus uv_get_status();
bool uv_detect_fire();
uint16_t uv_get_baseline();
bool uv_is_calibrated();

#endif // UV_SENSOR_H
