from flask import Flask, request, render_template
import requests
from api import API_KEY

app = Flask(__name__)

WEATHER_BASE_URL = "http://dataservice.accuweather.com"

# Функция для оценки неблагоприятных условий
def analyze_weather_conditions(min_temp, max_temp, wind_velocity, precipitation_chance):
    if min_temp < 0 or max_temp > 35:
        return "Температурные условия неблагоприятны!"
    if wind_velocity > 50:
        return "Слишком сильный ветер!"
    if precipitation_chance > 70:
        return "Высокая вероятность дождя!"
    return "Погодные условия удовлетворительные."

# Функция для поиска ключа местоположения по координатам
def retrieve_location_key(latitude, longitude):
    location_request_url = f"{WEATHER_BASE_URL}/locations/v1/cities/geoposition/search?apikey={API_KEY}&q={latitude}%2C{longitude}"
    try:
        location_response = requests.get(location_request_url)
        location_info = location_response.json()
        return location_info['Key']
    except Exception:
        return render_template('home.html', error_message="Ошибка определения местоположения")

# Функция для получения прогноза погоды по ключу местоположения
def fetch_weather_forecast(loc_key):
    forecast_request_url = f"{WEATHER_BASE_URL}/forecasts/v1/daily/1day/{loc_key}?apikey={API_KEY}&language=en-us&details=true&metric=true"
    try:
        weather_response = requests.get(forecast_request_url)
        if weather_response.status_code != 200:
            return None
        return weather_response.json()
    except Exception:
        return render_template('home.html', error_message="Ошибка получения данных о погоде")

# Главная страница
@app.route('/')
def main_page():
    return render_template('home.html')

# Маршрут для получения прогноза погоды
@app.route('/get-forecast', methods=['POST'])
def process_weather_request():
    # Получаем введённые данные
    start_lat = request.form['latitude_start']
    start_lon = request.form['longitude_start']
    end_lat = request.form['latitude_end']
    end_lon = request.form['longitude_end']

    # Проверка заполнения всех полей
    if not all([start_lat, start_lon, end_lat, end_lon]):
        return "Ошибка: Все координаты должны быть указаны!", 400

    # Получение location_key для стартовой точки
    start_loc_key = retrieve_location_key(start_lat, start_lon)
    if not start_loc_key:
        return "Ошибка: Не удалось найти местоположение для стартовой точки!", 400

    # Получение location_key для конечной точки
    end_loc_key = retrieve_location_key(end_lat, end_lon)
    if not end_loc_key:
        return "Ошибка: Не удалось найти местоположение для конечной точки!", 400

    # Получение прогноза погоды для обеих точек
    start_weather = fetch_weather_forecast(start_loc_key)
    end_weather = fetch_weather_forecast(end_loc_key)

    if not start_weather or not end_weather:
        return "Ошибка: Невозможно получить данные прогноза!", 400

    # Извлекаем данные для старта
    start_forecast = start_weather['DailyForecasts'][0]
    start_max_temp = start_forecast['Temperature']['Maximum']['Value']
    start_min_temp = start_forecast['Temperature']['Minimum']['Value']
    start_wind_speed = start_forecast['Day']['Wind']['Speed']['Value']
    start_rain_prob = start_forecast['Day']['PrecipitationProbability']

    # Извлекаем данные для конечной точки
    end_forecast = end_weather['DailyForecasts'][0]
    end_max_temp = end_forecast['Temperature']['Maximum']['Value']
    end_min_temp = end_forecast['Temperature']['Minimum']['Value']
    end_wind_speed = end_forecast['Day']['Wind']['Speed']['Value']
    end_rain_prob = end_forecast['Day']['PrecipitationProbability']

    # Оценка погодных условий для обеих точек
    start_conditions = analyze_weather_conditions(start_min_temp, start_max_temp, start_wind_speed, start_rain_prob)
    end_conditions = analyze_weather_conditions(end_min_temp, end_max_temp, end_wind_speed, end_rain_prob)

    # Отправка результата на страницу
    return f'''
        <h2>Погода в начальной точке:</h2>
        <p>{start_conditions}</p>
        <h2>Погода в конечной точке:</h2>
        <p>{end_conditions}</p>
        <a href="/">Вернуться</a>
    '''

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
