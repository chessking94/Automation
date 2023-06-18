"""fileproc

Author: Ethan Hunt
Date: 2023-06-18
Version: 1.0

"""

import csv
import datetime as dt
import logging
import os
import tempfile
import shutil

from .constants import NL as NL
from .misc import get_config as get_config

# TODO: Mass move files from one location to another? Perhaps too general and shutil is good enough


class monitoring_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
    DELIM = get_config(MODULE_NAME, 'referenceDelimiter')


class monitoring:
    def __init__(self, path):
        self.path = path
        self.error = None
        self.last_review_time = self._processtime(readwrite='r')
        self.manual_review = False

        if self._validate() is not None:
            logging.critical(self.error)

    def _validate(self) -> str:
        if not os.path.isdir(self.path):
            self.error = f'Path does not exist|{self.path}'

        if monitoring_constants.DELIM in self.path:
            self.error = f'Path contains referenceDelimiter|{self.path}'

        return self.error

    def _processtime(self, readwrite: str = 'r', dt_string: str = None) -> dt.datetime:
        valid_readwrite = ['r', 'w']
        if readwrite not in valid_readwrite:
            raise ValueError(f"Invalid parameter 'readwrite': {readwrite}")

        dt_format = '%Y-%m-%d %H:%M:%S'
        dt_format_validated = True
        time_val = None
        try:
            time_val = dt.datetime.strptime(dt_string, dt_format)
        except (TypeError, ValueError):
            dt_format_validated = False

        if dt_format_validated:
            return time_val

        key_column = 'Path'
        dt_column = 'LastMonitorTime'
        reference_file = get_config(monitoring_constants.MODULE_NAME, 'referenceFile')
        if not os.path.isfile(reference_file):
            header_row = f'{key_column}{monitoring_constants.DELIM}{dt_column}{NL}'
            with open(file=reference_file, mode='w', encoding='utf-8') as f:
                f.write(header_row)

        time_val = None
        if readwrite == 'r':
            with open(reference_file, 'r') as ref_file:
                reader = csv.DictReader(ref_file)
                for row in reader:
                    if row[key_column] == self.path:
                        last_dt = row[dt_column]
                        time_val = dt.datetime.strptime(last_dt, dt_format)
                        break
            if time_val is None:
                time_val = dt.datetime(1970, 1, 1)
        else:
            logging.critical('going to update file')
            temp_file_path = tempfile.NamedTemporaryFile(delete=False).name
            with open(reference_file, 'r', newline='') as reader_file, open(temp_file_path, 'w', newline='') as writer_file:
                reader = csv.DictReader(reader_file)
                writer = csv.DictWriter(writer_file, fieldnames=reader.fieldnames)
                writer.writeheader()

                cur_dt = dt.datetime.now()
                time_val = cur_dt.strftime(dt_format)

                found = False
                for row in reader:
                    if row[key_column] == self.path:
                        row[dt_column] = time_val
                        found = True
                    writer.writerow(row)

                if not found:
                    new_row = {key_column: self.path, dt_column: time_val}
                    writer.writerow(new_row)

            shutil.move(temp_file_path, reference_file)

        return time_val

    def change_time(self, dt_string: str):
        self.last_review_time = self._processtime(readwrite='r', dt_string=dt_string)
        self.manual_review = True

    def modified_files(self) -> list:
        directory_files = os.listdir(self.path)
        mod_files = []
        for file in directory_files:
            file_name = os.path.join(self.path, file)
            if os.path.isfile(file_name):
                file_modified_time = dt.datetime.fromtimestamp(os.path.getmtime(file_name))
                if file_modified_time > self.last_review_time:
                    mod_files.append(file)

        if not self.manual_review:
            self._processtime(readwrite='w')

        return mod_files
