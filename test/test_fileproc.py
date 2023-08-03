import os
import shutil
import unittest

import src.fileproc as fileproc
from src.misc import get_config

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'fileproc')


class TestManipulate(unittest.TestCase):
    def setUp(self):
        self.fp = fileproc.manipulate()
        self.file_list = []

    def tearDown(self):
        for f in self.file_list:
            if os.path.isfile(f):
                os.remove(f)

    def test_mergecsvfiles_invalid_dir(self):
        bad_dir = '/this/path/is/bad'
        self.assertRaises(FileNotFoundError, self.fp.mergecsvfiles, bad_dir, 'fileproc_test*.txt', True, ',')

    def test_mergecsvfiles(self):
        merge_name = 'mergedfile.txt'
        result_file = self.fp.mergecsvfiles(FILE_DIR, 'fileproc_test*.txt', merge_name, True, ',')
        self.file_list.append(result_file)
        self.assertEqual(os.path.normpath(result_file), os.path.join(FILE_DIR, merge_name))

    def test_wildcardcopy_invalid_src(self):
        bad_src = '/this/path/is/bad'
        self.assertRaises(FileNotFoundError, self.fp.wildcardcopy, bad_src, os.getcwd(), '*.txt')

    def test_wildcardcopy_invalid_dest(self):
        bad_dest = '/this/path/is/bad'
        self.assertRaises(FileNotFoundError, self.fp.wildcardcopy, os.getcwd(), bad_dest, '*.txt')

    def test_wildcardcopy(self):
        self.file_list = self.fp.wildcardcopy(FILE_DIR, os.path.dirname(FILE_DIR), '*.txt')
        self.assertEqual(len(self.file_list), 2)


class TestMonitoring(unittest.TestCase):
    def test_monitoring_invalid_path(self):
        self.assertRaises(FileNotFoundError, fileproc.monitoring, '/this/path/is/bad')

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
            self.assertRaises(RuntimeError, fileproc.monitoring, test_path)
            if os.path.isdir(test_path):
                shutil.rmtree(test_path)
        else:
            self.assertEqual(1, 1)  # path was invalid and threw an exception, consider the test successful

    def test_monitoring(self):
        monit = fileproc.monitoring(path=FILE_DIR)
        dt = '1970-01-01 00:00:00'
        monit.change_time(dt)
        files = monit.modified_files()
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0], 'fileproc_testfile.txt')
        self.assertEqual(files[1], 'fileproc_testfile2.txt')


if __name__ == '__main__':
    unittest.main()
