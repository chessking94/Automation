import os
import unittest
from unittest.mock import patch, MagicMock

import src.sftp as sftp

FILE_DIR = os.path.join(os.path.dirname(__file__), 'files', 'sftp')

# I had ChatGPT write much of this for me, I have no idea what the F most of it is doing.


class TestSftp(unittest.TestCase):
    @patch('paramiko.SSHClient')
    def test_normal_connection(self, mock_sshclient):
        sftp_conn = sftp.sftp('Test Normal')
        ssh_client = mock_sshclient.return_value
        sftp_conn._connectssh()

        ssh_client.connect.assert_called_with(
            hostname=sftp_conn.host,
            port=sftp_conn.port,
            username=sftp_conn.usr,
            password=sftp_conn.pwd
        )

    @patch('paramiko.SSHClient')
    def test_key_connection(self, mock_sshclient):
        sftp_conn = sftp.sftp('Test Key')
        ssh_client = mock_sshclient.return_value
        sftp_conn._connectssh()

        ssh_client.connect.assert_called_with(
            hostname=sftp_conn.host,
            port=sftp_conn.port,
            username=sftp_conn.usr,
            password=sftp_conn.pwd,
            pkey=sftp_conn.private_key,
            passphrase=sftp_conn.passphrase
        )

    @patch('paramiko.SSHClient')
    def test_download_invalid_path(self, mock_sshclient):
        bad_path = '/this/path/is/bad'
        sftp_conn = sftp.sftp('Test Normal')
        ssh_client = mock_sshclient.return_value
        sftp_client = MagicMock()
        ssh_client.open_sftp.return_value = sftp_client
        sftp_conn._connectssh()

        self.assertRaises(FileNotFoundError, sftp_conn.download, None, bad_path, False, False)

    # TODO: Figure this mess out. It's beyond my understanding right now
    # @patch('paramiko.SSHClient')
    # def test_download(self, mock_sshclient):
    #     sftp_conn = sftp.sftp('Test Normal')
    #     ssh_client = mock_sshclient.return_value
    #     sftp_client = MagicMock()
    #     ssh_client.open_sftp.return_value = sftp_client
    #     sftp_conn._connectssh()

    @patch('paramiko.SSHClient')
    def test_upload_invalid_path(self, mock_sshclient):
        bad_path = '/this/path/is/bad'
        sftp_conn = sftp.sftp('Test Normal')
        ssh_client = mock_sshclient.return_value
        sftp_client = MagicMock()
        ssh_client.open_sftp.return_value = sftp_client
        sftp_conn._connectssh()
        self.assertRaises(FileNotFoundError, sftp_conn.upload, None, bad_path, None, False)

    # TODO: Figure this mess out. It's beyond my understanding right now
    # @patch('paramiko.SSHClient')
    # def test_upload(self, mock_sshclient):
    #     sftp_conn = sftp.sftp('Test Normal')
    #     ssh_client = mock_sshclient.return_value
    #     sftp_client = MagicMock()
    #     ssh_client.open_sftp.return_value = sftp_client
    #     sftp_conn._connectssh()


if __name__ == '__main__':
    unittest.main()
