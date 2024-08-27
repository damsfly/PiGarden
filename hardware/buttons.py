# buttons.py
import RPi.GPIO as GPIO
import logging
import time


class ButtonController:
    def __init__(self, button_pins, button_actions, debounce_time):
        self.button_pins = button_pins
        self.button_actions = button_actions
        self.debounce_time = debounce_time
        self.last_press_time = {pin: 0 for pin in button_pins}
        try:
            self.setup_button_pins()
        except RuntimeError as e:
            logging.error("Failed to setup button pins: %s", e)

    def setup_button_pins(self):
        """ Configure les pins des boutons """
        try:
            GPIO.setmode(GPIO.BCM)
            for pin in self.button_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.button_callback, bouncetime=self.debounce_time)
        except RuntimeError as e:
            logging.error("RuntimeError during GPIO setup: %s", e)
            raise

    def button_callback(self, pin):
        """ Fonction de rappel pour gérer la pression des boutons """
        current_time = time.time()
        if current_time - self.last_press_time[pin] < self.debounce_time / 1000.0:
            return  # Ignore the button press as it's within the debounce time
        self.last_press_time[pin] = current_time

        if pin in self.button_actions:
            action = self.button_actions[pin]
            action()



"""
Dans la classe ButtonController, nous configurons les pins des boutons 
avec des résistances de tirage et attachons une détection d'événement 
pour appeler une fonction button_callback lorsque un bouton est pressé. 
La fonction button_callback recherche ensuite la fonction correspondante à appeler 
à partir d'un dictionnaire qui mappe les pins aux fonctions.
"""