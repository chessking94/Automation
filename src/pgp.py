"""pgp

Author: Ethan Hunt
Date: 2023-06-14
Version: 1.0

"""

import csv
import datetime as dt
import logging
import os

import pgpy

import constants
import misc

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]
DELIM = misc.get_config(MODULE_NAME, 'logDelimiter')


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

        suppress_delimiter = misc.get_config(MODULE_NAME, 'suppressDelimiter')
        self.suppress_encrypt = profile.get('SuppressEncrypt').strip(f"'{suppress_delimiter} '")
        self.suppress_encrypt = self.suppress_encrypt.split(suppress_delimiter)
        self.suppress_decrypt = profile.get('SuppressDecrypt').strip(f"'{suppress_delimiter} '")
        self.suppress_decrypt = self.suppress_decrypt.split(suppress_delimiter)

        self.public_file = os.path.join(misc.get_config(MODULE_NAME, 'publicPath'), f'{self.name}_public.asc')
        self.private_file = os.path.join(misc.get_config(MODULE_NAME, 'privatePath'), f'{self.name}_private.asc')
        self.passphrase_file = os.path.join(misc.get_config(MODULE_NAME, 'passphrasePath'), f'{self.name}_passphrase.txt')

        self.error = None
        self.log_path = misc.get_config(MODULE_NAME, 'logPath')
        self.log_name = f"{misc.get_config(MODULE_NAME, 'logName')}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.log"

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
        archive = archive if archive in constants.BOOLEANS else False

        if self.error is None:
            pub_key, _ = pgpy.PGPKey.from_file(self.public_file)
            encrypt_files = [f for f in os.listdir(self.encrypt_path) if os.path.isfile(os.path.join(self.encrypt_path, f))]
            # TODO: Add support for suppress_encrypt
            # TODO: Exclude files with self.extension extension or those already encrypted
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
        archive = archive if archive in constants.BOOLEANS else False

        if self.error is None:
            with open(self.passphrase_file, 'r') as ppfp:
                passphrase = ppfp.readline().strip()

            prv_key, _ = pgpy.PGPKey.from_file(self.private_file)
            decrypt_files = [f for f in os.listdir(self.decrypt_path) if os.path.isfile(os.path.join(self.decrypt_path, f))]
            # TODO: Add support for suppress_decrypt
            for f in decrypt_files:
                with prv_key.unlock(passphrase):
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


def main():
    logging.basicConfig(
        format='%(funcName)s\t%(levelname)s\t%(message)s',
        level=logging.INFO
    )

    # TODO: Consider converting this to a SQL (Express) DB
    profile_file = misc.get_config(MODULE_NAME, 'profileList')
    with open(profile_file, encoding='utf-8') as f:
        dict_reader = csv.DictReader(f, delimiter=',', quotechar='"')
        profiles = [p for p in dict_reader]

    for profile in profiles:
        proc = pgp(profile)
        proc.validate_profile()
        # proc.encrypt()
        proc.decrypt()


if __name__ == '__main__':
    main()
