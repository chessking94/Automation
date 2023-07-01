# import logging
import os
import unittest

from src.cmd import cmd

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files')


class TestCmd(unittest.TestCase):
    def test_run_script_with_parameters(self):
        script = cmd()
        test_val = script.run_script('py', FILE_DIR, 'cmd_script.py', '-a1 -b2')

        self.assertEqual(test_val, 0)

    def test_run_script_without_parameters(self):
        script = cmd()
        test_val = script.run_script('py', FILE_DIR, 'cmd_script.py')

        self.assertNotEqual(test_val, 0)

    def test_run_script_without_program_name(self):
        script = cmd()
        test_val = script.run_script(None, FILE_DIR, 'cmd_script.bat')

        self.assertEqual(test_val, 0)

    def test_run_script_with_invalid_script_path(self):
        script = cmd()
        self.assertRaises(FileNotFoundError, script.run_script, 'py', FILE_DIR, 'dne.py')


if __name__ == '__main__':
    unittest.main()
