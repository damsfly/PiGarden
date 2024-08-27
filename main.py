###############################################################################
# Filename    : main.py
# Version     : 3.0
# Description : Automation d'arrosage pour jardin extérieur sur Raspberry Pi 4b
# Author      : Fleury Damien
# modification: 2023/12/08
###############################################################################
"""
Ce programme gère l'arrosage du jardin et de la serre (les tomates)
en contrôlant le niveau d'eau des citernes et le taux d'hygrométrie de la terre.
Les données sont enregistrées dans une base de données. Un Front-end permet de contrôler
le tout via une application sur smartphone en exploitant une API.
L'arrosage est planifié pour se déclencher deux fois par jour, selon les conditions suivantes :
-Si le taux d'humidité de la terre des tomates est supérieur ou égal à 62%, l'arrosage de la serre n'a pas lieu.
-Si le taux d'humidité de la terre du jardin est supérieur ou égal à 62%, l'arrosage du jardin n'a pas lieu.
-Pour les deux zones, la durée d'arrosage est calculée en fonction du taux d'humidité de la terre.
Si les citernes ne sont pas assez remplies, le réseau d'eau est utilisé.
S'il y a un problème avec l'API qui obtient le taux d'hygrométrie de la terre, un e-mail est envoyé.
Ce programme contrôle un Raspberry Pi 4b qui commande des électrovannes, une pompe
et un capteur de distance à ultrasons.
4 boutons permettent d'arroser le jardin, arroser les tomates, activer l'eau dans un robinet et
mettre fin à l'arrosage.
L'application sur Iphone peut contrôler le Raspberry avec les mêmes fonctions
que les boutons physiques. L'état du système (arrosage en cours, quelle zone, depuis quelle source d'eau) et
le niveau d'eau des citernes est monitoré.
*** toutes les fonctionnalités sont ok ! ***
"""

import RPi.GPIO as GPIO
from garden_app_instance import GardenWateringApp


garden_app = GardenWateringApp()

if __name__ == "__main__":
    print("Démarrage du programme...")
    print("*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*")
    print("* Presser Ctrl-C pour mettre fin au programme     *")
    print("*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*")
    print("\n")
    try:
        garden_app.run()

    except KeyboardInterrupt:
        print("\nInterruption détectée. Arrêt du programme...")
    finally:
        garden_app.destroy()
        GPIO.cleanup()
