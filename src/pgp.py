"""pgp

Author: Ethan Hunt
Date: 2023-06-14
Version: 2.0

"""

import datetime as dt
import fnmatch
import logging
import os

import pgpy

from .constants import BOOLEANS as BOOLEANS
from .misc import get_config as get_config
from .secrets import keepass


class pgp_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
    DELIM = get_config('logDelimiter')


class pgp:
    def __init__(self, profile_name: str):
        kp = keepass(
            filename=get_config('keepassFile'),
            password=os.getenv('AUTOMATIONPASSWORD'),
            group_title=pgp_constants.MODULE_NAME,
            entry_title=profile_name
        )
        self.name = profile_name
        self.extension = kp.getcustomproperties('EncryptedExtension').strip().lower()
        self.encrypt_path = kp.getcustomproperties('EncryptPathDefault').strip()
        self.decrypt_path = kp.getcustomproperties('DecryptPathDefault').strip()

        suppress_delimiter = get_config('suppressDelimiter')
        self.suppress_encrypt = kp.getcustomproperties('SuppressEncryptDefault').strip(f"'{suppress_delimiter} '")
        self.suppress_encrypt = self.suppress_encrypt.split(suppress_delimiter)
        self.suppress_encrypt.append(f'*.{self.extension}')
        self.suppress_decrypt = kp.getcustomproperties('SuppressDecryptDefault').strip(f"'{suppress_delimiter} '")
        self.suppress_decrypt = self.suppress_decrypt.split(suppress_delimiter)

        self.public_key = kp.readattachment('PUBLIC.asc')
        self.private_key = kp.readattachment('PRIVATE.asc')
        self.passphrase = kp.getgeneral('Password')

        self.error = None
        self.log_path = os.path.join(get_config('logRoot'), pgp_constants.MODULE_NAME)
        self.log_name = f"{self.__class__.__name__}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"

        if self._validate_profile() is not None:
            logging.critical(self.error)

    def _validate_profile(self) -> str:
        if self.error is not None:
            logging.critical(self.error)

        return self.error

    def encrypt(self, archive: bool = True):
        # TODO: Add custom path and file parameters like in SFTP
        archive = archive if archive in BOOLEANS else False

        if self.error is None:
            pub_key, _ = pgpy.PGPKey.from_blob(self.public_key)
            directory_list = [f for f in os.listdir(self.encrypt_path) if os.path.isfile(os.path.join(self.encrypt_path, f))]
            suppress_list = []
            for f in directory_list:
                for suppress_item in self.suppress_encrypt:
                    if fnmatch.fnmatch(f, suppress_item):
                        suppress_list.append(f)

            encrypt_files = [x for x in directory_list if x not in suppress_list]
            for f in encrypt_files:
                is_encrypted = False
                try:
                    pgpy.PGPMessage.from_file(os.path.join(self.encrypt_path, f))
                    is_encrypted = True
                except ValueError:
                    logging.debug(f'File is already encrypted|{f}')
                if not is_encrypted:
                    data = pgpy.PGPMessage.new(os.path.join(self.encrypt_path, f), file=True)
                    encrypted_data = bytes(pub_key.encrypt(data))
                    encrypted_file = os.path.join(self.encrypt_path, f'{f}.{self.extension}')
                    with open(encrypted_file, 'wb') as ef:
                        ef.write(encrypted_data)

                    if archive:
                        archive_dir = os.path.join(self.encrypt_path, 'Archive')
                        if os.path.isdir(archive_dir):
                            archive_name = os.path.join(archive_dir, f)
                            os.rename(os.path.join(self.encrypt_path, f), archive_name)

    def decrypt(self, archive: bool = True):
        # TODO: Add custom path and file parameters like in SFTP
        archive = archive if archive in BOOLEANS else False

        if self.error is None:
            prv_key, _ = pgpy.PGPKey.from_blob(self.private_key)
            directory_list = [f for f in os.listdir(self.decrypt_path) if os.path.isfile(os.path.join(self.decrypt_path, f))]
            suppress_list = []
            for f in directory_list:
                for suppress_item in self.suppress_decrypt:
                    if fnmatch.fnmatch(f, suppress_item):
                        suppress_list.append(f)

            decrypt_files = [x for x in directory_list if x not in suppress_list]
            for f in decrypt_files:
                with prv_key.unlock(self.passphrase):
                    done = False
                    try:
                        encrypted_data = pgpy.PGPMessage.from_file(os.path.join(self.decrypt_path, f))
                    except ValueError:  # file is already decrypted
                        done = True

                    if not done:
                        decrypted_data = prv_key.decrypt(encrypted_data).message
                        if not isinstance(decrypted_data, bytearray):
                            decrypted_data = bytearray(decrypted_data, encoding='utf-8')  # convert to bytes otherwise there's an extra <CR>
                        decrypted_name = f.replace(f'.{self.extension}', '')
                        decrypted_file = os.path.join(self.decrypt_path, decrypted_name)
                        with open(decrypted_file, 'wb') as df:
                            df.write(decrypted_data)

                        if archive:
                            archive_dir = os.path.join(self.decrypt_path, 'Archive')
                            if os.path.isdir(archive_dir):
                                archive_name = os.path.join(archive_dir, f)
                                os.rename(os.path.join(self.decrypt_path, f), archive_name)
