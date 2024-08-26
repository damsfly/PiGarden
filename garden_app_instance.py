import logging
import signal
import time
import schedule
import RPi.GPIO as GPIO
import threading
from config import load_config
from custom_logging import setup_logger
from hardware import RelayController, DistanceSensor, ButtonController
from weather.weather_api import WeatherAPI
from data_management.database import create_database
from data_management.data_logger import (
    log_water_level, log_system_state, log_soil_moisture, log_watering_session, log_hourly_rain,
    log_hourly_temperature, log_hourly_wind, log_hourly_sunlight, log_rain_forecast, log_hourly_humidity,
    log_last_12h_rain, log_cpu_temperature, log_technical_cabinet_conditions
)
from hardware.sensors import get_cpu_temperature, get_technical_cabinet_condition_data
from notifications.email_notifications import send_email

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class GardenWateringApp:
    """ Classe qui gère l'arrosage du jardin """
    watering_in_progress = False
    manual_watering_in_progress = False

    def __init__(self):
        """ Initialisation des variables """
        self.config = load_config()
        self.app_logger = setup_logger('log_watering_garden.log', 'garden_app')
        create_database()
        self.watering_in_progress = False
        self.manual_watering_in_progress = False
        self.last_manual_watering_time = None
        self.manual_watering_cooldown = 300  # Temps d'attente entre deux arrosages manuels en secondes

        button_actions = {
            self.config['button_pins'][0]: self.start_tomato_watering,
            self.config['button_pins'][1]: self.start_garden_watering,
            self.config['button_pins'][2]: self.start_annex_faucet,
            self.config['button_pins'][3]: self.stop_watering,  # Mise à jour ici
        }
        self.button_controller = ButtonController(
            self.config['button_pins'],
            button_actions,
            self.config['button_debounce_time']
        )

        self.email_config = {
            "email_address": self.config["email_address"],
            "email_password": self.config["email_password"],
            "smtp_server": self.config["smtp_server"],
            "smtp_port": self.config["smtp_port"],
            "recipient_address": self.config["recipient_address"]
        }

        self.distance_sensor = DistanceSensor(
            trigger_pin=self.config['distance_sensor']['trigger_pin'],
            echo_pin=self.config['distance_sensor']['echo_pin'],
            max_distance=self.config['distance_sensor']['max_distance'],
            email_config=self.email_config
        )

        self.dht_pin = self.config['dht11_pin']
        self.relay_controller = RelayController(self.config["relay_pins"])
        self.weather_api = WeatherAPI(
            self.config["weatherapi_api_key"],
            self.config["latitude"],
            self.config["longitude"],
            self.config["ecowitt_application_key"],
            self.config["ecowitt_api_key"],
            self.config["meteo_station_mac_adresse"],
            email_config=self.email_config
        )

        self.current_water_source = "Unknown"
        self.current_state = None
        self.current_zone = None
        self.current_source = None

        signal.signal(signal.SIGINT, self.interrupt_handler)

        self.lock = threading.Lock()

    def update_system_state(self, state, zone, source, mode):
        """ Met à jour et enregistre l'état du système """
        if zone is None:
            zone = "Unknown"
        if source is None:
            source = "Unknown"

        if state != self.current_state or zone != self.current_zone or source != self.current_source:
            self.app_logger.info(f"Updating system state from {self.current_state} to {state}, "
                         f"zone from {self.current_zone} to {zone}, "
                         f"source from {self.current_source} to {source}, "
                         f"mode: {mode}")
            self.current_state = state
            self.current_zone = zone
            self.current_source = source
            log_system_state(state, zone, source, mode)
        else:
            self.app_logger.debug(f"No change in system state. Current state: {self.current_state}, "
                          f"Zone: {self.current_zone}, Source: {self.current_source}, Mode: {mode}")

    def _activate_relay(self, relay_pin):
        """ Active un relais et log l'action """
        try:
            self.relay_controller.activate_relay(relay_pin)
            self.app_logger.info(f"Activating relay {relay_pin}")
        except Exception as e:
            self.app_logger.error(f"Failed to activate relay {relay_pin}: {e}")

    def _deactivate_relay(self, relay_pin):
        """ Désactive un relais et log l'action """
        try:
            self.relay_controller.deactivate_relay(relay_pin)
            self.app_logger.info(f"Deactivating relay {relay_pin}")
        except Exception as e:
            self.app_logger.error(f"Failed to deactivate relay {relay_pin}: {e}")

    def deactivate_all_relays(self):
        """ Désactive tous les relais activés pendant l'arrosage """
        for pin in self.config["relay_pins"]:
            self._deactivate_relay(pin)

    def send_data_to_db_hourly(self):
        """ Enregistre les données de niveau des citernes, d'humidité, etc. toutes les heures dans la base de données """
        try:
            level = self.distance_sensor.get_distance()
            tomato_moisture, garden_moisture = self.weather_api.get_soil_moisture_data()
            last_hour_rain = self.weather_api.get_last_1_hour_rain_data()
            last_hour_temperature = self.weather_api.get_last_1_hour_temperature_data()
            last_hour_wind_speed = self.weather_api.get_last_1_hour_wind_data()
            last_hour_sun_radiation = self.weather_api.get_last_1_hour_sun_data()
            last_hour_humidity = self.weather_api.get_last_1_hour_humidity_data()

            log_water_level(level)
            log_soil_moisture(tomato_moisture, "Tomato")
            log_soil_moisture(garden_moisture, "Garden")
            log_hourly_rain(last_hour_rain)
            log_hourly_temperature(last_hour_temperature)
            log_hourly_wind(last_hour_wind_speed)
            log_hourly_sunlight(last_hour_sun_radiation)
            log_hourly_humidity(last_hour_humidity)

            cpu_temp = get_cpu_temperature()
            log_cpu_temperature(cpu_temp)

            # Check CPU temperature and send alert if it exceeds 70°C
            if cpu_temp and cpu_temp > 70:
                subject = "Alerte: Température CPU élevée"
                body = f"La température du CPU a dépassé 70°C. Température actuelle: {cpu_temp}°C"
                send_email(self.email_config, subject, body)
                self.app_logger.warning("CPU temperature exceeded 70°C. Alert email sent.")

            ambient_temp, ambient_humidity = get_technical_cabinet_condition_data(self.dht_pin)
            log_technical_cabinet_conditions(ambient_temp, ambient_humidity)
        except Exception as e:
            self.app_logger.error(f"Error in send_data_to_db_hourly: {e}")

    def calculate_watering_duration(self, moisture_level):
        if moisture_level < 30:
            return 600
        elif moisture_level < 50:
            return 420
        elif moisture_level < 62:
            return 240
        else:
            return 0

    def select_water_source(self):
        """ Sélectionne la source d'eau en fonction du niveau des citernes """
        level = self.distance_sensor.get_distance()
        log_water_level(level)
        if level >= self.config['minimum_water_level']:
            self.relay_controller.activate_relay(self.config['pump_relay_pin'])
            source = "pump"
        else:
            self.relay_controller.activate_relay(self.config['city_water_relay_pin'])
            source = "city_water"
        return source

    def deactivate_water_source(self, source):
        """ Désactive la source d'eau utilisée """
        if source == "pump":
            self.relay_controller.deactivate_relay(self.config['pump_relay_pin'])
        elif source == "city_water":
            self.relay_controller.deactivate_relay(self.config['city_water_relay_pin'])

    def water_tomatoes(self):
        """ Arrose les tomates si nécessaire """
        tomato_moisture = self.weather_api.get_soil_moisture_data()[0]
        if tomato_moisture >= 62:
            self.app_logger.info("No watering needed for tomatoes, soil moisture is sufficient.")
            return

        duration = self.calculate_watering_duration(tomato_moisture)
        source = self.select_water_source()
        self.relay_controller.activate_relay(self.config['tomato_relay_pin'])
        self.update_system_state("Watering", "Tomatoes", source, "Automatic")
        self.app_logger.info(f"Starting to water tomatoes for {duration} seconds using {source}.")
        time.sleep(duration)
        self.relay_controller.deactivate_relay(self.config['tomato_relay_pin'])
        self.app_logger.info("Finished watering tomatoes.")
        self.deactivate_water_source(source)
        log_watering_session("tomatoes", duration, source, tomato_moisture, "Automatic")

    def water_garden(self):
        """ Arrose le jardin si nécessaire """
        garden_moisture = self.weather_api.get_soil_moisture_data()[1]
        if garden_moisture >= 62:
            self.app_logger.info("No watering needed for garden, soil moisture is sufficient.")
            return

        duration = self.calculate_watering_duration(garden_moisture)
        source = self.select_water_source()
        self.relay_controller.activate_relay(self.config['garden_relay_pin'])
        self.update_system_state("Watering", "Garden", source, "Automatic")
        self.app_logger.info(f"Starting to water garden for {duration} seconds using {source}.")
        time.sleep(duration)
        self.relay_controller.deactivate_relay(self.config['garden_relay_pin'])
        self.app_logger.info("Finished watering garden.")
        self.deactivate_water_source(source)
        log_watering_session("garden", duration, source, garden_moisture, "Automatic")

    def scheduled_watering(self):
        """ Commence l'arrosage à des heures définies en fonction de l'humidité du sol """
        if self.watering_in_progress or self.manual_watering_in_progress:
            self.app_logger.info("Watering already in progress. Skipping scheduled watering.")
            return

        self.watering_in_progress = True

        rain_forecast = self.weather_api.get_next_12_hour_rain_data()
        log_rain_forecast(rain_forecast)

        last_12h_rain = self.weather_api.get_last_12_hour_rain_data()
        log_last_12h_rain(last_12h_rain)

        self.water_tomatoes()
        self.water_garden()

        self.watering_in_progress = False
        self.update_system_state("Stopped", "All", self.current_water_source, "Automatic")
        self.app_logger.info("Scheduled watering completed.")

    def start_tomato_watering(self):
        """ Démarre l'arrosage manuel pour les tomates """
        self.start_watering(self.config["tomato_relay_pin"], self.config["tomato_watering_duration"], "Tomato")

    def start_garden_watering(self):
        """ Démarre l'arrosage manuel pour le jardin """
        self.start_watering(self.config["garden_relay_pin"], self.config["garden_watering_duration"], "Garden")

    def start_annex_faucet(self):
        """ Démarre l'arrosage manuel pour le robinet annexe """
        self.start_watering(self.config["annex_relay_pin"], self.config["annex_watering_duration"], "Annex")

    def start_watering(self, relay_pin, duration, zone_name):
        """ Démarre l'arrosage pour une zone spécifique """
        current_time = time.time()
        with self.lock:
            if self.can_start_manual_watering():
                if self.last_manual_watering_time and (
                        current_time - self.last_manual_watering_time) < self.manual_watering_cooldown:
                    self.app_logger.info(
                        f"Cannot start manual watering for {zone_name} zone. Please wait for the cooldown period.")
                    return

                self.manual_watering_in_progress = True
                try:
                    level = self.distance_sensor.get_distance()
                    self.current_water_source = self.select_water_source()
                    self.update_system_state("Watering", zone_name, self.current_water_source, "Manual")
                    self._activate_relay(relay_pin)
                    self.app_logger.info(f"Starting manual watering for {zone_name} zone for {duration} seconds.")
                    time.sleep(duration)
                except Exception as e:
                    self.app_logger.error(f"Error during watering in {zone_name}: {e}")
                finally:
                    self._deactivate_relay(relay_pin)
                    self.manual_watering_in_progress = False
                    self.deactivate_water_source(self.current_water_source)
                    self.update_system_state("Stopped", zone_name, self.current_water_source, "Manual")
                    log_watering_session(zone_name, duration, self.current_water_source, None, "Manual")
                    self.last_manual_watering_time = time.time()
            else:
                self.app_logger.info("Watering already in progress. Skipping manual watering.")

    def can_start_manual_watering(self):
        """ Vérifie si un nouvel arrosage manuel peut être démarré """
        with self.lock:
            return not self.watering_in_progress and not self.manual_watering_in_progress

    def stop_watering(self):
        """ Stoppe tous les arrosages et désactive tous les relais """
        with self.lock:
            if self.watering_in_progress or self.manual_watering_in_progress:
                self.app_logger.info("Stopping all watering actions.")
                self.watering_in_progress = False
                self.manual_watering_in_progress = False
                self.deactivate_all_relays()
                self.update_system_state("Stopped", "All", self.current_water_source, "Manual")
                self.app_logger.info("All watering stopped.")
            else:
                self.app_logger.info("No watering action in progress to stop.")

    def interrupt_handler(self, signum, frame):
        """ Gère les interruptions """
        self.app_logger.info("Watering stopped by interrupt signal.")
        self.stop_watering()

    def run(self):
        """ Fonction principale pour déclencher l'arrosage à heures fixes et enregistrer le niveau d'eau """
        schedule.every().hour.at(":00").do(self.send_data_to_db_hourly)
        schedule.every().day.at("08:00").do(self.scheduled_watering)
        schedule.every().day.at("20:00").do(self.scheduled_watering)
        schedule.every().day.at("00:00").do(self.weather_api.reset_reported_errors)  # Réinitialise les erreurs à minuit

        while True:
            schedule.run_pending()
            time.sleep(1)

    def destroy(self):
        self.app_logger.info("Destroying application...")
        self.stop_watering()  # Assurez-vous que tous les arrosages sont arrêtés
        GPIO.cleanup()


if __name__ == "__main__":
    garden_app = GardenWateringApp()
    try:
        garden_app.run()
    except KeyboardInterrupt:
        garden_app.destroy()
