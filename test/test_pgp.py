# import logging
import os
import unittest

import src.pgp as pgp

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'pgp')


class TestPgp(unittest.TestCase):
    def setUp(self):
        self.proc = pgp.pgp('Test')
        self.file_list = []

    def tearDown(self):
        for f in self.file_list:
            if os.path.isfile(f):
                os.remove(f)

    # encryption
    def test_encrypt_invalid_path(self):
        bad_path = '/this/path/is/bad'
        self.assertRaises(FileNotFoundError, self.proc.encrypt, bad_path)

    def test_encrypt_file_already_encrypted(self):
        fname = 'encryption_test1.txt.pgp'
        with self.assertLogs(level='WARNING') as log:
            self.file_list = self.proc.encrypt(FILE_DIR, fname, False)
            self.assertEqual(len(self.file_list), 0)
            self.assertIn('File is already encrypted', log.output[0])

    def test_encrypt_one_file(self):
        fname = 'encryption_test2.txt'
        self.file_list = self.proc.encrypt(FILE_DIR, fname, False)
        self.assertEqual(len(self.file_list), 1)

    def test_encrypt_multiple_files(self):
        flist = ['encryption_test2.txt', 'encryption_test3.txt']
        self.file_list = self.proc.encrypt(FILE_DIR, flist, False)
        self.assertEqual(len(self.file_list), len(flist))

    def test_encrypt_wildcard_file(self):
        file_wc = 'encryption_test*.txt'
        self.file_list = self.proc.encrypt(FILE_DIR, file_wc, False)
        self.assertEqual(len(self.file_list), 2)

    def test_encrypt_directory(self):
        self.file_list = self.proc.encrypt(FILE_DIR, None, False)
        self.assertEqual(len(self.file_list), 3)

    # decryption
    def test_decrypt_invalid_path(self):
        bad_path = '/this/path/is/bad'
        self.assertRaises(FileNotFoundError, self.proc.decrypt, bad_path)

    def test_decrypt_file_already_decrypted(self):
        fname = 'decryption_test1.txt'
        with self.assertLogs(level='WARNING') as log:
            self.file_list = self.proc.decrypt(FILE_DIR, fname, False)
            self.assertEqual(len(self.file_list), 0)
            self.assertIn('File is already decrypted', log.output[0])

    def test_decrypt_one_file(self):
        fname = 'decryption_test2.txt.pgp'
        self.file_list = self.proc.decrypt(FILE_DIR, fname, False)
        self.assertEqual(len(self.file_list), 1)

    def test_decrypt_multiple_files(self):
        flist = ['decryption_test2.txt.pgp', 'decryption_test3.txt.pgp']
        self.file_list = self.proc.decrypt(FILE_DIR, flist, False)
        self.assertEqual(len(self.file_list), len(flist))

    def test_decrypt_wildcard_file(self):
        file_wc = 'decryption_test*.txt.pgp'
        self.file_list = self.proc.decrypt(FILE_DIR, file_wc, False)
        self.assertEqual(len(self.file_list), 2)

    def test_decrypt_directory(self):
        self.file_list = self.proc.encrypt(FILE_DIR, None, False)
        self.assertEqual(len(self.file_list), 3)


if __name__ == '__main__':
    unittest.main()
