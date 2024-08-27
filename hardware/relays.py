import RPi.GPIO as GPIO
import logging

class RelayController:
    def __init__(self, relay_pins):
        self.relay_pins = relay_pins
        # GPIO.setmode(GPIO.BCM)
        self.setup_relay_pins()

    def setup_relay_pins(self):
        """ Définition des pins des relais comme sorties et mise à l'état bas (off). """
        GPIO.setup(self.relay_pins, GPIO.OUT, initial=GPIO.LOW)

    def activate_relay(self, pin):
        """ Active un relais spécifique. """
        logging.info(f"Activation du relais {pin}")
        GPIO.output(pin, GPIO.HIGH)

    def deactivate_relay(self, pin):
        """ Désactive un relais spécifique. """
        logging.info(f"Désactivation du relais {pin}")
        GPIO.output(pin, GPIO.LOW)
