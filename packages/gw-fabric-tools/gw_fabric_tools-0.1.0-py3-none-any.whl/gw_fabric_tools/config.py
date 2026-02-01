import json

CONFIG_FILE_DEFAULT = ".fab-vars.json"


def load_config(env: str, *, config_file: str = CONFIG_FILE_DEFAULT) -> dict:
    with open(config_file) as f:
        return json.load(f)[env]
