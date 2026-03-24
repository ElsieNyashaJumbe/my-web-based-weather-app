// Get user's location when page loads
window.onload = function() {
    console.log("Page loaded, getting location...");
    getLocation();
};

// Get user's current location
function getLocation() {
    if (navigator.geolocation) {
        showLoading(true);
        navigator.geolocation.getCurrentPosition(
            position => {
                console.log("Got user location:", position.coords);
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                getWeatherByCoords(lat, lon);
            },
            error => {
                console.error("Geolocation error:", error);
                showLoading(false);
                showError("Please enable location access or search for a city");
            }
        );
    } else {
        showError("Geolocation is not supported by your browser");
    }
}

// Get weather by coordinates
async function getWeatherByCoords(lat, lon) {
    try {
        console.log("Getting weather for coordinates:", lat, lon);
        
        const response = await fetch('/get_weather_by_coords', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ lat, lon })
        });
        
        console.log("Response status:", response.status);
        const data = await response.json();
        console.log("Weather data received:", data);
        
        if (!response.ok) {
            throw new Error(data.error || 'Error fetching weather');
        }
        
        displayAllWeather(data);
        
    } catch (error) {
        console.error("Weather fetch error:", error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Search for a city
async function searchCity() {
    const cityInput = document.getElementById('cityInput');
    const city = cityInput.value.trim();
    
    console.log("Search button clicked, city:", city);
    
    if (!city) {
        showError('Please enter a city name');
        return;
    }
    
    showLoading(true);
    hideError();
    hideWeatherContent();
    
    try {
        console.log("Sending search request for:", city);
        
        const response = await fetch('/search_city', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ city: city })
        });
        
        console.log("Search response status:", response.status);
        
        const data = await response.json();
        console.log("Search response data:", data);
        
        if (!response.ok) {
            throw new Error(data.error || 'Error fetching weather data');
        }
        
        displayAllWeather(data);
        
    } catch (error) {
        console.error("Search error:", error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Display all weather data
function displayAllWeather(data) {
    console.log("Displaying weather data:", data);
    
    // Display current weather
    displayCurrentWeather(data.current);
    
    // Display hourly forecast
    displayHourlyForecast(data.hourly);
    
    // Display daily forecast
    displayDailyForecast(data.daily);
    
    // Show the weather content
    document.getElementById('weatherContent').style.display = 'block';
}

// Display current weather
function displayCurrentWeather(current) {
    document.getElementById('cityName').textContent = `${current.city}, ${current.country}`;
    document.getElementById('currentTemp').textContent = current.temperature;
    document.getElementById('feelsLike').textContent = current.feels_like;
    document.getElementById('currentDescription').textContent = current.description;
    document.getElementById('humidity').textContent = `${current.humidity}%`;
    document.getElementById('windSpeed').textContent = `${current.wind_speed} m/s`;
    document.getElementById('pressure').textContent = `${current.pressure} hPa`;
    
    const iconUrl = `https://openweathermap.org/img/wn/${current.icon}@2x.png`;
    document.getElementById('currentWeatherIcon').src = iconUrl;
}

// Display hourly forecast
function displayHourlyForecast(hourlyData) {
    const container = document.getElementById('hourlyForecast');
    container.innerHTML = '';
    
    hourlyData.forEach(hour => {
        const hourElement = document.createElement('div');
        hourElement.className = 'hourly-item';
        hourElement.innerHTML = `
            <div class="hour-time">${hour.time}</div>
            <img src="https://openweathermap.org/img/wn/${hour.icon}.png" alt="Weather icon">
            <div class="hour-temp">${hour.temp}°C</div>
        `;
        container.appendChild(hourElement);
    });
}

// Display daily forecast
function displayDailyForecast(dailyData) {
    const container = document.getElementById('dailyForecast');
    container.innerHTML = '';
    
    dailyData.forEach((day, index) => {
        const dayElement = document.createElement('div');
        dayElement.className = 'daily-item';
        dayElement.onclick = () => showDayDetails(day);
        dayElement.innerHTML = `
            <div class="day-name">${index === 0 ? 'Today' : day.day_name}</div>
            <div class="day-date">${day.short_date}</div>
            <img src="https://openweathermap.org/img/wn/${day.icon}.png" alt="Weather icon">
            <div class="day-temp">
                <span class="max-temp">${day.max_temp}°</span>
                <span class="min-temp">${day.min_temp}°</span>
            </div>
        `;
        container.appendChild(dayElement);
    });
}

// Show day details
function showDayDetails(day) {
    console.log("Showing details for:", day);
    alert(`Details for ${day.date}\nMax: ${day.max_temp}°C\nMin: ${day.min_temp}°C`);
}

// Helper functions
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
    if (show) {
        document.getElementById('weatherContent').style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    console.error("Error displayed:", message);
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function hideWeatherContent() {
    document.getElementById('weatherContent').style.display = 'none';
}

function refreshWeather() {
    getLocation();
}

// Enter key support
document.getElementById('cityInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchCity();
    }
});