"""misc

Author: Ethan Hunt
Creation Date: 2023-06-13

"""

from collections import defaultdict
import csv
import json
import os

from . import VALID_DELIMS


def get_config(key: str, path_override: str = None, name_override: str = 'config.json') -> str:
    """Return a key value from the library configuration file

    Parameters
    ----------
    key : str
        Name of key to use
    path_override : str, optional (default None)
        Custom location of configuration file, will use the parent directory of this file if not provided
    name_override : str, optional (default "config.json")
        Name of configuration file

    Returns
    -------
    str : The associated value for 'key'

    Raises
    ------
    RuntimeError
        If no 'path_override' is provided and environment variable "CONFIGPATH" does not exist
    FileNotFoundError
        If 'path_override' directory does not exist
        If 'name_override' file does not exist


    TODO
    ----
    Generalize so it can accept JSON, YAML, and a two column csv file

    """
    if path_override is None:
        if os.getenv('CONFIGPATH') is not None:
            config_path = os.getenv('CONFIGPATH')
        else:
            raise RuntimeError('unable to determine config path')
    else:
        config_path = path_override

    if name_override is None:
        config_name = 'config.json'
    else:
        config_name = name_override

    if not os.path.isdir(config_path):
        raise FileNotFoundError(f"path '{config_path}' does not exist")

    config_file = os.path.join(config_path, config_name)
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"config file '{config_file}' does not exist")

    with open(config_file, 'r') as cf:
        key_data = json.load(cf)
    val = key_data.get(key)
    return val


def csv_to_json(csvfile: str, delimiter: str = ',') -> dict:
    """Convert a csv file into a dictionary object

    Return a nested dictionary object from a csv where the first column is
    the key and subsequent columns are nested key:value pairs for that key

    Parameters
    ----------
    csvfile : str
        Full path of csv file to read
    delimiter : str, optional (default ",")
        Field delimiter used in the csv file

    Returns
    -------
    dict : Nested dictionary where each level is grouped by unique values in the first column of the csv

    Raises
    ------
    NotImplementedError
        If delimiter is not in a validation list
    ValueError
        If the values in the first column of the csv are not unique

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
