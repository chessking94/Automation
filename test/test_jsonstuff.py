# import logging
import os
import unittest

import src.jsonstuff as jsonstuff

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files')


class TestJsonstuff(unittest.TestCase):
    def setUp(self):
        self.file_list = []

    def _resetfilelist(self):
        self.file_list = []

    def _deletefiles(self, files: list):
        for f in files:
            if os.path.isfile(f):
                os.remove(f)

    def test_reformat_json_invalid_path(self):
        self.assertRaises(FileNotFoundError, jsonstuff.reformat_json, '/this/path/is/bad')

    def test_reformat_json_invalid_file(self):
        self.assertRaises(FileNotFoundError, jsonstuff.reformat_json, os.getcwd(), 'dne.json')

    def test_reformat_json_single_file(self):
        self._resetfilelist()
        fname = 'jsonstuff_test1.json'
        self.file_list = jsonstuff.reformat_json(FILE_DIR, fname)

        self.assertEqual(len(self.file_list), 1)
        self._deletefiles(self.file_list)

    def test_reformat_json_already_formatted(self):
        self._resetfilelist()
        fname = 'jsonstuff_test2.json'
        self.file_list = jsonstuff.reformat_json(FILE_DIR, fname)

        self.assertEqual(len(self.file_list), 0)

    def test_reformat_json_multiple_files(self):
        self._resetfilelist()
        self.file_list = jsonstuff.reformat_json(FILE_DIR)

        self.assertEqual(len(self.file_list), 2)
        self._deletefiles(self.file_list)


if __name__ == '__main__':
    unittest.main()
