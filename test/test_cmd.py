# import logging
import os
import unittest

from src.cmd import cmd

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'cmd')


class TestCmd(unittest.TestCase):
    def setUp(self):
        self.cmdclass = cmd()

    def test_run_script_with_parameters(self):
        test_val = self.cmdclass.run_script('py', FILE_DIR, 'cmd_script.py', '-a1 -b2')
        self.assertEqual(test_val, 0)

    def test_run_script_without_parameters(self):
        test_val = self.cmdclass.run_script('py', FILE_DIR, 'cmd_script.py')
        self.assertNotEqual(test_val, 0)

    def test_run_script_without_program_name(self):
        test_val = self.cmdclass.run_script(None, FILE_DIR, 'cmd_script.bat')
        self.assertEqual(test_val, 0)

    def test_run_script_with_invalid_script_path(self):
        self.assertRaises(FileNotFoundError, self.cmdclass.run_script, 'py', FILE_DIR, 'dne.py')

    def test_run_command_invalid_command(self):
        self.assertRaises(RuntimeError, self.cmdclass.run_command, None, None)

    def test_run_command_invalid_path(self):
        self.assertRaises(FileNotFoundError, self.cmdclass.run_command, 'fake command', 'fake path')

    # intentionally omitting tests for valid run_command usage, intention is for it to be hook to run virtually anything


if __name__ == '__main__':
    unittest.main()
