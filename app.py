from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
from collections import Counter
import traceback
import sys
import io

# Fix for Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)

# Your OpenWeatherMap API key
API_KEY = "32939c916d7f3183d1a73e7a89a7b26b"  # MAKE SURE YOU REPLACE THIS!

# API endpoints
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/reverse"
DIRECT_GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_city', methods=['POST'])
def search_city():
    try:
        data = request.json
        city = data.get('city')
        
        # Use simple print without special characters
        print(f"Searching for: {city}")
        
        if not city:
            return jsonify({'error': 'Please enter a city name'}), 400
        
        # STEP 1: Get coordinates for the city
        geo_params = {
            'q': city,
            'limit': 1,
            'appid': API_KEY
        }
        
        geo_response = requests.get(DIRECT_GEOCODING_URL, params=geo_params)
        
        if geo_response.status_code != 200:
            return jsonify({'error': 'Error finding city'}), 500
        
        geo_data = geo_response.json()
        
        if not geo_data:
            return jsonify({'error': f'City "{city}" not found. Please check the spelling.'}), 404
        
        # Extract coordinates
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        found_city = geo_data[0]['name']
        country = geo_data[0].get('country', '')
        
        # STEP 2: Get current weather using coordinates
        current_params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric',
            'lang': 'en'
        }
        
        current_response = requests.get(CURRENT_WEATHER_URL, params=current_params)
        
        if current_response.status_code != 200:
            return jsonify({'error': 'Error getting weather data'}), 500
        
        current_data = current_response.json()
        
        # STEP 3: Get forecast using coordinates
        forecast_params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric',
            'lang': 'en'
        }
        
        forecast_response = requests.get(FORECAST_URL, params=forecast_params)
        
        if forecast_response.status_code != 200:
            return jsonify({'error': 'Error getting forecast data'}), 500
        
        forecast_data = forecast_response.json()
        
        # Process current weather (remove any potential special characters)
        current_weather = {
            'city': found_city.encode('ascii', 'ignore').decode('ascii'),
            'country': country.encode('ascii', 'ignore').decode('ascii'),
            'temperature': round(current_data['main']['temp']),
            'feels_like': round(current_data['main']['feels_like']),
            'description': current_data['weather'][0]['description'].capitalize(),
            'icon': current_data['weather'][0]['icon'],
            'humidity': current_data['main']['humidity'],
            'wind_speed': round(current_data['wind']['speed'], 1),
            'pressure': current_data['main']['pressure']
        }
        
        # Process hourly forecast (next 24 hours)
        hourly_forecast = []
        for i in range(min(8, len(forecast_data['list']))):
            forecast = forecast_data['list'][i]
            hourly_forecast.append({
                'time': datetime.fromtimestamp(forecast['dt']).strftime('%H:%M'),
                'temp': round(forecast['main']['temp']),
                'icon': forecast['weather'][0]['icon']
            })
        
        # Process daily forecast
        daily_forecast = []
        processed_dates = set()
        
        for forecast in forecast_data['list']:
            forecast_date = datetime.fromtimestamp(forecast['dt']).date()
            date_str = forecast_date.strftime('%Y-%m-%d')
            
            if date_str not in processed_dates and len(daily_forecast) < 7:
                processed_dates.add(date_str)
                
                # Get all forecasts for this day
                day_forecasts = [f for f in forecast_data['list'] 
                               if datetime.fromtimestamp(f['dt']).date() == forecast_date]
                
                day_temps = [f['main']['temp'] for f in day_forecasts]
                day_icons = [f['weather'][0]['icon'] for f in day_forecasts]
                
                # Get most common weather icon for the day
                most_common_icon = Counter(day_icons).most_common(1)[0][0]
                
                daily_forecast.append({
                    'date': forecast_date.strftime('%A, %b %d'),
                    'day_name': forecast_date.strftime('%A'),
                    'short_date': forecast_date.strftime('%d %b'),
                    'max_temp': round(max(day_temps)),
                    'min_temp': round(min(day_temps)),
                    'icon': most_common_icon,
                    'full_data': [{
                        'time': datetime.fromtimestamp(f['dt']).strftime('%H:%M'),
                        'temp': round(f['main']['temp']),
                        'icon': f['weather'][0]['icon'],
                        'description': f['weather'][0]['description'].capitalize()
                    } for f in day_forecasts[:4]]
                })
        
        print(f"Success! Weather data for {found_city} sent to browser")
        return jsonify({
            'current': current_weather,
            'hourly': hourly_forecast,
            'daily': daily_forecast
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/get_weather_by_coords', methods=['POST'])
def get_weather_by_coords():
    try:
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Location coordinates required'}), 400
        
        # Get city name from coordinates
        geo_params = {
            'lat': lat,
            'lon': lon,
            'limit': 1,
            'appid': API_KEY
        }
        
        geo_response = requests.get(GEOCODING_URL, params=geo_params)
        geo_data = geo_response.json()
        
        city_name = geo_data[0]['name'] if geo_data else "Unknown"
        country = geo_data[0]['country'] if geo_data else ""
        
        # Get current weather
        current_params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric',
            'lang': 'en'
        }
        
        current_response = requests.get(CURRENT_WEATHER_URL, params=current_params)
        current_data = current_response.json()
        
        # Get forecast
        forecast_params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric',
            'lang': 'en'
        }
        
        forecast_response = requests.get(FORECAST_URL, params=forecast_params)
        forecast_data = forecast_response.json()
        
        # Process current weather
        current_weather = {
            'city': city_name,
            'country': country,
            'temperature': round(current_data['main']['temp']),
            'feels_like': round(current_data['main']['feels_like']),
            'description': current_data['weather'][0]['description'].capitalize(),
            'icon': current_data['weather'][0]['icon'],
            'humidity': current_data['main']['humidity'],
            'wind_speed': round(current_data['wind']['speed'], 1),
            'pressure': current_data['main']['pressure']
        }
        
        # Process hourly forecast
        hourly_forecast = []
        for i in range(min(8, len(forecast_data['list']))):
            forecast = forecast_data['list'][i]
            hourly_forecast.append({
                'time': datetime.fromtimestamp(forecast['dt']).strftime('%H:%M'),
                'temp': round(forecast['main']['temp']),
                'icon': forecast['weather'][0]['icon']
            })
        
        # Process daily forecast
        daily_forecast = []
        processed_dates = set()
        
        for forecast in forecast_data['list']:
            forecast_date = datetime.fromtimestamp(forecast['dt']).date()
            date_str = forecast_date.strftime('%Y-%m-%d')
            
            if date_str not in processed_dates and len(daily_forecast) < 7:
                processed_dates.add(date_str)
                
                day_forecasts = [f for f in forecast_data['list'] 
                               if datetime.fromtimestamp(f['dt']).date() == forecast_date]
                
                day_temps = [f['main']['temp'] for f in day_forecasts]
                day_icons = [f['weather'][0]['icon'] for f in day_forecasts]
                
                most_common_icon = Counter(day_icons).most_common(1)[0][0]
                
                daily_forecast.append({
                    'date': forecast_date.strftime('%A, %b %d'),
                    'day_name': forecast_date.strftime('%A'),
                    'short_date': forecast_date.strftime('%d %b'),
                    'max_temp': round(max(day_temps)),
                    'min_temp': round(min(day_temps)),
                    'icon': most_common_icon
                })
        
        return jsonify({
            'current': current_weather,
            'hourly': hourly_forecast,
            'daily': daily_forecast
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 40)
    print("WEATHER APP STARTING")
    print("=" * 40)
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True)