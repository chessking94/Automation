"""misc

Author: Ethan Hunt
Date: 2023-06-13
Version: 1.0

"""

from collections import defaultdict
import csv
import json
import os

from .constants import VALID_DELIMS as VALID_DELIMS


def get_config(module: str, key: str, path_override: str = None) -> str:
    # TODO: Would it make more sense to have the config path be a parameter somewhere? Global variable? Config parameter?
    if path_override is None:
        config_path = os.path.dirname(__file__)
        for _ in range(1):  # predefined to be one directory above the location of this file
            config_path = os.path.dirname(config_path)
    else:
        config_path = path_override
    # TODO: Generalize this so it can accept both JSON and YAML, possibly even a two column csv/txt file
    with open(os.path.join(config_path, f'{module}_config.json'), 'r') as t:
        key_data = json.load(t)
    val = key_data.get(key)
    return val


def csv_to_json(csvfile: str, delimiter: str = ',') -> dict:
    """
    Return a nested dictionary object from a csv where the first column is
    the key and subsequent columns are nested key:value pairs for that key
    """
    if delimiter not in VALID_DELIMS:
        raise NotImplementedError(f"invalid delimiter: {delimiter}")

    nested_dict = defaultdict(dict)
    key_set = set()

    with open(csvfile, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=delimiter)
        headers = next(reader)  # Read the header row

        for row in reader:
            key = row[0]  # Use the first column as the key
            if key in key_set:
                raise ValueError(f"duplicate key '{key}' present")
            key_set.add(key)

            inner_dict = {header: value for header, value in zip(headers[1:], row[1:])}
            nested_dict[key] = inner_dict

    return nested_dict
