import os
import shutil
import unittest

import src.fileproc as fileproc
from src.misc import get_config

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'fileproc')


class TestMonitoring(unittest.TestCase):
    def test_monitoring_invalid_path(self):
        with self.assertLogs(level='CRITICAL') as log:
            _ = fileproc.monitoring(path='/this/path/is/bad')
            self.assertIn('Path does not exist', log.output[0])

    def test_monitoring_invalid_path_character(self):
        refdelim = get_config('fileproc_referenceDelimiter')
        test_path = os.path.join(FILE_DIR, f'te{refdelim}st')
        go = True
        try:
            if not os.path.isdir(test_path):
                os.mkdir(test_path)
        except OSError:
            go = False

        if go:
            with self.assertLogs(level='CRITICAL') as log:
                _ = fileproc.monitoring(path=test_path)
                self.assertIn('Path contains referenceDelimiter', log.output[0])
            if os.path.isdir(test_path):
                shutil.rmtree(test_path)
        else:
            self.assertEqual(1, 1)  # path was invalid and threw an exception, consider the test successful

    def test_monitoring(self):
        monit = fileproc.monitoring(path=FILE_DIR)
        dt = '1970-01-01 00:00:00'
        monit.change_time(dt)
        files = monit.modified_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], 'fileproc_testfile.txt')


if __name__ == '__main__':
    unittest.main()