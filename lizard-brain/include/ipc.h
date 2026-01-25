/**
 * Inter-Processor Communication Header
 */

#ifndef IPC_H
#define IPC_H

#include <Arduino.h>
#include "config.h"

// Communication parameters
#define IPC_BUFFER_SIZE 512
#define IPC_TIMEOUT_MS 5000
#define IPC_HEARTBEAT_INTERVAL_MS 1000

// Function prototypes
void ipc_init();
void ipc_send_sensor_data(const SensorReadings* readings);
void ipc_send_alert(SystemState state, const char* reason);
void ipc_send_status(const SystemStatus* status);
void ipc_send_heartbeat();
void ipc_process_messages();
void ipc_handle_message(const char* message);
void ipc_wake_cortex();
bool ipc_cortex_alive();
uint8_t ipc_checksum(const char* data);

#endif // IPC_H
