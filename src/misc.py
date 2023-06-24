"""misc

Author: Ethan Hunt
Date: 2023-06-13
Version: 1.0

"""

from collections import defaultdict
import csv
import json
import os


def get_config(module: str, key: str):
    config_path = os.path.dirname(__file__)
    for _ in range(1):
        config_path = os.path.dirname(config_path)
    # TODO: Generalize this so it can accept both JSON and YAML, possibly even a two column csv/txt file
    with open(os.path.join(config_path, f'{module}_config.json'), 'r') as t:
        key_data = json.load(t)
    val = key_data.get(key)
    return val


def csv_to_json(csvfile: str) -> dict:
    """
    Return a nested dictionary object from a csv where the first column is
    the key and subsequent columns are nested key:value pairs for that key
    """
    # TODO: Is there a way to verify that the first column has unique values? Process will break otherwise
    nested_dict = defaultdict(dict)

    with open(csvfile, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read the header row

        for row in reader:
            key = row[0]  # Use the first column as the key
            inner_dict = {header: value for header, value in zip(headers[1:], row[1:])}
            nested_dict[key] = inner_dict

    return nested_dict
