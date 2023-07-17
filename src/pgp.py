"""pgp

Author: Ethan Hunt
Creation Date: 2023-06-14

"""

import datetime as dt
import fnmatch
import logging
import os

import pgpy

from .constants import NL as NL
from .constants import BOOLEANS as BOOLEANS
from .misc import get_config as get_config
from .secrets import keepass


class pgp_constants:
    """A class for constants necessary for the pgp module"""
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class pgp:
    """Class implementation of PGP file handling

    Attributes
    ----------
    name : str
        Name of the PGP profile to use
    extension : str
        The expected PGP file extension (usually pgp or gpg)
    encrypt_path : str
        Default local directory to encrypt files from
    decrypt_path : str
        Default local directory to decrypt files from
    suppress_encrypt : list
        Specific files or wildcard names to not encrypt
    suppress_decrypt : list
        Specific files or wildcard names to not decrypt
    public_key : str
        Actual text of the public key
    private_key : str
        Actual text of the private key
    passphrase : str
        Passphrase for the private key
    log_path : str
        Directory in which log files will write to. Defined in the configuration file and will always be root/module_name
    log_name : str
        Name of log file, always module_yyyymmddHHMMSS.log
    log_delim : str
        Delimiter to use in the log file, defined in the configuration file

    """
    def __init__(self, profile_name: str, config_path: str = None):
        """Inits pgp class

        Parameters
        ----------
        profile_name : str
            Name of PGP profile
        config_path : str, optional (default None)
            Location of library configuration file

        Raises
        ------
        FileNotFoundError
            If 'config_path' does not exist
        RuntimeError
            If 'public_key' and 'private_key' values are missing
            If 'private_key' is populated but 'passphrase' is missing

        """
        if config_path and not os.path.isdir(config_path):
            raise FileNotFoundError

        kp = keepass(
            filename=get_config('keepassFile', config_path),
            password=os.getenv('AUTOMATIONPASSWORD'),
            group_title=pgp_constants.MODULE_NAME,
            entry_title=profile_name
        )
        self.name = profile_name
        self.extension = kp.getcustomproperties('EncryptedExtension').lower()
        self.encrypt_path = kp.getcustomproperties('EncryptPathDefault')
        self.decrypt_path = kp.getcustomproperties('DecryptPathDefault')

        suppress_delimiter = get_config('suppressDelimiter', config_path)
        self.suppress_encrypt = kp.getcustomproperties('SuppressEncryptDefault')
        self.suppress_encrypt = '' if self.suppress_encrypt is None else self.suppress_encrypt.strip(f"'{suppress_delimiter} '")
        self.suppress_encrypt = self.suppress_encrypt.split(suppress_delimiter)
        self.suppress_encrypt.append(f'*.{self.extension}')
        self.suppress_decrypt = kp.getcustomproperties('SuppressDecryptDefault')
        self.suppress_decrypt = '' if self.suppress_decrypt is None else self.suppress_decrypt.strip(f"'{suppress_delimiter} '")
        self.suppress_decrypt = self.suppress_decrypt.split(suppress_delimiter)

        self.public_key = kp.readattachment('PUBLIC.asc')
        self.private_key = kp.readattachment('PRIVATE.asc')
        self.passphrase = kp.getgeneral('Password')

        self.log_path = os.path.join(get_config('logRoot', config_path), pgp_constants.MODULE_NAME)
        self.log_name = f"{self.__class__.__name__}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"
        self.log_delim = get_config('logDelimiter', config_path)

        self._validate_profile()

    def _validate_profile(self):
        err_text = None
        if not self.public_key and not self.private_key:
            err_text = f"no public or private keys for profile '{self.name}'"

        if self.private_key and not self.passphrase:
            err_text = f"private key with no passphrase for profile '{self.name}'"

        if err_text is not None:
            raise RuntimeError(err_text)

    def _writelog(self, typ: str, dir: str, file_in: str, file_out: str):
        """Class function to write to a log file"""
        if not os.path.isdir(self.log_path):
            os.mkdir(self.log_path)
        with open(os.path.join(self.log_path, self.log_name), 'a') as logfile:
            dte, tme = dt.datetime.now().strftime('%Y-%m-%d'), dt.datetime.now().strftime('%H:%M:%S')
            logfile.write(f'{self.name}{self.log_delim}{dte}{self.log_delim}{tme}{self.log_delim}{typ}{self.log_delim}')
            logfile.write(f'{dir}{self.log_delim}{file_in}{self.log_delim}{file_out}{NL}')

    def encrypt(self, path_override: str = None, file_override: list | str = None, archive: bool = True, write_log: bool = False) -> list:
        """Encrypt files

        Parameters
        ----------
        path_override : str, optional (default None)
            Directory to encrypt. Will use self.encrypt_path if not provided
        file_override : list or str, optional (default None)
            File(s) to encrypt. Will encrypt all files in directory if not provided
        archive : bool, optional (default True)
            Indicator if original file(s) should move to an "Archive" subdirectory after encryption
        write_log : bool, optional (default False)
            Indicator if files encrypted should be written to a log file

        Returns
        -------
        list : All files that were encrypted, or an empty list if no files were encrypted

        Raises
        ------
        FileNotFoundError
            If 'path_override' does not exist

        TODO
        ----
        Excel/Word/Office files fail to encrypt because they are not text-based, how can I fix?

        """
        path_override = self.encrypt_path if path_override is None else path_override
        archive = archive if archive in BOOLEANS else False
        write_log = write_log if write_log in BOOLEANS else False

        if not os.path.isdir(path_override):
            raise FileNotFoundError

        # validate local_files and make sure its the proper data type
        file_override = [file_override] if isinstance(file_override, str) else file_override  # convert single files to a list
        file_override = file_override if isinstance(file_override, list) else []  # convert to empty list if not already a list type

        success_list = []
        if self.error is None:
            directory_list = [f for f in os.listdir(path_override) if os.path.isfile(os.path.join(path_override, f))]
            if len(file_override) == 0:
                # no specific files passed, use standard config parameters
                suppress_list = []
                for f in directory_list:
                    for suppress_item in self.suppress_encrypt:
                        if fnmatch.fnmatch(f, suppress_item):
                            suppress_list.append(f)

                encrypt_files = [x for x in directory_list if x not in suppress_list]
            else:
                # specific files/wildcards provided, bypass config parameters
                encrypt_list = []
                for f in directory_list:
                    for include_file in file_override:
                        if fnmatch.fnmatch(f, include_file):
                            encrypt_list.append(f)
                encrypt_files = [x for x in encrypt_list if os.path.isfile(os.path.join(path_override, x))]

            pub_key, _ = pgpy.PGPKey.from_blob(self.public_key)
            for f in encrypt_files:
                try:
                    pgpy.PGPMessage.from_file(os.path.join(path_override, f))
                    is_encrypted = True
                    logging.warning(f'File is already encrypted|{f}')
                except ValueError:
                    is_encrypted = False
                except NotImplementedError:
                    logging.critical(f'unable to read file {f}')
                    is_encrypted = True

                if not is_encrypted:
                    data = pgpy.PGPMessage.new(os.path.join(path_override, f), file=True)
                    encrypted_data = bytes(pub_key.encrypt(data))
                    encrypted_file = os.path.join(path_override, f'{f}.{self.extension}')
                    with open(encrypted_file, 'wb') as ef:
                        ef.write(encrypted_data)

                    success_list.append(encrypted_file)
                    if write_log:
                        self._writelog('ENCRYPT', path_override, f, os.path.basename(encrypted_file))

                    if archive:
                        archive_dir = os.path.join(path_override, 'Archive')
                        if os.path.isdir(archive_dir):
                            archive_name = os.path.join(archive_dir, f)
                            os.rename(os.path.join(path_override, f), archive_name)

        return success_list

    def decrypt(self, path_override: str = None, file_override: list | str = None, archive: bool = True, write_log: bool = False) -> list:
        """Decrypt files

        Parameters
        ----------
        path_override : str, optional (default None)
            Directory to decrypt. Will use self.decrypt_path if not provided
        file_override : list or str, optional (default None)
            File(s) to decrypt. Will decrypt all files in directory if not provided
        archive : bool, optional (default True)
            Indicator if original file(s) should move to an "Archive" subdirectory after decryption
        write_log : bool, optional (default False)
            Indicator if files decrypted should be written to a log file

        Returns
        -------
        list : All files that were decrypted, or an empty list if no files were decrypted

        Raises
        ------
        FileNotFoundError
            If 'path_override' does not exist

        """
        path_override = self.decrypt_path if path_override is None else path_override
        archive = archive if archive in BOOLEANS else False
        write_log = write_log if write_log in BOOLEANS else False

        if not os.path.isdir(path_override):
            raise FileNotFoundError

        # validate local_files and make sure its the proper data type
        file_override = [file_override] if isinstance(file_override, str) else file_override  # convert single files to a list
        file_override = file_override if isinstance(file_override, list) else []  # convert to empty list if not already a list type

        success_list = []
        if self.error is None:
            directory_list = [f for f in os.listdir(path_override) if os.path.isfile(os.path.join(path_override, f))]
            if len(file_override) == 0:
                # no specific files passed, use standard config parameters
                suppress_list = []
                for f in directory_list:
                    for suppress_item in self.suppress_decrypt:
                        if fnmatch.fnmatch(f, suppress_item):
                            suppress_list.append(f)

                decrypt_files = [x for x in directory_list if x not in suppress_list]
            else:
                # specific files/wildcards provided, bypass config parameters
                decrypt_list = []
                for f in directory_list:
                    for include_file in file_override:
                        if fnmatch.fnmatch(f, include_file):
                            decrypt_list.append(f)
                decrypt_files = [x for x in decrypt_list if os.path.isfile(os.path.join(path_override, x))]

            prv_key, _ = pgpy.PGPKey.from_blob(self.private_key)
            with prv_key.unlock(self.passphrase):
                for f in decrypt_files:
                    done = False
                    try:
                        encrypted_data = pgpy.PGPMessage.from_file(os.path.join(path_override, f))
                    except ValueError:
                        logging.warning(f'File is already decrypted|{f}')
                        done = True

                    if not done:
                        decrypted_data = prv_key.decrypt(encrypted_data).message
                        if not isinstance(decrypted_data, bytearray):
                            decrypted_data = bytearray(decrypted_data, encoding='utf-8')  # convert to bytes otherwise there's an extra <CR>

                        # strip off pgp, gpg, and self.extension
                        decrypted_name = f
                        if decrypted_name.endswith(('.pgp', '.gpg')):
                            decrypted_name = decrypted_name[:-4]
                        if decrypted_name.endswith(f'.{self.extension}'):
                            ext_len = len(self.extension)
                            decrypted_name = decrypted_name[:-ext_len]

                        decrypted_file = os.path.join(path_override, decrypted_name)
                        if os.path.isfile(decrypted_file):
                            decrypted_file = f'{decrypted_file}.out'
                        with open(decrypted_file, 'wb') as df:
                            df.write(decrypted_data)

                        success_list.append(decrypted_file)
                        if write_log:
                            self._writelog('DECRYPT', path_override, f, os.path.basename(decrypted_file))

                        if archive:
                            archive_dir = os.path.join(path_override, 'Archive')
                            if os.path.isdir(archive_dir):
                                archive_name = os.path.join(archive_dir, f)
                                os.rename(os.path.join(path_override, f), archive_name)

        return success_list
