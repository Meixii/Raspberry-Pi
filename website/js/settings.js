// Settings state
let settings = {
    timeFormat: '24h',
    dateFormat: 'iso',
    temperatureUnit: 'C',
    theme: 'dark',
    defaultSound: null,
    rgbEnabled: true,
    rgbPattern: 'default',
    volume: 70,
    snoozeDuration: 5,
    gradualWakeDuration: 15,
    calendarSyncInterval: 5
};

// Initialize settings component
function initializeSettings() {
    // Load settings
    loadSettings();
    
    // Add event listeners
    addSettingsEventListeners();
}

// Load settings from server
function loadSettings() {
    fetch(`${API_BASE_URL}/settings`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            settings = { ...settings, ...data.settings };
            applySettings();
        }
    })
    .catch(error => {
        console.error('Error loading settings:', error);
        showNotification('Error loading settings', 'error');
    });
}

// Apply settings to UI
function applySettings() {
    // Time format
    document.getElementById('time-format').value = settings.timeFormat;
    
    // Date format
    document.getElementById('date-format').value = settings.dateFormat;
    
    // Temperature unit
    document.getElementById('temp-unit').value = settings.temperatureUnit;
    
    // Theme
    document.body.className = `theme-${settings.theme}`;
    document.querySelectorAll('.theme-card').forEach(card => {
        card.classList.toggle('active', card.dataset.theme === settings.theme);
    });
    
    // Update app state
    app.state.settings = settings;
}

// Save settings to server
function saveSettings(newSettings) {
    fetch(`${API_BASE_URL}/settings`, {
        method: 'POST',
        headers: window.defaultHeaders,
        body: JSON.stringify(newSettings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            settings = { ...settings, ...newSettings };
            applySettings();
            showNotification('Settings saved successfully', 'success');
        } else {
            showNotification('Error saving settings', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showNotification('Error saving settings', 'error');
    });
}

// Handle setting changes
function handleSettingChange(setting, value) {
    const newSettings = { [setting]: value };
    
    // Special handling for certain settings
    switch (setting) {
        case 'theme':
            document.body.className = `theme-${value}`;
            break;
            
        case 'timeFormat':
            // Update all time displays
            document.querySelectorAll('.time-display').forEach(el => {
                const time = new Date(el.dataset.time);
                el.textContent = app.formatTime(time);
            });
            break;
            
        case 'dateFormat':
            // Update all date displays
            document.querySelectorAll('.date-display').forEach(el => {
                const date = new Date(el.dataset.date);
                el.textContent = app.formatDate(date);
            });
            break;
            
        case 'temperatureUnit':
            // Update all temperature displays
            document.querySelectorAll('.temp-display').forEach(el => {
                const temp = parseFloat(el.dataset.temp);
                el.textContent = app.formatTemperature(temp);
            });
            break;
    }
    
    // Save to server
    saveSettings(newSettings);
}

// Add settings event listeners
function addSettingsEventListeners() {
    // Time format
    document.getElementById('time-format').addEventListener('change', (e) => {
        handleSettingChange('timeFormat', e.target.value);
    });
    
    // Date format
    document.getElementById('date-format').addEventListener('change', (e) => {
        handleSettingChange('dateFormat', e.target.value);
    });
    
    // Temperature unit
    document.getElementById('temp-unit').addEventListener('change', (e) => {
        handleSettingChange('temperatureUnit', e.target.value);
    });
    
    // Theme selection
    document.querySelectorAll('.theme-card').forEach(card => {
        card.addEventListener('click', () => {
            handleSettingChange('theme', card.dataset.theme);
        });
    });
}

// Export settings
function exportSettings() {
    const dataStr = JSON.stringify(settings, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportLink = document.createElement('a');
    exportLink.setAttribute('href', dataUri);
    exportLink.setAttribute('download', 'smart_alarm_settings.json');
    exportLink.click();
}

// Import settings
function importSettings(file) {
    const reader = new FileReader();
    
    reader.onload = (e) => {
        try {
            const importedSettings = JSON.parse(e.target.result);
            saveSettings(importedSettings);
        } catch (error) {
            console.error('Error parsing settings file:', error);
            showNotification('Invalid settings file', 'error');
        }
    };
    
    reader.readAsText(file);
}

// Reset settings to defaults
function resetSettings() {
    if (!confirm('Are you sure you want to reset all settings to default values?')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/settings/reset`, {
        method: 'POST',
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            settings = { ...settings, ...data.settings };
            applySettings();
            showNotification('Settings reset to defaults', 'success');
        } else {
            showNotification('Error resetting settings', 'error');
        }
    })
    .catch(error => {
        console.error('Error resetting settings:', error);
        showNotification('Error resetting settings', 'error');
    });
}

// Refresh settings
function refreshSettings() {
    loadSettings();
} 