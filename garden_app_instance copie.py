import logging
import signal
import threading
import time
import schedule
import RPi.GPIO as GPIO
from config import load_config
from custom_logging import setup_logger
from hardware import RelayController, DistanceSensor, ButtonController
from weather.weather_api import WeatherAPI
from data_management.database import create_database
from data_management.data_logger import log_water_level, log_system_state, log_soil_moisture


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class GardenWateringApp:
    """ Classe qui gère l'arrosage du jardin """
    watering_in_progress = False
    watering_timer = None

    def __init__(self):
        """ Initialisation des variables """

        # Load configurations from the JSON file
        self.config = load_config()

        # Configure the logger
        setup_logger()

        create_database()

        # Définitions des actions des boutons
        button_actions = {
            self.config['button_pins'][0]: self.start_tomato_watering,
            self.config['button_pins'][1]: self.start_garden_watering,
            self.config['button_pins'][2]: self.start_annex_faucet,
            self.config['button_pins'][3]: self.stop_watering,
        }

        # Initialise ButtonController avec les pins des boutons, les actions, et le temps de debounce
        self.button_controller = ButtonController(
            self.config['button_pins'],
            button_actions,
            self.config['button_debounce_time']
        )

        # Initialisation de email_notification
        email_config = {
            "email_address": self.config["email_address"],
            "email_password": self.config["email_password"],
            "smtp_server": self.config["smtp_server"],
            "smtp_port": self.config["smtp_port"],
            "recipient_address": self.config["recipient_address"]
        }

        # Initialisation du contrôleur de distance
        self.distance_sensor = DistanceSensor(
            trigger_pin=self.config['distance_sensor']['trigger_pin'],
            echo_pin=self.config['distance_sensor']['echo_pin'],
            max_distance=self.config['distance_sensor']['max_distance'],
            email_config=email_config
        )

        # Initialize relay controller
        self.relay_controller = RelayController(self.config["relay_pins"])

        self.watering_duration = self.config["watering_duration"]

        self.current_water_source = "Unknown"

        # Initialisation de WeatherAPI
        self.weather_api = WeatherAPI(
            self.config["weatherapi_api_key"],
            self.config["latitude"],
            self.config["longitude"],
            self.config["ecowitt_application_key"],
            self.config["ecowitt_api_key"],
            self.config["meteo_station_mac_adresse"],
            email_config=email_config
        )

        self.water_level = 0
        self.last_12_hour_rain = None

        # Initialiser les attributs d'état actuel
        self.current_state = None
        self.current_zone = None
        self.current_source = None

    def set_socketio_instance(self, socketio_instance):
        self.relay_controller.set_socketio_instance(socketio_instance)

    def update_system_state(self, state, zone, source, mode):
        """ Met à jour et enregistre l'état du système """
        # Attribuer des valeurs par défaut si zone ou source sont None
        if zone is None:
            zone = "Unknown"
        if source is None:
            source = "Unknown"

        if state != self.current_state or zone != self.current_zone or source != self.current_source:
            logging.info(f"Updating system state from {self.current_state} to {state}, "
                         f"zone from {self.current_zone} to {zone}, "
                         f"source from {self.current_source} to {source}, "
                         f"mode: {mode}")
            self.current_state = state
            self.current_zone = zone
            self.current_source = source
            log_system_state(state, zone, source, mode)
        else:
            logging.debug(f"No change in system state. Current state: {self.current_state}, "
                          f"Zone: {self.current_zone}, Source: {self.current_source}, Mode: {mode}")

    def send_data_to_db_hourly(self):
        """ Enregistre les données de niveau des citernes et d'humidité toutes les heures dans la base de données """
        level = self.distance_sensor.get_distance()
        tomato_moisture, garden_moisture = self.weather_api.get_soil_moisture_data()  # Obtenir l'humidité

        log_water_level(level)  # Enregistrer le niveau d'eau
        log_soil_moisture(tomato_moisture, "Tomato")  # Enregistrer l'humidité des tomates
        log_soil_moisture(garden_moisture, "Garden")  # Enregistrer l'humidité du jardin

    def start_zone_watering(self, relay_pin, duration, zone):
        logging.info(f"Démarrage du thread d'arrosage pour la zone {zone}")
        self.relay_controller.activate_relay(relay_pin)
        logging.info(f"Starting watering for {zone} zone with duration {duration} seconds.")
        time.sleep(duration)
        self.relay_controller.deactivate_relay(relay_pin)
        logging.info(f"Completed watering for {zone} zone.")
        logging.info(f"Arrêt du thread d'arrosage pour la zone {zone}")

    def calculate_watering_duration(self, moisture_level):
        if moisture_level < 30:
            return 60  # Durée en secondes 600
        elif moisture_level < 50:
            return 42  # Durée en secondes 420
        elif moisture_level < 62:
            return 24  # Durée en secondes 240
        else:
            return 0  # Pas besoin d'arroser

    def generic_watering(self, duration, pins, initiated_manually=False):
        """ Défini si l'arrosage est en cours """
        if not self.watering_in_progress:
            self.watering_in_progress = True
            level = self.distance_sensor.get_distance()
            self.activate_water_source(level)

            self.update_system_state("Watering", self.current_zone, self.current_water_source,
                                     "Automatic" if not initiated_manually else "Manual")

            for pin in pins:
                self.relay_controller.activate_relay(pin)

            self.watering_timer = threading.Timer(duration, lambda: self.turn_off_relays(self.current_zone, False))
            self.watering_timer.start()
            self.watering_timer.join()

            # if not initiated_manually:
            #     self.update_system_state("Stopped", self.current_zone, self.current_water_source, "Automatic")

            # Enregistrer l'état après l'arrêt de l'arrosage
            self.update_system_state("Stopped", self.current_zone, self.current_water_source,
                                     "Automatic" if not initiated_manually else "Manual")

            self.watering_in_progress = False
            logging.info("Watering completed.")
        else:
            logging.warning("Watering already in progress. Cannot start watering.")

    def watering_thread(self, watering_function):
        """ Contrôle si l'arrosage est en cours """
        if not self.watering_in_progress:
            watering_function()

    def interrupt_handler(self, signum, frame):
        """ Gère les interruptions """
        logging.info("Watering stopped by interrupt signal.")
        self.stop_watering_process()

    def activate_water_source(self, level):
        """ Défini quelle source d'eau utiliser pour l'arrosage """
        water_source = "Water tank" if level > 15 else "city"
        if water_source == "Water tank":
            logging.info("Using water tank and starting pump...")
            self.relay_controller.activate_relay(18)
            self.relay_controller.activate_relay(23)
        else:
            logging.info("Using city water network")
            self.relay_controller.activate_relay(24)
        return water_source

    def turn_off_relays(self, zone="General", manual_stop=False):
        """ Arrête tous les relais qui sont actifs """
        for pin in self.config["relay_pins"]:
            self.relay_controller.deactivate_relay(pin)
        if not manual_stop:
            logging.info(f"Watering stopped for zone: {zone}")

    def scheduled_watering(self):
        """Commence l'arrosage à des heures définies en fonction de l'humidité du sol."""
        if self.watering_in_progress:
            logging.info("Watering already in progress. Skipping scheduled watering.")
            return

        self.watering_in_progress = True
        tomato_moisture, garden_moisture = self.weather_api.get_soil_moisture_data()

        tomato_duration = self.calculate_watering_duration(tomato_moisture)
        garden_duration = self.calculate_watering_duration(garden_moisture)

        zones_to_water = []
        if tomato_duration > 0:
            zones_to_water.append("Tomato")
        if garden_duration > 0:
            zones_to_water.append("Garden")

        # Détermine les zones à arroser pour la mise à jour de l'état
        zones_str = ", ".join(zones_to_water) if zones_to_water else "No zones"

        if zones_to_water:
            level = self.distance_sensor.get_distance()
            self.current_water_source = self.activate_water_source(level)

            self.current_zone = zones_str

            # Mise à jour de l'état avant de démarrer l'arrosage avec les zones déterminées
            self.update_system_state("Watering", zones_str, self.current_water_source, "Automatic")

            threads = []
            if tomato_duration > 0:
                tomato_thread = threading.Thread(target=self.start_zone_watering,
                                                 args=(self.config["tomato_relay_pin"], tomato_duration, "Tomato"))
                threads.append(tomato_thread)

            if garden_duration > 0:
                garden_thread = threading.Thread(target=self.start_zone_watering,
                                                 args=(self.config["garden_relay_pin"], garden_duration, "Garden"))
                threads.append(garden_thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            self.turn_off_relays()  # S'assure que l'état "Stopped" est géré ici

        else:
            logging.info("No watering needed based on soil moisture levels.")

        self.watering_in_progress = False
        self.update_system_state("Stopped", self.current_zone, self.current_water_source, "Automatic")

    def start_tomato_watering(self):
        self.start_watering(self.config["tomato_relay_pin"], self.config["tomato_watering_duration"], "Tomato")

    def start_garden_watering(self):
        self.start_watering(self.config["garden_relay_pin"], self.config["garden_watering_duration"], "Garden")

    def start_annex_faucet(self):
        self.start_watering(self.config["annex_relay_pin"], self.config["annex_watering_duration"], "Annex")

    def start_watering(self, relay_pin, duration, zone_name):
        """Démarre l'arrosage pour une zone spécifique."""
        if self.can_start_watering():
            logging.info(f"Starting manual watering for {zone_name} zone.")
            level = self.distance_sensor.get_distance()
            self.current_water_source = self.activate_water_source(level)
            log_water_level(level)
            self.update_system_state("Watering", zone_name, self.current_water_source, True)
            self.relay_controller.activate_relay(relay_pin)
            self.start_watering_timer(duration, zone_name)

    def can_start_watering(self):
        """Vérifie si un nouvel arrosage peut être démarré."""
        return not self.watering_in_progress

    def start_watering_timer(self, duration, zone):
        """Démarre un timer pour l'arrosage et gère l'état."""
        self.watering_in_progress = True
        self.current_zone = zone
        logging.info(f"Timer started for {zone} zone for {duration} seconds.")
        threading.Timer(duration, lambda: self.stop_watering_process(zone)).start()

    # Stop watering
    def stop_watering(self):
        """
            Réceptionne l'activation du bouton d'arrêt de l'arrosage en cours
            et déclenche la procédure d'arrêt
        """
        if self.watering_in_progress:
            self.update_system_state("Stopped", self.current_zone, self.current_water_source, "Manual")
            logging.info("Arrêt manuel de l'arrosage")
            self.stop_watering_process(self.current_zone, manual_stop=True)
        else:
            logging.info("Aucun arrosage en cours. Impossible d'arrêter.")

    def stop_watering_process(self, zone="General", manual_stop=False):
        """ Active la procédure d'arrêt de l'arrosage en cours """
        if self.watering_timer:
            self.watering_timer.cancel()
        self.turn_off_relays(zone, manual_stop)
        if manual_stop:
            # Enregistrer l'état seulement si c'est un arrêt manuel
            self.update_system_state("Stopped", zone, self.current_water_source, "Manual")
            logging.info(f"Manual stop of watering for zone: {zone}")
        else:
            # Ajouter un log pour l'arrêt automatique
            self.update_system_state("Stopped", zone, self.current_water_source, "Automatic")
            logging.info(f"Automatic stop of watering for zone: {zone}")
        self.watering_in_progress = False
        level = self.distance_sensor.get_distance()  # Enregistrez le niveau actuel
        log_water_level(level)

    def run(self):
        """
            Fonction principale
            qui va déclencher l'arrosage à heures fixes
            et activer l'envoi régulier du niveau d'eau des citernes dans la BD
        """
        # Planifier l'enregistrement du niveau d'eau dans la base de données toutes les heures à 30 minutes
        schedule.every().hour.at(":30").do(self.send_data_to_db_hourly)

        # Planifier l'arrosage pour s'exécuter à 8h et 20h tous les jours
        schedule.every().day.at("22:02").do(self.scheduled_watering)
        schedule.every().day.at("22:04").do(self.scheduled_watering)

        while True:
            # Exécuter les tâches planifiées
            schedule.run_pending()
            # Pause pour réduire l'utilisation du CPU
            time.sleep(0.1)

    def destroy(self):
        logging.info("Destroying application...")
        GPIO.cleanup()


# Création de l'instance de GardenWateringApp
garden_app = GardenWateringApp()