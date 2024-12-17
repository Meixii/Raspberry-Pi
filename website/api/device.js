const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

// In-memory storage for device registration (should be replaced with database in production)
const pendingRegistrations = new Map();
const verificationCodes = new Map();
const registeredDevices = new Map();

// Generate a new device token
router.post('/generate-token', (req, res) => {
    try {
        const token = uuidv4();
        const verificationCode = crypto.randomInt(100000, 999999).toString();
        
        // Store the token and verification code
        pendingRegistrations.set(token, {
            timestamp: Date.now(),
            verified: false
        });
        verificationCodes.set(token, verificationCode);

        // Clean up old tokens (older than 1 hour)
        cleanupOldTokens();

        res.json({ token });
    } catch (error) {
        console.error('Error generating token:', error);
        res.status(500).json({ error: 'Failed to generate token' });
    }
});

// Verify the device code
router.post('/verify-code', (req, res) => {
    const { token, code } = req.body;

    if (!token || !code) {
        return res.status(400).json({ error: 'Token and code are required' });
    }

    try {
        const storedCode = verificationCodes.get(token);
        const registration = pendingRegistrations.get(token);

        if (!registration) {
            return res.status(404).json({ error: 'Invalid or expired token' });
        }

        if (code !== storedCode) {
            return res.status(400).json({ error: 'Invalid verification code' });
        }

        // Mark as verified
        registration.verified = true;
        pendingRegistrations.set(token, registration);

        res.json({ success: true });
    } catch (error) {
        console.error('Error verifying code:', error);
        res.status(500).json({ error: 'Failed to verify code' });
    }
});

// Complete device setup
router.post('/complete-setup', (req, res) => {
    const { token, deviceName, timezone, location } = req.body;

    if (!token || !deviceName || !timezone || !location) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        const registration = pendingRegistrations.get(token);

        if (!registration || !registration.verified) {
            return res.status(400).json({ error: 'Invalid or unverified token' });
        }

        // Create device record
        const deviceId = uuidv4();
        const device = {
            id: deviceId,
            name: deviceName,
            timezone,
            location,
            registeredAt: new Date().toISOString(),
            lastSeen: new Date().toISOString()
        };

        // Store device
        registeredDevices.set(deviceId, device);

        // Clean up registration data
        pendingRegistrations.delete(token);
        verificationCodes.delete(token);

        res.json({
            success: true,
            device: {
                id: deviceId,
                name: deviceName
            }
        });
    } catch (error) {
        console.error('Error completing setup:', error);
        res.status(500).json({ error: 'Failed to complete device setup' });
    }
});

// Get device information
router.get('/:deviceId', (req, res) => {
    const { deviceId } = req.params;

    try {
        const device = registeredDevices.get(deviceId);

        if (!device) {
            return res.status(404).json({ error: 'Device not found' });
        }

        res.json(device);
    } catch (error) {
        console.error('Error getting device info:', error);
        res.status(500).json({ error: 'Failed to get device information' });
    }
});

// Update device information
router.put('/:deviceId', (req, res) => {
    const { deviceId } = req.params;
    const updates = req.body;

    try {
        const device = registeredDevices.get(deviceId);

        if (!device) {
            return res.status(404).json({ error: 'Device not found' });
        }

        // Update device information
        const updatedDevice = {
            ...device,
            ...updates,
            lastSeen: new Date().toISOString()
        };

        registeredDevices.set(deviceId, updatedDevice);

        res.json(updatedDevice);
    } catch (error) {
        console.error('Error updating device:', error);
        res.status(500).json({ error: 'Failed to update device' });
    }
});

// Utility function to clean up old tokens
function cleanupOldTokens() {
    const oneHour = 60 * 60 * 1000; // 1 hour in milliseconds
    const now = Date.now();

    for (const [token, registration] of pendingRegistrations.entries()) {
        if (now - registration.timestamp > oneHour) {
            pendingRegistrations.delete(token);
            verificationCodes.delete(token);
        }
    }
}

module.exports = router; 