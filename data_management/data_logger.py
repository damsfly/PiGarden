from sqlalchemy.orm import sessionmaker
import logging
from config import load_config
from data_management.database import engine
from models import (
    CpuTemperature, TechnicalCabinetConditions, WaterLevel, RainForecast, Precipitation,
    Hygrometry, SystemState, WateringSession, HourlyRain, HourlyTemperature, HourlyWind,
    HourlySunlight, HourlyHumidity
)
from custom_logging import setup_logger

# Configurer le logger
app_logger = setup_logger('log_watering_garden.log', 'data_logger')

# Charger la configuration
config = load_config()
db_config = config['database']
DATABASE_URL = f"mariadb+mariadbconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fonctions de journalisation
def log_cpu_temperature(temperature):
    """ Enregistre la température du processeur dans la base de données """
    if temperature is None:
        app_logger.warning("Attempted to log None as CPU temperature")
        return
    rounded_temperature = round(temperature, 2)
    try:
        session = SessionLocal()
        cpu_temp = CpuTemperature(temperature=rounded_temperature)
        session.add(cpu_temp)
        session.commit()
        app_logger.info("CPU temperature data saved to database. Temperature: %s °C", rounded_temperature)
    except Exception as error:
        app_logger.error("Error saving CPU temperature data to database. Exception: %s", str(error))
    finally:
        session.close()


def log_technical_cabinet_conditions(temperature, humidity):
    """ Enregistre la température et l'humidité de l'armoire technique dans la base de données """
    if temperature is None or humidity is None:
        app_logger.warning("Attempted to log None as technical cabinet conditions")
        return
    rounded_temperature = round(temperature, 2)
    rounded_humidity = round(humidity, 2)
    try:
        session = SessionLocal()
        tech_conditions = TechnicalCabinetConditions(temperature=rounded_temperature, humidity=rounded_humidity)
        session.add(tech_conditions)
        session.commit()
        app_logger.info("Technical cabinet conditions data saved to database. Temperature: %s °C, Humidity: %s %%", rounded_temperature, rounded_humidity)
    except Exception as error:
        app_logger.error("Error saving technical cabinet conditions data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_water_level(level):
    """ Enregistre le niveau de l'eau dans la base de données """
    rounded_level = round(level, 1)  # Arrondi à une décimale
    try:
        session = SessionLocal()
        water_level = WaterLevel(level=rounded_level)
        session.add(water_level)
        session.commit()
        app_logger.info("Water level data saved to database. Level: %s", rounded_level)
    except Exception as error:
        app_logger.error("Error saving water level data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_rain_forecast(amount):
    """ Enregistre les prévisions de pluie dans la base de données """
    try:
        session = SessionLocal()
        rain_forecast = RainForecast(amount=amount)
        session.add(rain_forecast)
        session.commit()
        app_logger.info("Rain forecast data saved to database. Amount: %s mm", amount)
    except Exception as error:
        app_logger.error("Error saving rain forecast data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_last_12h_rain(amount):
    """ Enregistre le volume de pluie réel tombé dans la base de données """
    try:
        session = SessionLocal()
        precipitation = Precipitation(amount=amount)
        session.add(precipitation)
        session.commit()
        app_logger.info("Actual rain data saved to database. Amount: %s mm", amount)
    except Exception as error:
        app_logger.error("Error saving actual rain data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_soil_moisture(level, zone="general"):
    """ Enregistre les données d'humidité du sol dans la base de données """
    try:
        session = SessionLocal()
        hygrometry = Hygrometry(level=level, zone=zone)
        session.add(hygrometry)
        session.commit()
        app_logger.info("Soil moisture data saved to database. Level: %s, Zone: %s", level, zone)
    except Exception as error:
        app_logger.error("Error saving soil moisture data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_system_state(state, zone, source, mode):
    """ Enregistre l'état de l'arrosage dans la base de données """
    try:
        session = SessionLocal()
        system_state = SystemState(state=state, zone=zone, source=source, mode=mode)
        session.add(system_state)
        session.commit()
        app_logger.info("System state saved to database. State: %s, Zone: %s, Source: %s, Mode: %s", state, zone, source, mode)
    except Exception as error:
        app_logger.error("Error saving system state to database. Exception: %s", str(error))
    finally:
        session.close()

def log_watering_session(zone, duration, source, soil_moisture_before, mode):
    """Enregistre les détails de la session d'arrosage dans la base de données"""
    try:
        session = SessionLocal()
        watering_session = WateringSession(zone=zone, duration=duration, source=source,
                                           soil_moisture_before=soil_moisture_before, mode=mode)
        session.add(watering_session)
        session.commit()
        app_logger.info(
            "Watering session logged to database. Zone: %s, Duration: %s, Source: %s, Moisture Before: %s, Mode: %s",
            zone, duration, source, soil_moisture_before, mode)
    except Exception as error:
        app_logger.error("Error logging watering session to database. Exception: %s", str(error))
    finally:
        session.close()

def log_hourly_rain(amount):
    """ Enregistre la quantité de pluie tombée chaque heure dans la base de données """
    if amount is None:
        app_logger.warning("Attempted to log None as hourly rain")
        return  # ou définir une valeur par défaut, ex: amount = 0
    rounded_amount = round(amount, 2)  # Arrondi à deux décimales
    try:
        session = SessionLocal()
        hourly_rain = HourlyRain(amount=rounded_amount)
        session.add(hourly_rain)
        session.commit()
        app_logger.info("Hourly rain data saved to database. Amount: %s mm", rounded_amount)
    except Exception as error:
        app_logger.error("Error saving hourly rain data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_hourly_temperature(temperature):
    """ Enregistre la température chaque heure dans la base de données """
    if temperature is None:
        app_logger.warning("Attempted to log None as hourly temperature")
        return  # ou définir une valeur par défaut, ex: temperature = 20.0
    rounded_temperature = round(temperature, 2)
    try:
        session = SessionLocal()
        hourly_temperature = HourlyTemperature(temperature=rounded_temperature)
        session.add(hourly_temperature)
        session.commit()
        app_logger.info("Hourly temperature data saved to database. Temperature: %s °C", rounded_temperature)
    except Exception as error:
        app_logger.error("Error saving hourly temperature data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_hourly_wind(wind_speed):
    """ Enregistre la vitesse du vent chaque heure dans la base de données """
    if wind_speed is None:
        app_logger.warning("Attempted to log None as hourly wind speed")
        return  # ou définir une valeur par défaut, ex: wind_speed = 0
    rounded_wind_speed = round(wind_speed, 2)
    try:
        session = SessionLocal()
        hourly_wind = HourlyWind(wind_speed=rounded_wind_speed)
        session.add(hourly_wind)
        session.commit()
        app_logger.info("Hourly wind data saved to database. Wind Speed: %s km/h", rounded_wind_speed)
    except Exception as error:
        app_logger.error("Error saving hourly wind data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_hourly_sunlight(solar_radiation):
    """ Enregistre l'ensoleillement chaque heure dans la base de données """
    if solar_radiation is None:
        app_logger.warning("Attempted to log None as hourly solar radiation")
        return  # ou définir une valeur par défaut, ex: solar_radiation = 0.0
    rounded_solar_radiation = round(solar_radiation, 2)
    try:
        session = SessionLocal()
        hourly_sunlight = HourlySunlight(solar_radiation=rounded_solar_radiation)
        session.add(hourly_sunlight)
        session.commit()
        app_logger.info("Hourly sunlight data saved to database. Solar Radiation: %s W/m²", rounded_solar_radiation)
    except Exception as error:
        app_logger.error("Error saving hourly sunlight data to database. Exception: %s", str(error))
    finally:
        session.close()

def log_hourly_humidity(humidity):
    """ Enregistre l'humidité extérieure chaque heure dans la base de données """
    if humidity is None:
        app_logger.warning("Attempted to log None as hourly humidity")
        return  # ou définir une valeur par défaut, ex: humidity = 50
    rounded_humidity = round(humidity, 2)
    try:
        session = SessionLocal()
        hourly_humidity = HourlyHumidity(humidity=rounded_humidity)
        session.add(hourly_humidity)
        session.commit()
        app_logger.info("Hourly humidity data saved to database. Humidity: %s %%", rounded_humidity)
    except Exception as error:
        app_logger.error("Error saving hourly humidity data to database. Exception: %s", str(error))
    finally:
        session.close()

