from collections import defaultdict
import csv
import datetime as dt
import json
import logging
import os
from pathlib import Path
import re
import sys
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
        'type': re.sub(r'<|>', '', str(exctype)),  # remove < and > since it messes up converting to HTML for potential email notifications
        'description': str(value),
        'traceback': str(traceback.format_tb(tb, 10))
    }
    logging.critical(str(write_val))


def initiate_logging(script_name: str, config_file: str) -> str:
    """Initiate standard logging

    Set-up base logging configuration

    Parameters
    ----------
    script_name : str
        Name of the script logging is being initiated from. Can be called via 'pathlib.Path(__file__).stem'
    config_file : str
        Full path of a configuration file for the script calling this function

    Returns
    -------
    str : Full path of the log file being written to

    """
    script_name = Path(__file__).stem
    log_root = get_config('logRoot', config_file)

    dte = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    log_name = f'{script_name}_{dte}.log'
    log_file = os.path.join(log_root, log_name)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s\t%(funcName)s\t%(levelname)s\t%(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    sys.excepthook = log_exception  # force unhandled exceptions to write to the log file

    return log_file


def list_to_html(data: list, has_header: bool = True) -> str:
    """Convert a list to an HTML table

    Based on https://stackoverflow.com/a/52785746

    Parameters
    ----------
    data : list
        The list to convert to a table
    has_header : bool, optional (default True)
        An indicator if the first element of the list is a header

    Returns
    -------
    str : The requested HTML table

    """

    html = '<table border="1">'
    for i, row in enumerate(data):
        if has_header and i == 0:
            tag = 'th'
        else:
            tag = 'td'
        tds = ''.join('<{}>{}</{}>'.format(tag, cell, tag) for cell in row)
        html += '<tr>{}</tr>'.format(tds)
    html += '</table>'

    return html
