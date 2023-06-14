"""misc

Author: Ethan Hunt
Date: 2023-06-13
Version: 1.0

"""

import json
import os


def get_config(key):
    config_path = os.path.dirname(__file__)
    for _ in range(1):
        config_path = os.path.dirname(config_path)
    # TODO: Generalize this so it can accept both JSON and YAML, possibly even a two column csv/txt file
    with open(os.path.join(config_path, 'config.json'), 'r') as t:
        key_data = json.load(t)
    val = key_data.get(key)
    return val
