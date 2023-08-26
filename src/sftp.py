import base64
import datetime as dt
import fnmatch
import io
import logging
import os
import posixpath
import re
import stat

import paramiko

from . import NL, BOOLEANS
from .misc import get_config
from .secrets import keepass


class sftp_constants:
    """A class for constants necessary for the sftp module"""
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class sftp:
    """Class to connect to an interact with an SFTP site

    Attributes
    ----------
    config_file : str
        Full path location of library configuration file
    name : str
        Name of the SFTP profile to connect to
    login_type : str
        Type of connection; normal and keyfile are accepted
    host : str
        The URL or IP address of the SFTP site
    port : int
        Port number to connect on. Defaults to 22 if not provided or invalid number is provided
    usr : str
        Username to connect with
    pwd : str
        Password to connect with
    passphrase : str
        Passphrase for the key file, if applicable
    private_key : str
        Actual private key text from the key file, if applicable
    save_host_key : bool
        Whether or not to save the host key information
    connect_insecure : bool
        Whether to bypass host key verification upon connection
    remote_in : str
        Default remote directory to upload files to. With use root "/" if not provided
    remote_out : str
        Default remote directory to download files from. With use root "/" if not provided
    local_in : str
        Default local directory to upload files from
    local_out : str
        Default local directory to download files to
    suppress_in : list
        Specific files or wildcard names to not download from an SFTP
    suppress_out : list
        Specific files or wildcard names to not upload to an SFTP
    ssh : paramiko.SSHClient
        Object representing the SFTP client being connected to
    log_path : str
        Directory in which log files will write to. Defined in the configuration file and will always be root/module_name
    log_name : str
        Name of log file, always module_yyyymmddHHMMSS.log
    log_delim : str
        Delimiter to use in the log file, defined in the configuration file
    track_progress : bool
        Indicator whether to print progress messages to stdout every 100 files processed

    """
    def __init__(
        self,
        profile_name: str,
        track_progress: bool = True,
        config_file: str = None,
        save_host_key: bool = False,
        connect_insecure: bool = False
    ):
        """Inits sftp class

        Parameters
        ----------
        profile_name : str
            Name of SFTP profile
        track_progress: bool, optional (default True)
            Inidicator if progress should be printed to stdout
        config_file : str, optional (default None)
            Full path location of library configuration file
        save_host_key : bool, optional (default False)
            Whether or not to save the host key information
        connect_insecure : bool, optional (default False)
            Whether to bypass host key verification upon connection

        Raises
        ------
        ValueError
            If 'host' is missing
            If 'username' is missing
            If 'pwd' and 'private_key' are missing
            If 'login_type' = "Key" but 'private_key' is missing

        TODO
        ----
        Look into error handling if private key is not an RSA key

        """
        self.config_file = config_file
        self.kp = keepass(
            filename=get_config('keepassFile', self.config_file),
            password=os.getenv(get_config('passwordEnvVar', self.config_file)),
            group_title=sftp_constants.MODULE_NAME,
            entry_title=profile_name
        )
        self.name = profile_name
        self.login_type = self.kp.getcustomproperties('LoginType').strip().upper()
        self.login_type = 'KEY' if 'KEY' in self.login_type else 'NORMAL'  # consider it a key file if string contains 'key'
        self.host = self.kp.getgeneral('url')
        self.host_key_type = self.kp.getcustomproperties('HostKeyType')
        self.host_key_value = self.kp.getcustomproperties('HostKeyValue')
        self.port = self.kp.getcustomproperties('Port')
        try:
            self.port = int(self.port)
        except ValueError:
            self.port = 22
        self.usr = self.kp.getgeneral('Username')
        self.pwd = self.kp.getgeneral('Password')
        self.passphrase = self.kp.getcustomproperties('Passphrase')
        self.private_key = self.kp.readattachment('OPENSSH_PRIVATE.asc')
        if self.private_key:
            self.private_key = io.StringIO(self.private_key)
            self.private_key = paramiko.RSAKey.from_private_key(self.private_key, self.passphrase)
        self.save_host_key = save_host_key if save_host_key in BOOLEANS else False
        self.connect_insecure = connect_insecure if connect_insecure in BOOLEANS else False
        if self.connect_insecure:
            logging.info(f'connecting to {self.host} insecurely')

        root = '/'
        self.remote_in = self.kp.getcustomproperties('RemoteInDefault')
        self.remote_in = root if not self.remote_in else self.remote_in
        self.remote_out = self.kp.getcustomproperties('RemoteOutDefault')
        self.remote_out = root if not self.remote_out else self.remote_out
        self.local_in = self.kp.getcustomproperties('LocalInDefault')
        self.local_out = self.kp.getcustomproperties('LocalOutDefault')

        suppress_delimiter = get_config('suppressDelimiter', self.config_file)
        self.suppress_in = self.kp.getcustomproperties('SuppressInDefault')
        self.suppress_in = '' if self.suppress_in is None else self.suppress_in.strip(f"'{suppress_delimiter} '")
        self.suppress_in = self.suppress_in.split(suppress_delimiter)
        self.suppress_out = self.kp.getcustomproperties('SuppressOutDefault')
        self.suppress_out = '' if self.suppress_out is None else self.suppress_out.strip(f"'{suppress_delimiter} '")
        self.suppress_out = self.suppress_out.split(suppress_delimiter)

        self.log_path = os.path.join(get_config('logRoot', self.config_file), sftp_constants.MODULE_NAME)
        self.log_name = f"{self.__class__.__name__}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}_{re.sub(r'[^a-zA-Z0-9]', '', self.name)}.log"
        self.log_delim = get_config('logDelimiter', self.config_file)
        self.track_progress = track_progress if track_progress in BOOLEANS else True

        self._validate_profile()

        self._connectssh()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.ssh.close()

    def close(self):
        self.ssh.close()

    def _validate_profile(self):
        err_text = None
        if not self.host:
            err_text = f"missing host for profile '{self.name}'"
        if not self.usr:
            err_text = f"missing username for profile '{self.name}'"
        if not self.pwd and not self.private_key:
            err_text = f"missing login method for profile '{self.name}'"
        if self.login_type == 'KEY' and not self.private_key:
            err_text = f"missing key file for profile '{self.name}'"

        if err_text is not None:
            logging.critical(err_text)
            raise ValueError(err_text)

    def _connectssh(self):
        """Connects to the ssh

        Raises
        ------
        paramiko.AuthenticationException
            If SSH authentication fails
        paramiko.SSHException
            For general SSH exceptions
        Exception
            Anything else that might pop up

        """
        self.ssh = paramiko.SSHClient()
        if self.save_host_key or self.connect_insecure:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            host_key = paramiko.pkey.PKey.from_type_string(self.host_key_type, base64.b64decode(self.host_key_value))
            self.ssh.get_host_keys().add(self.host, self.host_key_type, host_key)
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
                    pkey=self.private_key,
                    passphrase=self.passphrase,
                    disabled_algorithms=dict(pubkeys=['rsa-sha2-512', 'rsa-sha2-256'])
                )
        except paramiko.AuthenticationException as e:
            logging.critical(paramiko.AuthenticationException(self.host))
            raise paramiko.AuthenticationException(self.host) from e
        except paramiko.SSHException as e:
            logging.critical(paramiko.SSHException(f'{e}|{self.host}'))
            raise paramiko.SSHException(f'{e}|{self.host}') from e
        except Exception as e:
            logging.critical(f'Unhandled exception {e}|{self.host}')
            raise Exception(f'Unhandled exception {e}|{self.host}') from e

        if self.save_host_key:
            host_key = self.ssh.get_transport().get_remote_server_key()
            self.kp.writecustomproperty(string_field='HostKeyType', new_value=host_key.get_name(), create_property=True)
            self.kp.writecustomproperty(string_field='HostKeyValue', new_value=host_key.get_base64(), create_property=True)

    def _writelog(self, direction: str, remote_dir: str, local_dir: str, filename: str):
        """Class function to write to a log file"""
        if not os.path.isdir(self.log_path):
            os.mkdir(self.log_path)
        with open(os.path.join(self.log_path, self.log_name), 'a') as logfile:
            dte, tme = dt.datetime.now().strftime('%Y-%m-%d'), dt.datetime.now().strftime('%H:%M:%S')
            logfile.write(f'{self.name}{self.log_delim}{dte}{self.log_delim}{tme}{self.log_delim}{direction}{self.log_delim}')
            logfile.write(f'{remote_dir}{self.log_delim}{local_dir.replace(os.pathsep, posixpath.sep)}{self.log_delim}{filename}{NL}')

    def listsftpdir(self, remote_dir: str) -> list:
        """Return a list of files on an SFTP

        Parameters
        ----------
        remote_dir : str
            Remote directory to list files from

        Returns
        -------
        list : All files in the remote directory, or an empty list if no files exist

        """
        with self.ssh.open_sftp() as ftp:
            ftp.chdir(remote_dir)
            dir_list = ftp.listdir_attr(remote_dir)

        file_list = []
        if len(dir_list) > 0:
            file_list = [x.filename for x in dir_list if not stat.S_ISDIR(x.st_mode)]

        return file_list

    def download(
        self,
        remote_dir: str = None,
        local_dir: str = None,
        remote_files: list | str = None,
        suppress_override: list | str = None,
        delete_ftp: bool = True,
        write_log: bool = False
    ) -> list:
        """Download files from an SFTP

        Parameters
        ----------
        remote_dir : str, optional (default None)
            Remote directory to download files from. Will use self.remote_in if not provided
        local_dir : str, optional (default None)
            Local directory to download files to. Will use self.local_in if not provided
        remote_files : list or str, optional (default None)
            Specific files or wildcard names to download. Will use all files in remote_dir if not provided
        suppress_override : list or str, optional (default None)
            Specific files or wildcard names to suppress from download. Will use all 'self.suppress_in' if not provided
        delete_ftp : bool, optional (default True)
            Indicator if files should be deleted from the SFTP after download is completed
        write_log : bool, optional (default False)
            Indicator if files downloaded should be written to a log file

        Returns
        -------
        list : the basename of the files downloaded

        Raises
        ------
        FileNotFoundError
            If 'local_dir' does not exist

        """
        remote_dir = self.remote_in if remote_dir is None else remote_dir
        local_dir = self.local_in if local_dir is None else local_dir
        delete_ftp = delete_ftp if delete_ftp in BOOLEANS else False
        write_log = write_log if write_log in BOOLEANS else False

        if not os.path.isdir(local_dir):
            err_msg = f"local directory '{local_dir} does not exist"
            logging.critical(err_msg)
            raise FileNotFoundError(err_msg)

        # validate local_files and make sure its the proper data type
        remote_files = [remote_files] if isinstance(remote_files, str) else remote_files  # convert single files to a list
        remote_files = remote_files if isinstance(remote_files, list) else []  # convert to empty list if not already a list type

        suppress_override = [suppress_override] if isinstance(suppress_override, str) else suppress_override
        suppress_override = suppress_override if isinstance(suppress_override, list) else []
        suppress_list = self.suppress_in if len(suppress_override) == 0 else suppress_override

        success_list = []
        with self.ssh.open_sftp() as ftp:
            ftp.chdir(remote_dir)
            dir_list = [f.filename for f in ftp.listdir_attr(remote_dir) if not stat.S_ISDIR(f.st_mode)]
            suppress_items = []
            if len(remote_files) == 0:
                # no specific files passed, figure it out within the script
                # do not need separate handling of suppress_list because it's just a list iterable
                for f in dir_list:
                    for item in suppress_list:
                        if fnmatch.fnmatch(f, item):
                            suppress_items.append(f)
                download_files = [x for x in dir_list if x not in suppress_items]
            else:
                # specific files/wildcards provided, bypass config parameters
                download_list = []
                for include_file in remote_files:
                    match_found = False
                    for f in dir_list:
                        if fnmatch.fnmatch(f, include_file):
                            download_list.append(f)
                            match_found = True
                    if not match_found:
                        logging.info(f"unable to download '{include_file}', file or pattern does not exist in '{remote_dir}'")

                # pull out the files to suppress
                if len(suppress_list) != 0:
                    for f in download_list:
                        for item in suppress_list:
                            if fnmatch.fnmatch(f, item):
                                suppress_items.append(f)
                download_files = [x for x in download_list if x not in suppress_items]

            tot_ct = len(download_files)
            for ctr, f in enumerate(download_files):
                remote_file = os.path.join(remote_dir, f).replace('\\', '/')
                local_file = os.path.join(local_dir, f)
                archive_dir_name = get_config('archiveDirName', self.config_file)
                local_file_archive = os.path.join(local_dir, archive_dir_name, f)
                if not os.path.isfile(local_file):
                    if not os.path.isfile(local_file_archive):
                        success = True
                        try:
                            ftp.get(remote_file, local_file)
                        except Exception as e:
                            success = False
                            logging.error(f"unable to download '{remote_file}'|{e}")

                        if success:
                            success_list.append(f)
                            if write_log:
                                self._writelog('GET', remote_dir, local_dir, f)
                            if delete_ftp:
                                ftp.remove(remote_file)

                if self.track_progress:
                    if (ctr + 1) % 100 == 0:
                        logging.info(f'{ctr + 1} files processed out of {tot_ct}')

        return success_list

    def upload(
            self,
            remote_dir: str = None,
            local_dir: str = None,
            local_files: list | str = None,
            suppress_override: list | str = None,
            write_log: bool = False
    ) -> list:
        """Upload files to an SFTP

        Parameters
        ----------
        remote_dir : str, optional (default None)
            Remote directory to upload files to. Will use 'self.remote_out' if not providied
        local_dir : str, optional (default None)
            Local directory to upload files from. Will use 'self.local_out' if not provided
        local_files : list or str, optional (default None)
            Specific files or wildcard names to upload. Will use all files in 'local_dir' if not provided
        suppress_override : list or str, optional (default None)
            Specific files or wildcard names to suppress from upload. Will use all 'self.suppress_out' if not provided
        write_log : bool, optional (default False)
            Indicator if files uploaded should be written to a log file

        Returns
        -------
        list : the basename of the files successfully uploaded

        Raises
        ------
        FileNotFoundError
            If 'local_dir' does not exist

        """
        remote_dir = self.remote_out if remote_dir is None else remote_dir
        local_dir = self.local_out if local_dir is None else local_dir
        write_log = write_log if write_log in BOOLEANS else False

        if not os.path.isdir(local_dir):
            err_msg = f"local directory '{local_dir} does not exist"
            logging.critical(err_msg)
            raise FileNotFoundError(err_msg)

        # validate variables and make sure they the proper data type
        local_files = [local_files] if isinstance(local_files, str) else local_files
        local_files = local_files if isinstance(local_files, list) else []

        suppress_override = [suppress_override] if isinstance(suppress_override, str) else suppress_override
        suppress_override = suppress_override if isinstance(suppress_override, list) else []
        suppress_list = self.suppress_out if len(suppress_override) == 0 else suppress_override

        directory_list = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
        suppress_items = []
        if len(local_files) == 0:
            # no specific files passed, figure it out within the script
            # do not need separate handling of suppress_list because it's just a list iterable
            for f in directory_list:
                for item in suppress_list:
                    if fnmatch.fnmatch(f, item):
                        suppress_items.append(f)
            upload_files = [x for x in directory_list if x not in suppress_items]
        else:
            # specific files/wildcards provided, bypass config parameters
            upload_list = []
            for include_file in local_files:
                match_found = False
                for f in directory_list:
                    if fnmatch.fnmatch(f, include_file):
                        upload_list.append(f)
                        match_found = True
                if not match_found:
                    logging.info(f"unable to upload '{include_file}', file or pattern does not exist in '{local_dir.replace(os.pathsep, posixpath.sep)}'")

            # pull out the files to suppress
            if len(suppress_list) != 0:
                for f in upload_list:
                    for item in suppress_list:
                        if fnmatch.fnmatch(f, item):
                            suppress_items.append(f)
            upload_files = [x for x in upload_list if x not in suppress_items]

        success_list = []
        tot_ct = len(upload_files)
        if tot_ct > 0:
            archive_dir_name = get_config('archiveDirName', self.config_file)
            local_dir_archive = os.path.join(local_dir, archive_dir_name)
            with self.ssh.open_sftp() as ftp:
                ftp.chdir(remote_dir)
                for ctr, f in enumerate(upload_files):
                    success = True
                    lf = os.path.join(local_dir, f)
                    uf = remote_dir + posixpath.sep + f if remote_dir[-1] != posixpath.sep else remote_dir + f  # ensure a trailing path separator exists
                    try:
                        ftp.put(lf, uf)
                    except Exception as e:
                        success = False
                        logging.error(f"unable to upload '{f} to '{remote_dir}'|{e}")

                    if self.track_progress:
                        if (ctr + 1) % 100 == 0:
                            logging.info(f'{ctr + 1} files processed out of {tot_ct}')

                    if success:
                        success_list.append(f)

                        if write_log:
                            self._writelog('PUT', remote_dir, local_dir, f)

                        if os.path.isdir(local_dir_archive):
                            archive_name = os.path.join(local_dir_archive, f)
                            os.rename(lf, archive_name)

        return success_list
