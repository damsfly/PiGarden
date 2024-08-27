import json
import os


def load_config():
    # Get the absolute path to the directory where this script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Combine the script directory with the relative path to form an absolute path to config.json
    config_path = os.path.join(script_dir, "config.json")

    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)
