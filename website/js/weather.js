// Weather state
let weatherData = null;
let weatherAlerts = [];
let weatherForecast = [];
let updateInterval = null;

// Initialize weather component
function initializeWeather() {
    // Load initial weather data
    loadWeatherData();
    
    // Set up automatic updates
    updateInterval = setInterval(loadWeatherData, 15 * 60 * 1000); // Update every 15 minutes
    
    // Add event listeners
    addWeatherEventListeners();
}

// Load weather data from server
function loadWeatherData() {
    // Load current weather
    fetch(`${API_BASE_URL}/weather/current`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            weatherData = data.weather;
            renderCurrentWeather();
        }
    })
    .catch(error => {
        console.error('Error loading weather:', error);
        showNotification('Error loading weather data', 'error');
    });
    
    // Load weather alerts
    fetch(`${API_BASE_URL}/weather/alerts`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            weatherAlerts = data.alerts;
            renderWeatherAlerts();
        }
    })
    .catch(error => {
        console.error('Error loading weather alerts:', error);
    });
    
    // Load weather forecast
    fetch(`${API_BASE_URL}/weather/forecast`, {
        headers: window.defaultHeaders
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            weatherForecast = data.forecast;
            renderWeatherForecast();
        }
    })
    .catch(error => {
        console.error('Error loading weather forecast:', error);
    });
}

// Render current weather
function renderCurrentWeather() {
    if (!weatherData) return;
    
    const container = document.querySelector('.current-weather');
    container.innerHTML = `
        <div class="weather-card">
            <div class="weather-header">
                <h3>Current Weather</h3>
                <span class="location">${weatherData.location.name}, ${weatherData.location.region}</span>
            </div>
            <div class="weather-content">
                <div class="weather-main">
                    <div class="temperature">
                        ${app.formatTemperature(weatherData.temp_c)}
                    </div>
                    <div class="condition">
                        ${weatherData.condition.text}
                    </div>
                </div>
                <div class="weather-details">
                    <div class="detail">
                        <i class="material-icons">water_drop</i>
                        <span>Humidity: ${weatherData.humidity}%</span>
                    </div>
                    <div class="detail">
                        <i class="material-icons">air</i>
                        <span>Wind: ${weatherData.wind_kph} km/h</span>
                    </div>
                    <div class="detail">
                        <i class="material-icons">umbrella</i>
                        <span>Precipitation: ${weatherData.precip_mm} mm</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Render weather alerts
function renderWeatherAlerts() {
    const container = document.querySelector('.weather-alerts');
    container.innerHTML = '';
    
    if (weatherAlerts.length === 0) {
        container.innerHTML = `
            <div class="no-alerts">
                <i class="material-icons">check_circle</i>
                <p>No weather alerts</p>
            </div>
        `;
        return;
    }
    
    weatherAlerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = `alert-card ${alert.severity.toLowerCase()}`;
        alertElement.innerHTML = `
            <div class="alert-header">
                <i class="material-icons">warning</i>
                <span class="alert-type">${alert.event}</span>
                <span class="alert-severity">${alert.severity}</span>
            </div>
            <div class="alert-content">
                <p class="alert-headline">${alert.headline}</p>
                <div class="alert-details">
                    <p><strong>Areas:</strong> ${alert.areas}</p>
                    <p><strong>Valid:</strong> ${formatAlertTime(alert.effective)} - ${formatAlertTime(alert.expires)}</p>
                </div>
                <button class="show-details-btn">Show Details</button>
            </div>
            <div class="alert-full-details hidden">
                <p>${alert.desc}</p>
                ${alert.instruction ? `<p><strong>Instructions:</strong> ${alert.instruction}</p>` : ''}
            </div>
        `;
        
        // Add event listener for details button
        alertElement.querySelector('.show-details-btn').addEventListener('click', (e) => {
            const details = alertElement.querySelector('.alert-full-details');
            details.classList.toggle('hidden');
            e.target.textContent = details.classList.contains('hidden') ? 'Show Details' : 'Hide Details';
        });
        
        container.appendChild(alertElement);
    });
}

// Render weather forecast
function renderWeatherForecast() {
    const container = document.querySelector('.forecast');
    container.innerHTML = `
        <div class="forecast-card">
            <h3>3-Day Forecast</h3>
            <div class="forecast-list">
                ${weatherForecast.map(day => `
                    <div class="forecast-day">
                        <div class="forecast-date">${formatForecastDate(day.date)}</div>
                        <div class="forecast-temps">
                            <span class="high">${app.formatTemperature(day.max_temp_c)}</span>
                            <span class="low">${app.formatTemperature(day.min_temp_c)}</span>
                        </div>
                        <div class="forecast-condition">${day.condition.text}</div>
                        <div class="forecast-rain">
                            <i class="material-icons">water_drop</i>
                            <span>${day.chance_of_rain}%</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Format alert time
function formatAlertTime(timestamp) {
    const date = new Date(timestamp);
    return `${app.formatDate(date)} ${app.formatTime(date)}`;
}

// Format forecast date
function formatForecastDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('default', { weekday: 'short', month: 'short', day: 'numeric' });
}

// Add weather event listeners
function addWeatherEventListeners() {
    // Add refresh button handler
    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'refresh-btn';
    refreshBtn.innerHTML = '<i class="material-icons">refresh</i>';
    refreshBtn.addEventListener('click', loadWeatherData);
    
    document.querySelector('.weather-settings').prepend(refreshBtn);
}

// Clean up weather component
function cleanupWeather() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
}

// Refresh weather
function refreshWeather() {
    loadWeatherData();
} 