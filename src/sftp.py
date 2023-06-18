"""sftp

Author: Ethan Hunt
Date: 2023-06-13
Version: 1.0

"""

import datetime as dt
import logging
import os
import stat

import paramiko

from .constants import NL as NL
from .constants import BOOLEANS as BOOLEANS
from .misc import get_config as get_config


class sftp_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
    DELIM = get_config(MODULE_NAME, 'logDelimiter')


class sftp:
    def __init__(self, profile: dict):
        self.name = profile.get('Name').strip()
        self.active = profile.get('Active').strip()
        self.active = True if self.active == '1' else False
        self.login_type = profile.get('LoginType').strip()
        self.login_type = self.login_type.upper() if self.login_type.upper() in ['NORMAL', 'KEY'] else 'NORMAL'
        self.host = profile.get('Host').strip()
        self.port = profile.get('Port').strip()
        try:
            self.port = int(self.port)
        except ValueError:
            self.port = 22
        self.usr = profile.get('Username').strip()
        self.pwd = profile.get('Password').strip()
        self.keyfile = profile.get('KeyFile').strip()

        root = '/'
        self.remote_in = profile.get('RemoteIn').strip()
        self.remote_in = root if self.remote_in == '' else self.remote_in
        self.remote_out = profile.get('RemoteOut').strip()
        self.remote_out = root if self.remote_out == '' else self.remote_out
        self.local_in = profile.get('LocalIn').strip()
        self.local_out = profile.get('LocalOut').strip()

        suppress_delimiter = get_config(sftp_constants.MODULE_NAME, 'suppressDelimiter')
        self.suppress_in = profile.get('SuppressIn').strip(f"'{suppress_delimiter} '")
        self.suppress_in = self.suppress_in.split(suppress_delimiter)
        self.suppress_out = profile.get('SuppressOut').strip(f"'{suppress_delimiter} '")
        self.suppress_out = self.suppress_out.split(suppress_delimiter)

        self.error = None
        self.ssh = None
        self.key_path = get_config(sftp_constants.MODULE_NAME, 'keyPath')
        self.log_path = get_config(sftp_constants.MODULE_NAME, 'logPath')
        self.log_name = f"{get_config(sftp_constants.MODULE_NAME, 'logName')}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"
        self.track_progress = get_config(sftp_constants.MODULE_NAME, 'trackProgress')

        if self._validate_profile() is not None:
            logging.critical(self.error)

    def _validate_profile(self) -> str:
        if not self.active:
            self.error = f'Inactive profile|{self.name}'
        if self.host is None:
            self.error = f'Missing host|{self.name}'
        if self.usr is None:
            self.error = f'Missing username|{self.name}'
        if self.pwd is None and self.keyfile is None:
            self.error = f'Missing login method|{self.name}'

        return self.error

    def _connectssh(self):
        self.ssh = paramiko.SSHClient()
        # TODO: Really should do this the right way, since AutoAddPolicy is vulnerable to MITM attacks
        # Am hesitent to fix this since it likely will require a manual change for new connections and non-Python peeps won't know how
        # https://stackoverflow.com/questions/10670217/paramiko-unknown-server
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.login_type == 'NORMAL':
                self.ssh.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.usr,
                    password=self.pwd
                )
            elif self.login_type == 'KEY':
                self.ssh.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.usr,
                    key_filename=os.path.join(self.key_path, self.keyfile),
                    passphrase=self.pwd
                )
        except paramiko.AuthenticationException:
            logging.critical(f'AuthenticationException|{self.host}')
        except paramiko.SSHException as e:
            logging.critical(f'{e}|{self.host}')
        except Exception as e:
            logging.critical(f'Unhandled exception {e}|{self.host}')

    def _writelog(self, direction: str, remote_dir: str, local_dir: str, filename: str):
        with open(os.path.join(self.log_path, self.log_name), 'a') as logfile:
            dte, tme = dt.datetime.now().strftime('%Y-%m-%d'), dt.datetime.now().strftime('%H:%M:%S')
            logfile.write(f'{self.name}{sftp_constants.DELIM}{dte}{sftp_constants.DELIM}{tme}{sftp_constants.DELIM}{direction}{sftp_constants.DELIM}')
            logfile.write(f'{remote_dir}{sftp_constants.DELIM}{local_dir}{sftp_constants.DELIM}{filename}{NL}')

    def download(self, remote_dir: str = None, local_dir: str = None, delete_ftp: bool = True, write_log: bool = False):
        # TODO: Validate local_in exists
        remote_dir = self.remote_in if remote_dir is None else remote_dir
        local_dir = self.local_in if local_dir is None else local_dir
        delete_ftp = delete_ftp if delete_ftp in BOOLEANS else False
        write_log = write_log if write_log in BOOLEANS else False

        if self.error is None:
            self._connectssh()
            with self.ssh.open_sftp() as ftp:
                ftp.chdir(remote_dir)
                dir_list = ftp.listdir_attr(remote_dir)
                tot_ct = len(dir_list)
                for ctr, f in enumerate(dir_list):
                    if self.track_progress:
                        if (ctr + 1) % 100 == 0:
                            logging.info(f'{ctr + 1} files processed out of {tot_ct}')
                    if not stat.S_ISDIR(f.st_mode):
                        # TODO: Add support for self.suppress_in
                        remote_file = os.path.join(remote_dir, f.filename).replace('\\', '/')
                        local_file = os.path.join(local_dir, f.filename)
                        local_file_archive = os.path.join(local_dir, 'Archive', f.filename)
                        if not os.path.isfile(local_file):
                            if not os.path.isfile(local_file_archive):
                                ftp.get(remote_file, local_file)
                                if write_log:
                                    self._writelog('GET', remote_dir, local_dir, f.filename)
                                if delete_ftp:
                                    ftp.remove(remote_file)
                            else:
                                logging.debug(f'In archive|{f.filename}')
                        else:
                            logging.debug(f'In main|{f.filename}')

    def upload(self, remote_dir: str = None, local_dir: str = None, write_log: bool = False):
        # TODO: Validate local_out exists
        remote_dir = self.remote_out if remote_dir is None else remote_dir
        local_dir = self.local_out if local_dir is None else local_dir
        write_log = write_log if write_log in BOOLEANS else False

        if self.error is None:
            local_dir_archive = os.path.join(local_dir, 'Archive')
            local_files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
            if len(local_files) > 0:
                # TODO: Add support for self.suppress_out
                self._connectssh()
                with self.ssh.open_sftp() as ftp:
                    ftp.chdir(remote_dir)
                    for f in local_files:
                        lf = os.path.join(local_dir, f)
                        ftp.put(lf, remote_dir)
                        if write_log:
                            self._writelog('PUT', remote_dir, local_dir, f.filename)
                        if os.path.isdir(local_dir_archive):
                            archive_name = os.path.join(local_dir_archive, f)
                            os.rename(lf, archive_name)
