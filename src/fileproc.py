"""fileproc

Author: Ethan Hunt
Creation Date: 2023-06-18

"""

import csv
import datetime as dt
import os
import tempfile
import shutil

from .constants import BOOLEANS as BOOLEANS
from .constants import NL as NL
from .misc import get_config as get_config

# TODO: Mass move files from one location to another? Perhaps too general and shutil is good enough
# TODO: Handling/logging around receiving servicer files


class fileproc_constants:
    """A class for constants necessary for the fileproc module"""
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class monitoring:
    """Class to monitor directories for changes in content

    Attributes
    ----------
    path : str
        Directory to monitor
    config_path : str
        Location of library configuration file
    error : str
        Text of validation error
    last_review_time : str
        Reference datetime to identify modified files from. Formatted as yyyy-mm-dd HH:MM:SS
    manual_review : bool
        Flag used if process is being run as a one-off instance
    log_path : str
        Directory in which log files will write to. Defined in the configuration file and will always be root/module_name
    log_name : str
        Name of log file, always module_yyyymmddHHMMSS.log
    log_delim : str
        Delimiter to use in the log file, defined in the configuration file
    ref_delim : str
        Delimiter to use in the reference file logging the last datetime of monitoring review, defined in the configuration file

    """
    def __init__(self, path: str, config_path: str = None):
        """Inits monitoring class

        Parameters
        ----------
        path : str
            Directory to monitor
        config_path : str, optional (default None)
            Location of library configuration file

        Raises
        ------
        FileNotFoundError
            If 'config_path' does not exist
            If 'path' does not exist
        RuntimeError
            If 'path' contains 'ref_delim'

        Examples
        ----------
        >>> monitor = monitoring('/my/path')
        >>> print(monitor.__module__)
        src.fileproc

        """
        if config_path and not os.path.isdir(config_path):
            raise FileNotFoundError

        self.path = path
        self.config_path = config_path
        self.error = None
        self.last_review_time = self._processtime(readwrite='r')
        self.manual_review = False

        self.log_path = os.path.join(get_config('logRoot', config_path), fileproc_constants.MODULE_NAME)
        self.log_name = f"{self.__class__.__name__}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"

        self.log_delim = get_config('logDelimiter', config_path)
        self.ref_delim = get_config('fileproc_referenceDelimiter', config_path)

        self._validate()

    def _validate(self):
        """Class function to validate if the necessary information is available at the time of __init__"""
        if not os.path.isdir(self.path):
            raise FileNotFoundError(f"path '{self.path}' does not exist")

        if self.ref_delim in self.path:
            raise RuntimeError(f"path '{self.path}' contains referenceDelimiter '{self.ref_delim}'")

    def _processtime(self, readwrite: str = 'r', dt_string: str = None) -> dt.datetime:
        """Class function that returns the time a directory was last monitored

        Read from file the last datetime a directory was monitored, or update file with new datetime
        Able to accept a custom time to bypass reading from file

        Parameters
        ----------
        readwrite : str, optional (default 'r')
            Indicator whether to Read from reference file or Write to reference file
        dt_string : str, optional (default None)
            Datetime override value to use instead of datetime in reference file

        Returns
        -------
        Datetime.Datetime : 'dt_string' converted to Datetime object or value from reference file

        Raises
        ------
        ValueError
            If 'readwrite' is not either "r" or "w"

        """
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

        # valid datetime was provided; return it and exit function
        if dt_format_validated:
            return time_val

        # create reference file if it does not exist
        key_column = 'Path'
        dt_column = 'LastMonitorTime'
        reference_file = get_config('fileproc_referenceFile', self.config_path)
        if not os.path.isfile(reference_file):
            header_row = f'{key_column}{self.ref_delim}{dt_column}{NL}'
            with open(file=reference_file, mode='w', encoding='utf-8') as f:
                f.write(header_row)

        if readwrite == 'r':
            # Read last time from reference file; return Epoch if no datetime is found
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
            # Write current datetime to reference file
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

    def _writelog(self, filename: str):
        """Class function to write to a log file"""
        with open(os.path.join(self.log_path, self.log_name), 'a') as logfile:
            dte, tme = dt.datetime.now().strftime('%Y-%m-%d'), dt.datetime.now().strftime('%H:%M:%S')
            logfile.write(f'{self.path}{self.log_delim}{dte}{self.log_delim}')
            logfile.write(f'{tme}{self.log_delim}{filename}{NL}')

    def change_time(self, dt_string: str):
        """Manually set 'last_review_time' and flip the 'manual_review' flag"""
        self.last_review_time = self._processtime(readwrite='r', dt_string=dt_string)
        self.manual_review = True

    def modified_files(self, write_log: bool = False) -> list:
        """Identify which files have been modified since a preset datetime value

        Parameters
        ----------
        write_log : bool, optional (default False)
            Indicator whether to write the list of modified files to a log file

        Returns
        -------
        list : All files recently modified, or an empty list if no files have been modified

        """
        write_log = write_log if write_log in BOOLEANS else False
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

        if write_log:
            for f in mod_files:
                self._writelog(f)

        return mod_files
