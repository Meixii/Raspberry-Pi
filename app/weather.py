import os
import json
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WeatherManager:
    def __init__(self, api_key):
        """Initialize the weather manager."""
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1"
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)  # Cache weather data for 15 minutes
        logger.info("Weather manager initialized")

    def get_current_weather(self):
        """Get current weather data."""
        try:
            # Check cache first
            if 'current' in self.cache:
                cache_time, cache_data = self.cache['current']
                if datetime.now() - cache_time < self.cache_duration:
                    return cache_data

            # Make API request
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': 'auto:ip',  # Use IP-based location
                'aqi': 'no'  # We don't need air quality data
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Extract relevant weather data
            data = response.json()
            weather_data = {
                'temp_c': data['current']['temp_c'],
                'humidity': data['current']['humidity'],
                'condition': {
                    'text': data['current']['condition']['text'],
                    'code': data['current']['condition']['code']
                },
                'wind_kph': data['current']['wind_kph'],
                'precip_mm': data['current']['precip_mm'],
                'location': {
                    'name': data['location']['name'],
                    'region': data['location']['region']
                }
            }
            
            # Update cache
            self.cache['current'] = (datetime.now(), weather_data)
            
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing weather data: {str(e)}")
            return None

    def get_forecast(self, days=3):
        """Get weather forecast for specified number of days."""
        try:
            # Check cache first
            cache_key = f'forecast_{days}'
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cache_data

            # Make API request
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': 'auto:ip',
                'days': days,
                'aqi': 'no'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Extract forecast data
            data = response.json()
            forecast_data = []
            
            for day in data['forecast']['forecastday']:
                forecast_data.append({
                    'date': day['date'],
                    'max_temp_c': day['day']['maxtemp_c'],
                    'min_temp_c': day['day']['mintemp_c'],
                    'condition': {
                        'text': day['day']['condition']['text'],
                        'code': day['day']['condition']['code']
                    },
                    'chance_of_rain': day['day']['daily_chance_of_rain']
                })
            
            # Update cache
            self.cache[cache_key] = (datetime.now(), forecast_data)
            
            return forecast_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forecast data: {str(e)}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing forecast data: {str(e)}")
            return None

    def get_alerts(self):
        """Get current weather alerts."""
        try:
            # Check cache first
            if 'alerts' in self.cache:
                cache_time, cache_data = self.cache['alerts']
                if datetime.now() - cache_time < timedelta(minutes=5):  # Shorter cache for alerts
                    return cache_data

            # Make API request
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': 'auto:ip',
                'days': 1,
                'alerts': 'yes'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Extract alerts
            data = response.json()
            alerts = data.get('alerts', {}).get('alert', [])
            
            # Process and filter alerts
            processed_alerts = []
            for alert in alerts:
                processed_alerts.append({
                    'headline': alert['headline'],
                    'severity': alert['severity'],
                    'urgency': alert['urgency'],
                    'areas': alert['areas'],
                    'category': alert['category'],
                    'event': alert['event'],
                    'effective': alert['effective'],
                    'expires': alert['expires'],
                    'desc': alert['desc']
                })
            
            # Sort alerts by severity
            severity_order = {'Extreme': 0, 'Severe': 1, 'Moderate': 2, 'Minor': 3}
            processed_alerts.sort(key=lambda x: severity_order.get(x['severity'], 999))
            
            # Update cache
            self.cache['alerts'] = (datetime.now(), processed_alerts)
            
            return processed_alerts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather alerts: {str(e)}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing weather alerts: {str(e)}")
            return None

    def clear_cache(self):
        """Clear the weather data cache."""
        self.cache.clear()
        logger.info("Weather cache cleared") 