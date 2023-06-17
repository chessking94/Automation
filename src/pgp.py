"""pgp

Author: Ethan Hunt
Date: 2023-06-14
Version: 1.0

"""

import datetime as dt
import fnmatch
import logging
import os

import pgpy

from .constants import BOOLEANS as BOOLEANS
from .misc import get_config as get_config


class pgp_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
    DELIM = get_config(MODULE_NAME, 'logDelimiter')


class pgp:
    def __init__(self, profile: dict):
        self.name = profile.get('Name').strip().upper()
        self.active = profile.get('Active').strip()
        self.active = True if self.active == '1' else False
        self.type = profile.get('Type').strip().upper()
        self.type = self.type if self.type in ['PUBLIC', 'PRIVATE'] else 'PUBLIC'
        self.extension = profile.get('Extension').strip()
        self.encrypt_path = profile.get('EncryptPath').strip()
        self.decrypt_path = profile.get('DecryptPath').strip()

        suppress_delimiter = get_config(pgp_constants.MODULE_NAME, 'suppressDelimiter')
        self.suppress_encrypt = profile.get('SuppressEncrypt').strip(f"'{suppress_delimiter} '")
        self.suppress_encrypt = self.suppress_encrypt.split(suppress_delimiter)
        self.suppress_encrypt.append(f'*.{self.extension}')
        self.suppress_decrypt = profile.get('SuppressDecrypt').strip(f"'{suppress_delimiter} '")
        self.suppress_decrypt = self.suppress_decrypt.split(suppress_delimiter)

        self.public_file = os.path.join(get_config(pgp_constants.MODULE_NAME, 'publicPath'), f'{self.name}_public.asc')
        self.private_file = os.path.join(get_config(pgp_constants.MODULE_NAME, 'privatePath'), f'{self.name}_private.asc')
        self.passphrase_file = os.path.join(get_config(pgp_constants.MODULE_NAME, 'passphrasePath'), f'{self.name}_passphrase.txt')

        self.error = None
        self.log_path = get_config(pgp_constants.MODULE_NAME, 'logPath')
        self.log_name = f"{get_config(pgp_constants.MODULE_NAME, 'logName')}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"

    def validate_profile(self) -> str:
        if not self.active:
            self.error = f'Inactive profile|{self.name}'

        if self.type == 'PUBLIC' and not os.path.isdir(self.encrypt_path):
            self.error = f'Encryption path does not exist|{self.name}'

        if self.type == 'PRIVATE' and not os.path.isdir(self.decrypt_path):
            self.error = f'Decryption path does not exist|{self.name}'

        if self.error is not None:
            logging.critical(self.error)

        return self.error

    def encrypt(self, archive: bool = True):
        archive = archive if archive in BOOLEANS else False

        if self.error is None:
            pub_key, _ = pgpy.PGPKey.from_file(self.public_file)
            directory_list = [f for f in os.listdir(self.encrypt_path) if os.path.isfile(os.path.join(self.encrypt_path, f))]
            suppress_list = []
            for f in os.listdir(self.encrypt_path):
                if os.path.isfile(os.path.join(self.encrypt_path, f)):
                    for suppress_item in self.suppress_encrypt:
                        if fnmatch.fnmatch(f, suppress_item):
                            suppress_list.append(f)
            encrypt_files = [x for x in directory_list if x not in suppress_list]
            # TODO: Exclude files already encrypted
            for f in encrypt_files:
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
        archive = archive if archive in BOOLEANS else False

        if self.error is None:
            with open(self.passphrase_file, 'r') as ppfp:
                passphrase = ppfp.readline().strip()

            prv_key, _ = pgpy.PGPKey.from_file(self.private_file)
            directory_list = [f for f in os.listdir(self.decrypt_path) if os.path.isfile(os.path.join(self.decrypt_path, f))]
            suppress_list = []
            for f in os.listdir(self.decrypt_path):
                if os.path.isfile(os.path.join(self.decrypt_path, f)):
                    for suppress_item in self.suppress_decrypt:
                        if fnmatch.fnmatch(f, suppress_item):
                            suppress_list.append(f)
            decrypt_files = [x for x in directory_list if x not in suppress_list]

            for f in decrypt_files:
                with prv_key.unlock(passphrase):
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
