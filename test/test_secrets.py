import os
import unittest

from src.misc import get_config
import src.secrets as secrets

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'secrets')


class TestKeepass(unittest.TestCase):
    def setUp(self):
        self.filename = get_config('keepassFile')
        self.password = os.getenv('AUTOMATIONPASSWORD')
        self.group_title = 'test'
        self.entry_title = 'Testing Entry'

    def test_validategroup_missing(self):
        bad_group = 'DNE'
        self.assertRaises(ValueError, secrets.keepass, self.filename, self.password, bad_group, self.entry_title)

    def test_validateentry_missing(self):
        bad_entry = 'DNE'
        self.assertRaises(ValueError, secrets.keepass, self.filename, self.password, self.group_title, bad_entry)

    def test_missing_database(self):
        bad_filename = 'DNE.kdbx'
        self.assertRaises(FileNotFoundError, secrets.keepass, bad_filename, self.password, self.group_title, self.entry_title)

    def test_getgeneral_invalid_field(self):
        kp = secrets.keepass(self.filename, self.password, self.group_title, self.entry_title)
        self.assertRaises(NotImplementedError, kp.getgeneral, 'DNE')

    def test_getgeneral(self):
        kp = secrets.keepass(self.filename, self.password, self.group_title, self.entry_title)
        test_val = kp.getgeneral('username')
        self.assertEqual(test_val, 'username')

    def test_getcustomproperties_invalid_field(self):
        kp = secrets.keepass(self.filename, self.password, self.group_title, self.entry_title)
        self.assertRaises(NotImplementedError, kp.getcustomproperties, 'DNE')

    def test_getcustomproperties(self):
        kp = secrets.keepass(self.filename, self.password, self.group_title, self.entry_title)
        test_val = kp.getcustomproperties('Test')
        self.assertEqual(test_val, 'Test')

    def test_readattachment_missing(self):
        kp = secrets.keepass(self.filename, self.password, self.group_title, self.entry_title)
        self.assertRaises(IndexError, kp.readattachment, 'DNE.txt')

    def test_readattachment(self):
        kp = secrets.keepass(self.filename, self.password, self.group_title, self.entry_title)
        test_val = kp.readattachment('Test.txt')
        self.assertEqual(test_val, 'Test')


if __name__ == '__main__':
    unittest.main()
