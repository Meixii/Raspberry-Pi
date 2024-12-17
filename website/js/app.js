// App state
const state = {
    currentPage: 'alarms',
    theme: localStorage.getItem('theme') || 'dark',
    settings: null
};

// API Base URL - Update this to your RPi's IP address
const API_BASE_URL = 'http://192.168.1.49:5000/api';

// Default headers for API requests
window.defaultHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
};

// Initialize app
function initializeApp() {
    // Load user data
    const userData = JSON.parse(localStorage.getItem('user'));
    if (userData) {
        document.getElementById('user-avatar').src = userData.picture || 'img/default-avatar.png';
        document.getElementById('user-name').textContent = userData.name;
    }
    
    // Initialize navigation
    initializeNavigation();
    
    // Apply saved theme
    applyTheme(state.theme);
    
    // Initialize components
    initializeAlarms();
    initializeCalendar();
    initializeWeather();
    initializeSounds();
    initializeLights();
    initializeSettings();
    
    // Add event listeners
    addEventListeners();
}

// Initialize navigation
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-links li');
    
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const page = link.dataset.page;
            changePage(page);
        });
    });

    // Add logout handler
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
}

// Change active page
function changePage(page) {
    // Update state
    state.currentPage = page;
    
    // Update navigation
    document.querySelectorAll('.nav-links li').forEach(link => {
        link.classList.toggle('active', link.dataset.page === page);
    });
    
    // Update visible page
    document.querySelectorAll('.page').forEach(pageElement => {
        pageElement.classList.toggle('active', pageElement.id === `${page}-page`);
    });
    
    // Refresh page content
    refreshPageContent(page);
}

// Handle logout
function handleLogout() {
    // Clear stored data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Redirect to auth page
    window.location.href = 'auth.html';
}

// Show notification
function showNotification(message, type = 'info') {
    alert(message); // For now, just using alert. You can enhance this later
}

// Add event listeners
function addEventListeners() {
    // Theme selection
    document.querySelectorAll('.theme-card').forEach(card => {
        card.addEventListener('click', () => {
            const theme = card.dataset.theme;
            applyTheme(theme);
        });
    });
    
    // Modal handlers
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        // Close modal when clicking outside
        modalContainer.addEventListener('click', (e) => {
            if (e.target === modalContainer) {
                modalContainer.classList.remove('active');
            }
        });

        // Add alarm button
        const addAlarmBtn = document.getElementById('add-alarm-btn');
        if (addAlarmBtn) {
            addAlarmBtn.addEventListener('click', () => {
                modalContainer.classList.add('active');
            });
        }

        // Cancel button in modal
        const cancelBtn = modalContainer.querySelector('.cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                modalContainer.classList.remove('active');
            });
        }
    }
}

// Apply theme
function applyTheme(theme) {
    // Remove existing theme classes
    document.body.classList.remove('theme-light', 'theme-dark', 'theme-night');
    
    // Add new theme class
    document.body.classList.add(`theme-${theme}`);
    
    // Save theme preference
    localStorage.setItem('theme', theme);
    state.theme = theme;
    
    // Update theme selection
    document.querySelectorAll('.theme-card').forEach(card => {
        card.classList.toggle('active', card.dataset.theme === theme);
    });
}

// Refresh page content
function refreshPageContent(page) {
    switch (page) {
        case 'alarms':
            refreshAlarms();
            break;
        case 'calendar':
            refreshCalendar();
            break;
        case 'weather':
            refreshWeather();
            break;
        case 'sounds':
            refreshSounds();
            break;
        case 'lights':
            refreshLights();
            break;
        case 'settings':
            refreshSettings();
            break;
    }
}

// Format helpers
function formatTime(date) {
    const format = state.settings?.timeFormat === '12h' ? 'h:mm A' : 'HH:mm';
    return new Date(date).toLocaleTimeString([], { 
        hour: format === 'HH:mm' ? '2-digit' : 'numeric',
        minute: '2-digit',
        hour12: format === 'h:mm A'
    });
}

function formatDate(date) {
    const format = state.settings?.dateFormat || 'iso';
    const d = new Date(date);
    
    switch (format) {
        case 'us':
            return d.toLocaleDateString('en-US');
        case 'uk':
            return d.toLocaleDateString('en-GB');
        case 'full':
            return d.toLocaleDateString('en-US', { 
                month: 'long', 
                day: 'numeric', 
                year: 'numeric' 
            });
        default:
            return d.toISOString().split('T')[0];
    }
}

function formatTemperature(celsius) {
    if (state.settings?.temperatureUnit === 'F') {
        const fahrenheit = (celsius * 9/5) + 32;
        return `${Math.round(fahrenheit)}°F`;
    }
    return `${Math.round(celsius)}°C`;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Export functions for use in other modules
window.app = {
    state,
    formatTime,
    formatDate,
    formatTemperature,
    showNotification
}; 