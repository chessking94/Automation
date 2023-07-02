# import logging
import os
import unittest

from src.cmd import cmd

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files')


class TestCmd(unittest.TestCase):
    def setUp(self):
        self.script = cmd()

    def test_run_script_with_parameters(self):
        test_val = self.script.run_script('py', FILE_DIR, 'cmd_script.py', '-a1 -b2')
        self.assertEqual(test_val, 0)

    def test_run_script_without_parameters(self):
        test_val = self.script.run_script('py', FILE_DIR, 'cmd_script.py')
        self.assertNotEqual(test_val, 0)

    def test_run_script_without_program_name(self):
        test_val = self.script.run_script(None, FILE_DIR, 'cmd_script.bat')
        self.assertEqual(test_val, 0)

    def test_run_script_with_invalid_script_path(self):
        self.assertRaises(FileNotFoundError, self.script.run_script, 'py', FILE_DIR, 'dne.py')


if __name__ == '__main__':
    unittest.main()
