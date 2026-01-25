// Sentin-AI Dashboard JavaScript
// Real-time sensor monitoring via WebSocket

let ws = null;
let reconnectInterval = null;

// Initialize WebSocket connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('✓ WebSocket connected');
        clearInterval(reconnectInterval);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDashboard(data);
    };

    ws.onclose = () => {
        console.log('⚠ WebSocket disconnected. Reconnecting...');
        reconnectInterval = setInterval(connectWebSocket, 5000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Update dashboard with new data
function updateDashboard(data) {
    // Update system status
    const statusBadge = document.getElementById('status-badge');
    statusBadge.textContent = data.status.toUpperCase();
    statusBadge.className = 'status-badge';

    if (data.status === 'alarm') {
        statusBadge.classList.add('alarm');
    } else if (data.status === 'alert') {
        statusBadge.classList.add('alert');
    }

    // Update uptime
    const hours = Math.floor(data.uptime_seconds / 3600);
    const minutes = Math.floor((data.uptime_seconds % 3600) / 60);
    const seconds = data.uptime_seconds % 60;
    document.getElementById('uptime').textContent =
        `${hours}h ${minutes}m ${seconds}s`;

    // Update sensors
    updateSensor('uv', data.sensors.uv);
    updateSensor('voc', data.sensors.voc);
    updateSensor('temp', data.sensors.temperature);
    updateSensor('humidity', data.sensors.humidity);

    // Update AI status
    document.getElementById('flame-status').textContent =
        data.ai.flame_detected ? '🔥 DETECTED' : 'Clear';
    document.getElementById('flame-status').style.color =
        data.ai.flame_detected ? 'var(--danger-color)' : 'var(--success-color)';

    document.getElementById('confidence').textContent =
        `${(data.ai.confidence * 100).toFixed(1)}%`;
    document.getElementById('inference-time').textContent =
        `${data.ai.last_inference_ms.toFixed(1)} ms`;
}

// Update individual sensor display
function updateSensor(sensorId, sensorData) {
    const valueElement = document.getElementById(`${sensorId}-value`);
    const statusElement = document.getElementById(`${sensorId}-status`);

    if (valueElement) {
        valueElement.textContent = sensorData.value.toFixed(1);
    }

    if (statusElement) {
        statusElement.className = 'sensor-status';

        if (sensorData.status === 'WARNING') {
            statusElement.classList.add('warning');
        } else if (sensorData.status === 'CRITICAL') {
            statusElement.classList.add('critical');
        }
    }
}

// Test alarm function
async function testAlarm() {
    const confirmed = confirm('Trigger alarm test? This will sound the piezo and test alert channels.');

    if (!confirmed) return;

    try {
        const response = await fetch('/api/test_alarm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            alert('✓ Alarm test triggered successfully');
        } else {
            alert('✗ Alarm test failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('✗ Failed to trigger alarm test');
    }
}

// Calibrate sensors
async function calibrateSensors() {
    const confirmed = confirm('Calibrate sensors? Ensure system is in a clean environment.');

    if (!confirmed) return;

    try {
        const response = await fetch('/api/calibrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            alert('✓ Sensor calibration started');
        } else {
            alert('✗ Calibration failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('✗ Failed to start calibration');
    }
}

// View alerts
async function viewAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();

        const alertsSection = document.getElementById('alerts-section');
        const alertsList = document.getElementById('alerts-list');

        if (data.alerts.length === 0) {
            alertsList.innerHTML = '<p class="no-alerts">No alerts recorded</p>';
        } else {
            let html = '';
            data.alerts.reverse().forEach(alert => {
                html += `
                    <div class="alert-item">
                        <strong>${alert.alert_type}</strong> - ${alert.timestamp}<br>
                        Channels: ${Object.keys(alert.channels).join(', ')}
                    </div>
                `;
            });
            alertsList.innerHTML = html;
        }

        alertsSection.style.display = 'block';
    } catch (error) {
        console.error('Error loading alerts:', error);
        alert('✗ Failed to load alerts');
    }
}

// Initialize on page load
window.addEventListener('load', () => {
    console.log('Sentin-AI Dashboard Initializing...');
    connectWebSocket();
});
