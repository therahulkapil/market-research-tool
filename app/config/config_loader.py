import yaml
import logging

CONFIG_FILE = "app/prompt_config.yaml"
PROMPT_CONFIG = {}

def load_config():
    global PROMPT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as file:
            PROMPT_CONFIG = yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file '{CONFIG_FILE}' not found.")
        PROMPT_CONFIG = {'topics': {}}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML: {e}")
        PROMPT_CONFIG = {'topics': {}}
