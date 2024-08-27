import RPi.GPIO as GPIO
import time
import logging
import os
import Adafruit_DHT
from notifications.email_notifications import send_email

class DistanceSensor:
    def __init__(self, trigger_pin, echo_pin, max_distance, email_config):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.max_distance = max_distance
        self.time_out = max_distance * 60  # Calcul du temps maximum d'attente pour time_out
        self.email_config = email_config
        self.setup_distance_sensor()

    def setup_distance_sensor(self):
        """Configuration du capteur de distance"""
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trigger_pin, GPIO.LOW)

    def pulse_in(self, level, time_out):
        """Mesure le temps d'une impulsion sur une broche GPIO."""
        start_time = time.time()

        while GPIO.input(self.echo_pin) != level:
            if (time.time() - start_time) > time_out * 0.000001:
                return 0

        start_time = time.time()

        while GPIO.input(self.echo_pin) == level:
            if (time.time() - start_time) > time_out * 0.000001:
                return 0

        pulse_time = (time.time() - start_time) * 1000000
        return pulse_time

    def get_distance(self):
        """Obtient les résultats de mesure du module ultrasonique, avec l'unité : cm"""
        distances = []
        for _ in range(5):
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)  # 10us
            GPIO.output(self.trigger_pin, GPIO.LOW)

            ping_time = self.pulse_in(GPIO.HIGH, self.time_out)

            if ping_time == 0 or ping_time * 340.0 / 2.0 / 10000.0 > 98:
                logging.warning("Failed to read distance from sensor or distance above threshold.")
                distances.append(float('inf'))
            else:
                distance = ping_time * 340.0 / 2.0 / 10000.0
                distances.append(distance)

        if all(dist == float('inf') for dist in distances):
            logging.warning("All distance readings are invalid, using default value and sending email.")
            send_email(self.email_config, "Erreur du Capteur de Distance",
                       "Toutes les lectures de distance sont invalides, valeur par défaut utilisée.")
            return 10

        valid_distances = [dist for dist in distances if dist != float('inf')]
        if valid_distances:
            average_distance = sum(valid_distances) / len(valid_distances)
            level = 95 - average_distance
        else:
            logging.error("Sensor appears to be disconnected or malfunctioning.")
            send_email(self.email_config, "Problème de Capteur",
                       "Le capteur semble être déconnecté ou défectueux.")
            return 10

        logging.debug("Distance from sensor: %.2f cm", average_distance)
        return level

def get_cpu_temperature():
    """Récupère la température du processeur."""
    try:
        temp = os.popen("vcgencmd measure_temp").readline()
        temperature = float(temp.replace("temp=", "").replace("'C\n", ""))
        return temperature
    except Exception as e:
        logging.error(f"Erreur lors de la lecture de la température du processeur: {e}")
        return None

def get_technical_cabinet_condition_data(dht_pin):
    """Obtient la température et l'humidité de l'armoire technique à partir du capteur DHT11."""
    DHT_SENSOR = Adafruit_DHT.DHT11

    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, dht_pin)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        logging.error("Failed to retrieve data from humidity sensor")
        return None, None
