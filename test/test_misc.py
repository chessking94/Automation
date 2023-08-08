import os
import unittest

import src.misc as misc

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'misc')


class TestMisc(unittest.TestCase):
    def test_get_config_no_file(self):
        self.assertRaises(FileNotFoundError, misc.get_config, 'Test', '')

    def test_get_config_missing_key(self):
        test_val = misc.get_config('DNE', os.path.join(FILE_DIR, 'test_config.json'))
        self.assertIsNone(test_val)

    def test_get_config(self):
        test_val = misc.get_config('Key', os.path.join(FILE_DIR, 'test_config.json'))
        self.assertEqual(test_val, 'Value')

    def test_csv_to_json(self):
        csvfile = os.path.join(FILE_DIR, 'csvjsonconvert.csv')
        csv_dict = {'value1': {'column2': 'value2', 'column3': 'value3'}}
        self.assertEqual(misc.csv_to_json(csvfile), csv_dict)

    def test_csv_to_json_dup_key(self):
        csvfile = os.path.join(FILE_DIR, 'csvjsonconvert_fail.csv')
        self.assertRaises(ValueError, misc.csv_to_json, csvfile)

    def test_csv_to_json_invalid_delim(self):
        csvfile = os.path.join(FILE_DIR, 'csvjsonconvert.csv')
        self.assertRaises(NotImplementedError, misc.csv_to_json, csvfile, 'a')


if __name__ == '__main__':
    unittest.main()
