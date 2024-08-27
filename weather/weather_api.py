# weather_api.py
import requests
import logging
from datetime import datetime, timedelta
from notifications.email_notifications import send_email
from data_management.data_logger import log_rain_forecast, log_last_12h_rain, log_soil_moisture
import threading


class WeatherAPI:
    lock = threading.Lock()
    reported_errors = {
        "soil_moisture_tomato": False,
        "soil_moisture_garden": False
    }

    def __init__(self, weatherapi_api_key, latitude, longitude, ecowitt_application_key, ecowitt_api_key, meteo_station_mac_adresse, email_config):
        self.weatherapi_api_key = weatherapi_api_key
        self.latitude = latitude
        self.longitude = longitude
        self.ecowitt_application_key = ecowitt_application_key
        self.ecowitt_api_key = ecowitt_api_key
        self.meteo_station_mac_adresse = meteo_station_mac_adresse
        self.email_config = email_config

    def get_forecast_data(self):
        """ Obtient les prévisions météo depuis weatherapi.com """
        url = (
            f"http://api.weatherapi.com/v1/forecast.json?"
            f"key={self.weatherapi_api_key}&q={self.latitude},{self.longitude}"
            f"&days=1&hourly=1"
        )
        response = requests.get(url)
        data = response.json()
        return data

    def extract_rain_forecast(self, data):
        """ Extrait les données météo obtenues depuis weatherapi.com """
        forecastday = data.get("forecast", {}).get("forecastday", [])
        if not forecastday:
            error_message = "Erreur : Aucune donnée 'forecastday' trouvée."
            logging.error(error_message)
            send_email(self.email_config, "Erreur dans l'API météo", error_message)
            return []

        hourly_forecast = forecastday[0].get("hour", [])
        rain_forecast = [
            (
                datetime.strptime(hour["time"], "%Y-%m-%d %H:%M").strftime(
                    "%Y-%m-%d %H:%M"
                ),
                hour["precip_mm"],
            )
            for hour in hourly_forecast[:12]
        ]
        return rain_forecast

    def get_next_12_hour_rain_data(self):
        """
        Calcule le volume de pluie prévu pour les 12 prochaines heures
        et enrégistre les données dans la BD
        """
        data = self.get_forecast_data()
        rain_forecast = self.extract_rain_forecast(data)

        total_rain = sum(rain for _, rain in rain_forecast)
        # log_rain_forecast(total_rain)  # Enregistre les prévisions dans la base de données

        logging.info(
            "Il est prévu de tomber %.2f mm de pluie au cours des 12 prochaines heures.",
            total_rain,
        )
        return total_rain

    def get_last_12_hour_rain_data(self):
        """
        Retrieves the rainfall data for the last 12 hours in millimeters using the Ecowitt API v3.
        """
        base_url = "https://api.ecowitt.net/api/v3/device/history"
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=12)
        params = {
            "application_key": self.ecowitt_application_key,
            "api_key": self.ecowitt_api_key,
            "mac": self.meteo_station_mac_adresse,
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "call_back": "rainfall",
            "rainfall_unitid": 12,
        }

        response = requests.get(base_url, params=params)

        # Check if the request was successful
        if response.status_code != 200:
            error_message = f"Error: {response.status_code}. Unable to retrieve data from the Ecowitt API."
            logging.error(error_message)
            return None

        data = response.json()

        # Check if the necessary data is in the response
        if (
                "data" not in data
                or "rainfall" not in data["data"]
                or "rain_rate" not in data["data"]["rainfall"]
                or "list" not in data["data"]["rainfall"]["rain_rate"]
        ):
            error_message = "Error: The expected data structure was not found in the response."
            logging.error(error_message)
            return None

        rain_rate_data = data["data"]["rainfall"]["rain_rate"]["list"]
        last_12h_rainfall: float | int = sum(float(rainfall) for timestamp, rainfall in rain_rate_data.items())
        # log_last_12h_rain(last_12h_rainfall)
        logging.info("Rainfall over the last 12 hours: %.2f mm", last_12h_rainfall)

        return last_12h_rainfall

    def get_soil_moisture_data(self):
        """
        Retrieves soil moisture data for both channels (soil_ch1 and soil_ch3)
        using the Ecowitt API v3 and returns them as moisture_data_tomato and moisture_data_garden.
        """
        with self.lock:
            base_url = "https://api.ecowitt.net/api/v3/device/real_time"
            moisture_data = {}

            for channel, zone in [("soil_ch1", "Tomato"), ("soil_ch3", "Garden")]:
                try:
                    params = {
                        "application_key": self.ecowitt_application_key,
                        "api_key": self.ecowitt_api_key,
                        "mac": self.meteo_station_mac_adresse,
                        "call_back": f"{channel}.soilmoisture",
                    }

                    response = requests.get(base_url, params=params)

                    if response.status_code != 200:
                        error_message = f"Erreur : {response.status_code}. Impossible de récupérer les données de l'API Ecowitt pour {channel}."
                        logging.error(error_message)
                        if not self.reported_errors[f"soil_moisture_{zone.lower()}"]:
                            send_email(self.email_config,
                                       f"Erreur dans l'API Ecowitt pour la reprise du taux d'humidité de {channel}",
                                       error_message)
                            self.reported_errors[f"soil_moisture_{zone.lower()}"] = True
                        moisture_data[zone] = 50.0  # Définir une valeur par défaut en cas d'erreur
                        continue

                    data = response.json()

                    if "data" not in data or channel not in data["data"] or "soilmoisture" not in data["data"][channel] or "value" not in data["data"][channel]["soilmoisture"]:
                        error_message = f"Erreur : La structure de données attendue pour {channel} n'a pas été trouvée dans la réponse."
                        logging.error(error_message)
                        if not self.reported_errors[f"soil_moisture_{zone.lower()}"]:
                            send_email(self.email_config,
                                       f"Erreur dans l'API Ecowitt pour la reprise du taux d'humidité de {channel}",
                                       error_message)
                            self.reported_errors[f"soil_moisture_{zone.lower()}"] = True
                        moisture_data[zone] = 50.0  # Définir une valeur par défaut en cas d'erreur
                        continue

                    moisture_data[zone] = float(data["data"][channel]["soilmoisture"]["value"])
                    log_soil_moisture(moisture_data[zone], zone)
                    logging.info(f"Current soil moisture level for {zone}: {moisture_data[zone]}")
                    self.reported_errors[f"soil_moisture_{zone.lower()}"] = False

                except Exception as e:
                    logging.error(f"Erreur lors de la récupération des données d'humidité pour {zone}: {str(e)}")
                    if not self.reported_errors[f"soil_moisture_{zone.lower()}"]:
                        send_email(self.email_config, f"Erreur lors de la récupération des données d'humidité pour {zone}", str(e))
                        self.reported_errors[f"soil_moisture_{zone.lower()}"] = True
                    moisture_data[zone] = 50.0  # Définir une valeur par défaut en cas d'erreur

            return moisture_data.get("Tomato"), moisture_data.get("Garden")

    def reset_reported_errors(self):
        self.reported_errors = {key: False for key in self.reported_errors}
        logging.info("Reported errors reset.")

    def get_history_data(self, start_date, end_date, call_back, temp_unitid=None, solar_irradiance_unitid=None,
                         rainfall_unitid=None, wind_speed_unitid=None):
        params = {
            "application_key": self.ecowitt_application_key,
            "api_key": self.ecowitt_api_key,
            "mac": self.meteo_station_mac_adresse,
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "call_back": call_back,
            "cycle_type": "auto"
        }
        # Optionally include specific unit IDs for temperature, solar irradiance, rainfall, and wind speed
        if temp_unitid:
            params["temp_unitid"] = temp_unitid
        if solar_irradiance_unitid:
            params["solar_irradiance_unitid"] = solar_irradiance_unitid
        if rainfall_unitid:
            params["rainfall_unitid"] = rainfall_unitid
        if wind_speed_unitid:
            params["wind_speed_unitid"] = wind_speed_unitid

        response = requests.get("https://api.ecowitt.net/api/v3/device/history", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("Failed to fetch data: %s", response.status_code)
            return None

    def get_last_1_hour_rain_data(self):
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now
        # Adding 'rainfall_unitid=12' to request rainfall data in mm
        data = self.get_history_data(start_date, end_date, "rainfall.hourly", rainfall_unitid=12)
        if data and 'data' in data and 'rainfall' in data['data'] and 'hourly' in data['data']['rainfall']:
            rain_data = data['data']['rainfall']['hourly']['list']
            rain_values = [float(rain) for rain in rain_data.values()]
            total_rainfall = sum(rain_values) if rain_values else None
            return total_rainfall
        return None  # Return None if no valid data is found or if the API call fails

    def get_last_1_hour_temperature_data(self):
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now
        # Adding 'temp_unitid=1' to the request to specify Celsius as the temperature unit
        data = self.get_history_data(start_date, end_date, "outdoor.temperature", temp_unitid=1)
        if data and 'data' in data and 'outdoor' in data['data'] and 'temperature' in data['data']['outdoor']:
            temperature_data = data['data']['outdoor']['temperature']['list']
            temperatures = [float(temp) for temp in temperature_data.values()]
            average_temperature = sum(temperatures) / len(temperatures) if temperatures else None
            return average_temperature
        return None  # Return None if no valid data is found or if the API call fails

    def get_last_1_hour_wind_data(self):
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now
        # Adding 'wind_speed_unitid=7' to request wind speed data in km/h
        data = self.get_history_data(start_date, end_date, "wind.wind_speed", wind_speed_unitid=7)
        if data and 'data' in data and 'wind' in data['data'] and 'wind_speed' in data['data']['wind']:
            wind_data = data['data']['wind']['wind_speed']['list']
            wind_speeds = [float(speed) for speed in wind_data.values()]
            average_wind_speed = sum(wind_speeds) / len(wind_speeds) if wind_speeds else None
            return average_wind_speed
        return None  # Return None if no valid data is found or if the API call fails

    def get_last_1_hour_sun_data(self):
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now
        # Adding 'solar_irradiance_unitid=16' to request solar radiation in W/m²
        data = self.get_history_data(start_date, end_date, "solar_and_uvi.solar", solar_irradiance_unitid=16)
        if data and 'data' in data and 'solar_and_uvi' in data['data'] and 'solar' in data['data']['solar_and_uvi']:
            solar_data = data['data']['solar_and_uvi']['solar']['list']
            solar_values = [float(solar) for solar in solar_data.values()]
            average_solar_radiation = sum(solar_values) / len(solar_values) if solar_values else None
            return average_solar_radiation
        return None  # Return None if no valid data is found or if the API call fails

    def get_last_1_hour_humidity_data(self):
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now
        data = self.get_history_data(start_date, end_date, "outdoor.humidity")
        if data and 'data' in data and 'outdoor' in data['data'] and 'humidity' in data['data']['outdoor']:
            humidity_data = data['data']['outdoor']['humidity']['list']
            humidities = [float(humidity) for humidity in humidity_data.values()]
            average_humidity = sum(humidities) / len(humidities) if humidities else None
            return average_humidity
        return None  # Return None if no valid data is found or if the API call fails

