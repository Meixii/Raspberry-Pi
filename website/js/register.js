// QR Scanner instance
let qrScanner = null;

// Initialize registration page
document.addEventListener('DOMContentLoaded', () => {
    // Initialize timezone select
    populateTimezones();
    
    // Add event listeners
    document.getElementById('startScan').addEventListener('click', toggleQRScanner);
    document.getElementById('submitDeviceId').addEventListener('click', handleManualDeviceId);
    document.getElementById('deviceSetupForm').addEventListener('submit', handleDeviceSetup);
});

// Populate timezone select with options
function populateTimezones() {
    const select = document.getElementById('timezone');
    moment.tz.names().forEach(tz => {
        const option = document.createElement('option');
        option.value = tz;
        option.textContent = tz;
        select.appendChild(option);
    });
    
    // Set default timezone based on browser
    const defaultTimezone = moment.tz.guess();
    select.value = defaultTimezone;
}

// Toggle QR Scanner
async function toggleQRScanner() {
    const scannerContainer = document.getElementById('scanner-container');
    const startScanBtn = document.getElementById('startScan');
    
    if (scannerContainer.classList.contains('hidden')) {
        // Start scanner
        scannerContainer.classList.remove('hidden');
        startScanBtn.innerHTML = '<i class="material-icons">stop</i> Stop Scanner';
        
        try {
            qrScanner = new QrScanner(
                document.getElementById('qr-video'),
                result => handleQRResult(result),
                {
                    highlightScanRegion: true,
                    highlightCodeOutline: true,
                }
            );
            await qrScanner.start();
        } catch (error) {
            console.error('QR Scanner error:', error);
            showNotification('Error starting QR scanner. Please try manual entry.', 'error');
        }
    } else {
        // Stop scanner
        stopScanner();
    }
}

// Stop QR Scanner
function stopScanner() {
    if (qrScanner) {
        qrScanner.stop();
        qrScanner.destroy();
        qrScanner = null;
    }
    
    document.getElementById('scanner-container').classList.add('hidden');
    document.getElementById('startScan').innerHTML = '<i class="material-icons">qr_code_scanner</i> Start QR Scanner';
}

// Handle QR scan result
function handleQRResult(result) {
    stopScanner();
    connectDevice(result);
}

// Handle manual device ID submission
function handleManualDeviceId() {
    const deviceId = document.getElementById('deviceId').value.trim();
    if (!deviceId) {
        showNotification('Please enter a device ID', 'error');
        return;
    }
    connectDevice(deviceId);
}

// Connect to device
async function connectDevice(deviceId) {
    try {
        const response = await fetch(`${API_BASE_URL}/device/connect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ device_id: deviceId })
        });
        
        const data = await response.json();
        if (data.success) {
            // Store device ID for setup
            localStorage.setItem('registering_device_id', deviceId);
            // Move to setup step
            showStep(2);
        } else {
            showNotification(data.message || 'Failed to connect to device', 'error');
        }
    } catch (error) {
        console.error('Device connection error:', error);
        showNotification('Error connecting to device. Please try again.', 'error');
    }
}

// Handle device setup form submission
async function handleDeviceSetup(event) {
    event.preventDefault();
    
    const deviceId = localStorage.getItem('registering_device_id');
    if (!deviceId) {
        showNotification('Device ID not found. Please start over.', 'error');
        showStep(1);
        return;
    }
    
    const setupData = {
        device_id: deviceId,
        name: document.getElementById('deviceName').value,
        timezone: document.getElementById('timezone').value,
        location: document.getElementById('location').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/device/setup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(setupData)
        });
        
        const data = await response.json();
        if (data.success) {
            // Clear stored device ID
            localStorage.removeItem('registering_device_id');
            // Show success step
            showStep('success');
        } else {
            showNotification(data.message || 'Failed to setup device', 'error');
        }
    } catch (error) {
        console.error('Device setup error:', error);
        showNotification('Error setting up device. Please try again.', 'error');
    }
}

// Show step
function showStep(stepNumber) {
    document.querySelectorAll('.step').forEach(step => {
        step.classList.add('hidden');
    });
    document.getElementById(`step${stepNumber}`).classList.remove('hidden');
}

// Show notification
function showNotification(message, type = 'info') {
    alert(message); // For now, just using alert. You can enhance this later
} 