import sys
import json
import threading
import logging
import time
from flask import Flask, render_template, jsonify
from app.flask_functions import (
    get_water_level_data,
    get_moisture_data,
    get_system_state,
    get_last_rain_data as fetch_last_rain_data,
    get_water_level_chart_data,
    get_watering_sessions,
    get_yearly_data,
    get_technical_cabinet_data
)
from garden_app_instance import GardenWateringApp
from custom_logging import setup_logger

sys.path.append('/home/PiGardenV6/app')

app = Flask(__name__, static_folder='app/static', template_folder='app/templates')

# Charger le fichier de configuration
with open('/home/PiGardenV6/config/config.json') as config_file:
    config = json.load(config_file)

# Initialisation de GardenWateringApp avec l'instance app Flask
garden_app = GardenWateringApp()

# setup_logger()
flask_logger = setup_logger('log_flask_garden.log', 'flask_app')
app.logger.handlers = flask_logger.handlers
app.logger.setLevel(flask_logger.level)

@app.route('/')
def index():
    water_level_data = get_water_level_data()
    tomato_moisture = get_moisture_data("Tomato")
    garden_moisture = get_moisture_data("Garden")
    system_state = get_system_state()
    last_rain_data = fetch_last_rain_data()
    return render_template('index.html', water_level=water_level_data, tomato_moisture=tomato_moisture,
                           garden_moisture=garden_moisture, system_state=system_state, last_rain_data=last_rain_data)

@app.route('/water-garden')
def water_garden():
    success = garden_app.start_garden_watering()
    return jsonify({"message": "Arrosage du jardin en cours"})

@app.route('/water-tomatoes')
def water_tomatoes():
    success = garden_app.start_tomato_watering()
    return jsonify({"message": "Arrosage des tomates en cours"})

@app.route('/activate-faucet')
def activate_faucet():
    success = garden_app.start_annex_faucet()
    return jsonify({"message": "Activation du robinet auxiliaire en cours"})

@app.route('/stop-watering')
def stop_watering():
    success = garden_app.stop_all_watering()
    return jsonify({"message": "Tous les arrosages ont été arrêtés"})

@app.route('/get-water-level')
def get_water_level():
    water_level_data = get_water_level_data()
    return jsonify({"water_level": water_level_data})

@app.route('/get-last-rain-data')
def get_last_rain_data():
    rain_data = fetch_last_rain_data()
    return jsonify({"rain_data": rain_data})

@app.route('/water-level-chart-data')
def water_level_chart_data():
    water_level_data = get_water_level_chart_data()
    if not water_level_data:
        return jsonify({'error': 'No data available'}), 404
    return jsonify(water_level_data)

@app.route('/watering-history')
def watering_history():
    watering_sessions = get_watering_sessions()
    return render_template('watering_history.html', watering_sessions=watering_sessions)

@app.route('/yearly-graph')
def yearly_graph():
    data = get_yearly_data()
    return render_template('yearly_graph.html', data=data)

@app.route('/technical-cabinet-temperature')
def technical_cabinet_temperature():
    data = get_technical_cabinet_data()
    return render_template('technical_cabinet_temperature.html', data=data)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    stop_application()
    return 'Server shutting down...'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)