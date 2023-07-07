"""sftp

Author: Ethan Hunt
Date: 2023-06-13
Version: 2.0

"""

import datetime as dt
import fnmatch
import logging
import os
import stat

import paramiko

from .constants import NL as NL
from .constants import BOOLEANS as BOOLEANS
from .misc import get_config as get_config
from .secrets import keepass


class sftp_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
    DELIM = get_config('logDelimiter')


class sftp:
    def __init__(self, profile_name: str, track_progress: bool = True):
        kp = keepass(
            filename=get_config('keepassFile'),
            password=os.getenv('AUTOMATIONPASSWORD'),
            group_title=sftp_constants.MODULE_NAME,
            entry_title=profile_name
        )
        self.name = profile_name
        self.login_type = kp.getcustomproperties('LoginType').strip().upper()
        self.login_type = self.login_type if self.login_type in ['NORMAL', 'KEY'] else 'NORMAL'
        self.host = kp.getgeneral('url').strip()
        self.port = kp.getcustomproperties('Port')
        try:
            self.port = int(self.port)
        except ValueError:
            self.port = 22
        self.usr = kp.getgeneral('Username').strip()
        self.pwd = kp.getgeneral('Password').strip()
        self.passphrase = kp.getcustomproperties('Passphrase').strip()
        self.private_key = kp.readattachment('OPENSSH_PRIVATE.asc')

        root = '/'
        self.remote_in = kp.getcustomproperties('RemoteInDefault').strip()
        self.remote_in = root if self.remote_in == '' else self.remote_in
        self.remote_out = kp.getcustomproperties('RemoteOutDefault').strip()
        self.remote_out = root if self.remote_out == '' else self.remote_out
        self.local_in = kp.getcustomproperties('LocalInDefault').strip()
        self.local_out = kp.getcustomproperties('LocalOutDefault').strip()

        suppress_delimiter = get_config('suppressDelimiter')
        self.suppress_in = kp.getcustomproperties('SuppressInDefault').strip(f"'{suppress_delimiter} '")
        self.suppress_in = self.suppress_in.split(suppress_delimiter)
        self.suppress_out = kp.getcustomproperties('SuppressOutDefault').strip(f"'{suppress_delimiter} '")
        self.suppress_out = self.suppress_out.split(suppress_delimiter)

        self.error = None
        self.ssh = None
        self.log_path = os.path.join(get_config('logRoot'), sftp_constants.MODULE_NAME)
        self.log_name = f"{self.__class__.__name__}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"
        self.track_progress = track_progress if track_progress in BOOLEANS else True

        if self._validate_profile() is not None:
            logging.critical(self.error)

    def _validate_profile(self) -> str:
        if not self.host:
            self.error = f'Missing host|{self.name}'
        if not self.usr:
            self.error = f'Missing username|{self.name}'
        if not self.pwd and not self.private_key:
            self.error = f'Missing login method|{self.name}'
        if self.login_type.upper() == 'KEY' and not self.private_key:
            self.error = f'Missing key file|{self.name}'

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
                    password=self.pwd,
                    # TODO: Consider some kind of error handling if not an OPENSSH key file
                    key_filename=os.path.join(self.key_path, self.keyfile),  # FIXME: Physical file DNE
                    passphrase=self.passphrase
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

    def _listsftpdir(self, remote_dir: str) -> list:
        self._connectssh()
        with self.ssh.open_sftp() as ftp:
            ftp.chdir(remote_dir)
            dir_list = ftp.listdir_attr(remote_dir)

        file_list = [x.filename for x in dir_list if not stat.S_ISDIR(x.st_mode)]
        return file_list

    def download(self, remote_dir: str = None, local_dir: str = None, delete_ftp: bool = True, write_log: bool = False):
        # TODO: download specific file masks
        remote_dir = self.remote_in if remote_dir is None else remote_dir
        local_dir = self.local_in if local_dir is None else local_dir
        delete_ftp = delete_ftp if delete_ftp in BOOLEANS else False
        write_log = write_log if write_log in BOOLEANS else False

        if not os.path.isdir(local_dir):
            raise FileNotFoundError

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
                        suppress_file = False
                        for suppress_item in self.suppress_in:
                            if fnmatch.fnmatch(f.filename, suppress_item):
                                suppress_file = True

                        if not suppress_file:
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

    def upload(self, remote_dir: str = None, local_dir: str = None, local_files: list | str = None, write_log: bool = False):
        remote_dir = self.remote_out if remote_dir is None else remote_dir
        local_dir = self.local_out if local_dir is None else local_dir
        write_log = write_log if write_log in BOOLEANS else False

        # validate local_files and make sure its the proper data type
        local_files = [local_files] if isinstance(local_files, str) else local_files  # convert single files to a list
        local_files = local_files if isinstance(local_files, list) else []  # convert to empty list if not already a list type

        if not os.path.isdir(local_dir):
            raise FileNotFoundError

        if self.error is None:
            if len(local_files) == 0:
                # no specific files passed, use standard config parameters
                local_files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
                suppress_list = []
                for f in local_files:
                    for suppress_item in self.suppress_out:
                        if fnmatch.fnmatch(f, suppress_item):
                            suppress_list.append(f)

                upload_files = [x for x in local_files if x not in suppress_list]
            else:
                # specific files/wildcards provided, bypass config parameters
                dir_files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
                upload_list = []
                for f in dir_files:
                    for include_file in local_files:
                        if fnmatch.fnmatch(f, include_file):
                            upload_list.append(f)
                upload_files = [x for x in upload_list if os.path.isfile(os.path.join(local_dir, x))]

            if len(upload_files) > 0:
                local_dir_archive = os.path.join(local_dir, 'Archive')
                self._connectssh()
                with self.ssh.open_sftp() as ftp:
                    ftp.chdir(remote_dir)
                    for f in upload_files:
                        lf = os.path.join(local_dir, f)
                        uf = remote_dir + '/' + f if remote_dir[-1] != '/' else remote_dir + f  # ok to hard-code / here, it's sftp
                        ftp.put(lf, uf)
                        if write_log:
                            self._writelog('PUT', remote_dir, local_dir, f)
                        if os.path.isdir(local_dir_archive):
                            archive_name = os.path.join(local_dir_archive, f)
                            os.rename(lf, archive_name)
