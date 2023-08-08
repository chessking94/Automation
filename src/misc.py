from collections import defaultdict
import csv
import json
import logging
import os
import traceback
import yaml

from . import VALID_DELIMS


def get_config(key: str, config_file: str = None) -> str:
    """Return a key value from the library configuration file

    Parameters
    ----------
    key : str
        Name of key to use
    config_file : str, optional (default None)
        Custom full path of a configuration file, will use the environment variable CONFIGFILE if not provided

    Returns
    -------
    str : The associated value for 'key'

    Raises
    ------
    RuntimeError
        If no 'config_file' is provided and environment variable "CONFIGFILE" does not exist
    FileNotFoundError
        If 'config_file' file does not exist

    """
    if config_file is None:
        if os.getenv('CONFIGFILE') is not None:
            config_file = os.getenv('CONFIGFILE')
        else:
            raise RuntimeError('unable to determine config file')

    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"config file '{config_file}' does not exist")

    config_type = os.path.splitext(config_file)[1].lower().replace('.', '')
    if config_type not in ['json', 'yaml']:
        raise NotImplementedError(f"config file '{os.path.basename(config_file)}' not supported")

    with open(config_file, 'r') as cf:
        if config_type == 'json':
            key_data = json.load(cf)
        elif config_type == 'yaml':
            key_data = yaml.safe_load(cf)
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


def log_exception(exctype, value, tb):
    """Log exception by using the root logger

    Taken from https://stackoverflow.com/a/48643567

    Parameters
    ----------
    exctype : exception_type
    value : NameError
    tb : traceback

    """

    write_val = {
        'type': str(exctype),
        'description': str(value),
        'traceback': str(traceback.format_tb(tb, 10))
    }
    logging.critical(str(write_val))
