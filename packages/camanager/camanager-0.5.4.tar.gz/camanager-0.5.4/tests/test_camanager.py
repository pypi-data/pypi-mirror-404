import datetime
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock, call

from src.camanager.masterkey import MasterKeyHelper
from .data import *
from src.camanager import camanager
from src.camanager.models import DATABASE_FILENAME, CA, Certificate, Config, ConfigType, CRLSigningCertificate
from src.camanager.models import database

def create_default_config(database_ctx, password='test'):
    masterkey_helper = MasterKeyHelper()
    master_key, password_salt = masterkey_helper.generate_new_to_b64(password)

    with database_ctx:
        # Create the config
        Config.create(
            name='default_key_size',
            type=ConfigType.INT,
            value=4096
        )

        Config.create(
            name='default_hash_algo',
            type=ConfigType.STRING,
            value='sha256'
        )

        Config.create(
            name='default_validity_seconds',
            type=ConfigType.INT,
            value=390 * 24 * 60 * 60  # 390 days (Safari allows until 398 days)
        )

        Config.create(
            name='password_salt',
            type=ConfigType.BINARY,
            value=password_salt
        )

        Config.create(
            name='encrypted_masterkey',
            type=ConfigType.STRING,
            value=master_key
        )

class TestCreateVault(unittest.TestCase):
    def setUp(self) -> None:
        try:
            os.remove(DATABASE_FILENAME)
        except FileNotFoundError:
            pass

    @patch('sys.stderr', new_callable=StringIO)
    def test_create_vault_file_already_existing(self,  mock_stderr):
        with open(DATABASE_FILENAME, 'w') as f:
            f.write('')

        cam = camanager.CAManager()

        with self.assertRaises(SystemExit) as cm:
            cam.create_vault()

        self.assertEqual(f'Vault "{DATABASE_FILENAME}" is already existing\n', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

        os.remove(DATABASE_FILENAME)

class TestAddCa(unittest.TestCase):
    def setUp(self) -> None:
        try:
            os.remove(DATABASE_FILENAME)
        except FileNotFoundError:
            pass

        database.init(DATABASE_FILENAME)

        with database:
            database.create_tables([CA, Certificate, CRLSigningCertificate, Config])
            create_default_config(database)

    def tearDown(self) -> None:
        try:
            os.remove(DATABASE_FILENAME)
        except FileNotFoundError:
            pass

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_name_already_in_use(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        database.init(DATABASE_FILENAME)

        with database:
            CA.create(name='MyCAName',
                      cert=load_txt('tests/data/ca.pem'),
                      key=load_txt('tests/data/ca.key'),
                      is_intermediate=False,
                      crl_output_filename='crl.pem').save()

        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('This name is already in use. Please choose a different name', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)


    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_nopem(self,  mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write('bad line')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid PEM certificate', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)


    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_badpem(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write('-----BEGIN CERTIFICATE-----\n*** FAKE LINE 1 ***\n*** FAKE LINE 2 ***\n'
                                '-----END CERTIFICATE-----\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid PEM certificate', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

        os.remove(DATABASE_FILENAME)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_key_nopem(self,  mock_stderr,  mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write('bad line')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid PEM key or password', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_key_badpem(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write('-----BEGIN RSA PRIVATE KEY-----\n*** FAKE LINE 1 ***\n*** FAKE LINE 2 ***\n'
                                '-----END RSA PRIVATE KEY-----\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid PEM key or password', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)


    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_ca_key_not_matching(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/pkey.key'))
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('The certificate and the private key are not corresponding', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_ca_key_crl_badpem(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/ca.key'))
                sys.stdin.write('y\n')
                sys.stdin.write('***BAMPEM***\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid PEM certificate', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_ca_key_crl_badkey(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/ca.key'))
                sys.stdin.write('y\n')
                sys.stdin.write(load_txt('tests/data/crl_signer.pem'))
                sys.stdin.write('***BAMKEY***\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid PEM key or password', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_ca_key_crl_key_not_matching(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/ca.key'))
                sys.stdin.write('y\n')
                sys.stdin.write(load_txt('tests/data/crl_signer.pem'))
                sys.stdin.write(load_txt('tests/data/pkey.key'))
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('The certificate and the private key are not corresponding', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)


    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_ca_key_crl_not_signed_by_ca(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/ca.key'))
                sys.stdin.write('y\n')
                sys.stdin.write(load_txt('tests/data/crl_signer.pem'))
                sys.stdin.write(load_txt('tests/data/crl_signer.key'))
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('The CRL certificate is not signed by the CA', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_crl_output_is_dir(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        temp_dir = tempfile.mkdtemp(suffix='.pem')
        os.makedirs(temp_dir, exist_ok=True)

        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca2.pem'))
                sys.stdin.write(load_txt('tests/data/ca2.key'))
                sys.stdin.write('n\n')
                sys.stdin.write(f'{temp_dir}\n')
                sys.stdin.seek(0)
                cam.add_ca()

        self.assertEqual('The provided output path is a directory', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

        os.removedirs(temp_dir)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_crl_url_not_in_ca_empty_url(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit):
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/ca.key'))
                sys.stdin.write('n\n')
                sys.stdin.write(f'crl.pem\n')
                sys.stdin.write('\n')
                sys.stdin.write('\n')
                sys.stdin.write('y\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertTrue('Enter the CRL URL' in mock_stdout.getvalue())

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_crl_url_not_in_ca_bad_url(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca.pem'))
                sys.stdin.write(load_txt('tests/data/ca.key'))
                sys.stdin.write('n\n')
                sys.stdin.write(f'crl.pem\n')
                sys.stdin.write('http // badurl.com\n')

                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid CRL URL', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_crl_url_in_ca(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit):
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca2.pem'))
                sys.stdin.write(load_txt('tests/data/ca2.key'))
                sys.stdin.write('n\n')
                sys.stdin.write(f'crl.pem\n')
                sys.stdin.write('\n')
                sys.stdin.write('y\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertTrue('Enter the CRL URL' not in mock_stdout.getvalue())

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_bad_ocsp_url(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca2.pem'))
                sys.stdin.write(load_txt('tests/data/ca2.key'))
                sys.stdin.write('n\n')
                sys.stdin.write(f'crl.pem\n')
                sys.stdin.write('bad OCSP url\n')
                sys.stdin.write('y\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('Invalid OCSP responder URL', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_script(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdin', new_callable=StringIO):
                sys.stdin.write('MyCAName\n')
                sys.stdin.write(load_txt('tests/data/ca2.pem'))
                sys.stdin.write(load_txt('tests/data/ca2.key'))
                sys.stdin.write('n\n')
                sys.stdin.write(f'crl.pem\n')
                sys.stdin.write('http://ocsp.example.com\n')
                sys.stdin.write('not_existing_script.bat\n')
                sys.stdin.seek(0)

                cam.add_ca()

        self.assertEqual('This path is invalid', mock_stderr.getvalue())
        self.assertEqual(-1, cm.exception.code)

    @patch('src.camanager.utils.ask_password', return_value='test')
    @patch('getpass.fallback_getpass', return_value='test')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_add_ca_script(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
        temp_script_fd, temp_script_path = tempfile.mkstemp()
        os.close(temp_script_fd)

        cam = camanager.CAManager()
        cam.load(dont_load_ca=True)

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write('MyCAName\n')
            sys.stdin.write(load_txt('tests/data/ca2.pem'))
            sys.stdin.write(load_txt('tests/data/ca2.key'))
            sys.stdin.write('y\n')
            sys.stdin.write(load_txt('tests/data/crl_signer.pem'))
            sys.stdin.write(load_txt('tests/data/crl_signer.key'))
            sys.stdin.write(f'crl.pem\n')
            sys.stdin.write('http://ocsp.example.com\n')
            sys.stdin.write(f'{temp_script_path}\n')
            sys.stdin.write(f'y\n')
            sys.stdin.seek(0)

            cam.add_ca()

        os.remove(temp_script_path)

        database.init(DATABASE_FILENAME)
        with database:
            self.assertEqual(CA.get(name='MyCAName').crl_post_script_path, temp_script_path.lower())
            self.assertEqual(CA.get(name='MyCAName').ocsp_url, 'http://ocsp.example.com')
            self.assertEqual(CA.get(name='MyCAName').crl_url, 'http://crl.example.com/crl.pem')
            self.assertEqual(CA.get(name='MyCAName').crl_output_filename, 'crl.pem')



    # @patch('src.camanager.utils.ask_password', return_value='test')
    # @patch('getpass.fallback_getpass', return_value='test')
    # @patch('sys.stdout', new_callable=StringIO)
    # @patch('sys.stderr', new_callable=StringIO)
    # def test_add_ca_ask_crl_path(self, mock_stderr, mock_stdout, mock_getpass, mock_askpassword):
    #     cam = camanager.CAManager()
    #     cam.load(dont_load_ca=True)
    #
    #     with self.assertRaises(SystemExit) as cm:
    #         with patch('sys.stdin', new_callable=StringIO):
    #             sys.stdin.write('MyCAName\n')
    #             sys.stdin.write(load_txt('tests/data/ca2.pem'))
    #             sys.stdin.write(load_txt('tests/data/ca2.key'))
    #             sys.stdin.write('n\n')
    #             sys.stdin.write('crl.pem\n')
    #
    #             try:
    #                 cam.add_ca()
    #             except EOFError:
    #                 pass
    #
    #     self.assertEqual('Enter the CRL URL (if not used, leave empty)', mock_stdout.getvalue())
#
# class TestLoadVault(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_load_vault_not_existing(self, mock_stderr):
#         cam = CAManager()
#
#         with self.assertRaises(SystemExit) as cm:
#             cam.load()
#
#         self.assertIn("doesn't exist yet", mock_stderr.getvalue())
#         self.assertEqual(-1, cm.exception.code)
#
#     @patch('src.camanager.utils.ask_password', return_value='test')
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_load_vault_no_ca(self, mock_stderr, mock_password):
#         # Create empty vault
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#         cam = CAManager()
#         with self.assertRaises(SystemExit) as cm:
#             cam.load()
#
#         self.assertIn("doesn't contains a CA", mock_stderr.getvalue())
#         self.assertEqual(-1, cm.exception.code)
# #
#
# class TestAddCA(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stderr', new_callable=StringIO)
#     @patch('builtins.input', return_value='TestCA')
#     # def test_add_ca_duplicate_name(self, mock_input, mock_stderr):
#     #     # Create vault with CA
#     #     from src.camanager.models import database
#     #     print('A')
#     #     database.init(DATABASE_FILENAME)
#     #     print('B')
#     #     with database:
#     #         print('B1')
#     #         database.create_tables([CA, Certificate, Config])
#     #         print('B2')
#     #         CA.create(name='TestCA', is_default=True, is_intermediate=False,
#     #                   cert=data.load_txt('data/ca.pem'),
#     #                   key=data.load_txt('data/ca.key').encode('utf8'),
#     #                   crl_output_filename='test.pem')
#     #         print('B3')
#     #     print('C')
#     #     cam = CAManager()
#     #     with self.assertRaises(SystemExit) as cm:
#     #         cam.add_ca()
#     #     print('D')
#     #     self.assertIn('already in use', mock_stderr.getvalue())
#     #     self.assertEqual(-1, cm.exception.code)
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_add_ca_cert_key_mismatch(self, mock_stderr):
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#         cam = CAManager()
#
#         with patch('builtins.input', return_value='NewCA'):
#             with patch('sys.stdin', new_callable=StringIO):
#                 sys.stdin.write(data.load_txt('data/ca.pem'))
#                 sys.stdin.write(data.load_txt('data/pkey.key'))
#                 sys.stdin.seek(0)
#
#                 with self.assertRaises(SystemExit) as cm:
#                     cam.add_ca()
#
#                 self.assertIn('not corresponding', mock_stderr.getvalue())
#                 self.assertEqual(-1, cm.exception.code)
#
#
# class TestListCertificates(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         # Create test vault
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stdout', new_callable=StringIO)
#     def test_list_no_certificates(self, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#         cam.list()
#
#         self.assertIn('No certificate found', mock_stdout.getvalue())
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @freeze_time("2024-01-01")
#     def test_list_valid_certificates(self, mock_stdout):
#         # Add a valid certificate
#         Certificate.create(
#             ca=self.ca,
#             cn='test.example.com',
#             san='DNS:test.example.com',
#             created_timestamp=datetime.datetime.now(),
#             not_after=datetime.datetime.now() + datetime.timedelta(days=365),
#             serial='01:02:03:04:05:06:07:08',
#             cert=data.load_txt('data/cert.pem'),
#             key=None,
#             is_revoked=False,
#             is_renewed=False
#         )
#
#         cam = CAManager()
#         cam.ca = self.ca
#         cam.list()
#
#         output = mock_stdout.getvalue()
#         self.assertIn('1 certificate found', output)
#         self.assertIn('test.example.com', output)
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @freeze_time("2024-01-01")
#     def test_list_soon_expired(self, mock_stdout):
#         # Add certificate expiring soon
#         Certificate.create(
#             ca=self.ca,
#             cn='expiring.example.com',
#             san='DNS:expiring.example.com',
#             created_timestamp=datetime.datetime.now(),
#             not_after=datetime.datetime.now() + datetime.timedelta(days=15),
#             serial='01:02:03:04:05:06:07:09',
#             cert=data.load_txt('data/cert.pem'),
#             key=None,
#             is_revoked=False,
#             is_renewed=False
#         )
#
#         cam = CAManager()
#         cam.ca = self.ca
#         cam.list(only_soon_expired=True)
#
#         output = mock_stdout.getvalue()
#         self.assertIn('1 certificate found', output)
#         self.assertIn('expiring.example.com', output)
#
#     def test_list_conflicting_params(self):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with self.assertRaises(RuntimeError):
#             cam.list(all_certificates=True, only_soon_expired=True)
#
#
# class TestGenerateNewCert(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             Config.create(name='default_key_size', type=ConfigType.INT, value=2048)
#             Config.create(name='default_hash_algo', type=ConfigType.STRING, value='sha256')
#             Config.create(name='default_validity_seconds', type=ConfigType.INT, value=365 * 24 * 60 * 60)
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem',
#                 crl_url='http://crl.example.com',
#                 ocsp_url='http://ocsp.example.com'
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @patch('src.camanager.camanager.CAManager._get_ca_key')
#     @patch('src.camanager.utils.confirm', side_effect=[True, True, False])
#     @patch('builtins.input', side_effect=['test.example.com', '', ''])
#     def test_generate_new_cert_default_params(self, mock_input, mock_confirm, mock_get_key, mock_stdout):
#         mock_get_key.return_value = data.get_ca_privatekey_obj()
#
#         cam = CAManager()
#         cam.ca = self.ca
#         cam.ca.load_cert()
#
#         cam.generate_new_cert()
#
#         output = mock_stdout.getvalue()
#         self.assertIn('Certificate successfully created', output)
#
#         # Verify certificate was saved
#         cert = Certificate.select().where(Certificate.cn == 'test.example.com').first()
#         self.assertIsNotNone(cert)
#         self.assertEqual(cert.cn, 'test.example.com')
#
#
# class TestSignCSR(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             Config.create(name='default_validity_seconds', type=ConfigType.INT, value=365 * 24 * 60 * 60)
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_sign_csr_file_not_found(self, mock_stderr):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with self.assertRaises(SystemExit) as cm:
#             cam.sign_csr('/nonexistent/file.csr')
#
#         self.assertIn("doesn't exist", mock_stderr.getvalue())
#         self.assertEqual(-1, cm.exception.code)
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_sign_csr_invalid_pem(self, mock_stderr):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with patch('sys.stdin', new_callable=StringIO):
#             sys.stdin.write('-----BEGIN CERTIFICATE REQUEST-----\nINVALID\n-----END CERTIFICATE REQUEST-----\n')
#             sys.stdin.seek(0)
#
#             with self.assertRaises(SystemExit) as cm:
#                 cam.sign_csr()
#
#             self.assertIn('Invalid PEM CSR', mock_stderr.getvalue())
#             self.assertEqual(-1, cm.exception.code)
#
#
# class TestRenewCertificate(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             Config.create(name='default_validity_seconds', type=ConfigType.INT, value=365 * 24 * 60 * 60)
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#             self.cert = Certificate.create(
#                 ca=self.ca,
#                 cn='test.example.com',
#                 san='DNS:test.example.com',
#                 created_timestamp=datetime.datetime.now(),
#                 not_after=datetime.datetime.now() + datetime.timedelta(days=30),
#                 serial='01:02:03:04:05:06:07:08',
#                 cert=data.load_txt('data/cert.pem'),
#                 key=data.load_txt('data/pkey.key'),
#                 is_revoked=False,
#                 is_renewed=False
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_renew_cert_no_private_key(self, mock_stderr):
#         # Create cert without key
#         cert_no_key = Certificate.create(
#             ca=self.ca,
#             cn='nokey.example.com',
#             san='DNS:nokey.example.com',
#             created_timestamp=datetime.datetime.now(),
#             not_after=datetime.datetime.now() + datetime.timedelta(days=30),
#             serial='01:02:03:04:05:06:07:10',
#             cert=data.load_txt('data/cert.pem'),
#             key=None,
#             is_revoked=False,
#             is_renewed=False
#         )
#
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with self.assertRaises(SystemExit) as cm:
#             cam.renew(str(cert_no_key.id))
#
#         self.assertIn('No private key stored', mock_stderr.getvalue())
#         self.assertEqual(-1, cm.exception.code)
#
#
# class TestExportCertificate(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#             self.cert = Certificate.create(
#                 ca=self.ca,
#                 cn='test.example.com',
#                 san='DNS:test.example.com',
#                 created_timestamp=datetime.datetime.now(),
#                 not_after=datetime.datetime.now() + datetime.timedelta(days=365),
#                 serial='01:02:03:04:05:06:07:08',
#                 cert=data.load_txt('data/cert.pem'),
#                 key=data.load_txt('data/pkey.key'),
#                 is_revoked=False,
#                 is_renewed=False
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     def test_export_invalid_format(self):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with self.assertRaises(ValueError):
#             cam.export(str(self.cert.id), 'invalid', None)
#
#     @patch('sys.stdout', new_callable=StringIO)
#     def test_export_pem_to_stdout(self, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with patch('src.camanager.utils.ask_password', return_value='test'):
#             cam.export(str(self.cert.id), 'pem', None)
#
#         output = mock_stdout.getvalue()
#         self.assertIn('BEGIN CERTIFICATE', output)
#         self.assertIn('BEGIN', output)
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @patch('src.camanager.utils.ask_password', return_value='password')
#     def test_export_p12_with_password(self, mock_password, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with tempfile.TemporaryDirectory() as tmpdir:
#             output_path = os.path.join(tmpdir, 'test')
#             cam.export(str(self.cert.id), 'p12', output_path)
#
#             self.assertTrue(os.path.exists(output_path + '.p12'))
#
#
# class TestRevokeCertificate(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#             self.cert = Certificate.create(
#                 ca=self.ca,
#                 cn='test.example.com',
#                 san='DNS:test.example.com',
#                 created_timestamp=datetime.datetime.now(),
#                 not_after=datetime.datetime.now() + datetime.timedelta(days=365),
#                 serial='01:02:03:04:05:06:07:08',
#                 cert=data.load_txt('data/cert.pem'),
#                 key=data.load_txt('data/pkey.key'),
#                 is_revoked=False,
#                 is_renewed=False
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @patch('src.camanager.camanager.CAManager.generate_crl')
#     @patch('src.camanager.utils.confirm', return_value=True)
#     @patch('builtins.input', side_effect=['Compromised', 'Security breach'])
#     def test_revoke_certificate(self, mock_input, mock_confirm, mock_gen_crl, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         cam.revoke(str(self.cert.id))
#
#         # Verify certificate was revoked
#         cert = Certificate.get_by_id(self.cert.id)
#         self.assertTrue(cert.is_revoked)
#         self.assertIsNotNone(cert.revoked_timestamp)
#         self.assertEqual(cert.revoked_comment, 'Security breach')
#
#         # Verify CRL generation was called
#         mock_gen_crl.assert_called_once()
#
#
# class TestGenerateCRL(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test_crl.pem',
#                 crl_url='http://crl.example.com'
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#         try:
#             os.remove('test_crl.pem')
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @patch('src.camanager.camanager.CAManager._get_ca_key')
#     def test_generate_crl(self, mock_get_key, mock_stdout):
#         mock_get_key.return_value = data.get_ca_privatekey_obj()
#
#         cam = CAManager()
#         cam.ca = self.ca
#         cam.ca.load_cert()
#
#         cam.generate_crl()
#
#         output = mock_stdout.getvalue()
#         self.assertIn('CRL successfully generated', output)
#         self.assertTrue(os.path.exists('test_crl.pem'))
#
#
# class TestAddExternal(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_add_external_file_not_found(self, mock_stderr):
#         print('AAAAA')
#         cam = CAManager()
#         cam.ca = self.ca
#
#         print('A')
#         with self.assertRaises(SystemExit) as cm:
#             print('B')
#             cam.add_external('/nonexistent/cert.pem')
#             print('C')
#         print('D')
#         self.assertIn("doesn't exist", mock_stderr.getvalue())
#         self.assertEqual(-1, cm.exception.code)
#
#     @patch('sys.stderr', new_callable=StringIO)
#     def test_add_external_invalid_pem(self, mock_stderr):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with patch('sys.stdin', new_callable=StringIO):
#             sys.stdin.write('-----BEGIN CERTIFICATE-----\nINVALID\n-----END CERTIFICATE-----\n')
#             sys.stdin.seek(0)
#
#             with self.assertRaises(SystemExit) as cm:
#                 cam.add_external()
#
#             self.assertIn('Invalid PEM CSR', mock_stderr.getvalue())
#             self.assertEqual(-1, cm.exception.code)
#
#
# class TestSelectCertificate(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#             self.cert1 = Certificate.create(
#                 ca=self.ca,
#                 cn='test1.example.com',
#                 san='DNS:test1.example.com',
#                 created_timestamp=datetime.datetime.now(),
#                 not_after=datetime.datetime.now() + datetime.timedelta(days=365),
#                 serial='01:02:03:04:05:06:07:08',
#                 cert=data.load_txt('data/cert.pem'),
#                 key=None,
#                 is_revoked=False,
#                 is_renewed=False
#             )
#
#             self.cert2 = Certificate.create(
#                 ca=self.ca,
#                 cn='test2.example.com',
#                 san='DNS:test2.example.com',
#                 created_timestamp=datetime.datetime.now(),
#                 not_after=datetime.datetime.now() + datetime.timedelta(days=365),
#                 serial='01:02:03:04:05:06:07:09',
#                 cert=data.load_txt('data/cert.pem'),
#                 key=None,
#                 is_revoked=False,
#                 is_renewed=False
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     def test_select_certificate_by_id(self):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         cert = cam.select_certificate(str(self.cert1.id))
#         self.assertEqual(cert.id, self.cert1.id)
#
#     @patch('sys.stdout', new_callable=StringIO)
#     def test_select_certificate_by_cn_single_match(self, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         cert = cam.select_certificate('test1')
#         self.assertEqual(cert.cn, 'test1.example.com')
#
#     @patch('sys.stdout', new_callable=StringIO)
#     def test_select_certificate_no_match(self, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         cert = cam.select_certificate('nonexistent')
#         self.assertIsNone(cert)
#         self.assertIn('No certificate found', mock_stdout.getvalue())
#
#     @patch('sys.stdout', new_callable=StringIO)
#     @patch('builtins.input', return_value=None)
#     def test_select_certificate_multiple_matches(self, mock_input, mock_stdout):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         mock_input.return_value = str(self.cert1.id)
#         cert = cam.select_certificate('test')
#
#         output = mock_stdout.getvalue()
#         self.assertIn('certificates found', output)
#
#
# class TestConfigMethods(unittest.TestCase):
#     def setUp(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#         from src.camanager.models import database
#         database.init(DATABASE_FILENAME)
#         with database:
#             database.create_tables([CA, Certificate, Config])
#
#             Config.create(name='test_int', type=ConfigType.INT, value=42)
#             Config.create(name='test_string', type=ConfigType.STRING, value='test')
#
#             self.ca = CA.create(
#                 name='TestCA',
#                 is_default=True,
#                 is_intermediate=False,
#                 cert=data.load_txt('data/ca.pem'),
#                 key=data.load_txt('data/ca.key').encode('utf8'),
#                 crl_output_filename='test.pem'
#             )
#
#     def tearDown(self):
#         try:
#             os.remove(DATABASE_FILENAME)
#         except FileNotFoundError:
#             pass
#
#     def test_get_config_int(self):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         value = cam._get_config('test_int')
#         self.assertEqual(value, 42)
#         self.assertIsInstance(value, int)
#
#     def test_get_config_string(self):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         value = cam._get_config('test_string')
#         self.assertEqual(value, 'test')
#         self.assertIsInstance(value, str)
#
#     def test_get_config_unknown(self):
#         cam = CAManager()
#         cam.ca = self.ca
#
#         with self.assertRaises(RuntimeError):
#             cam._get_config('nonexistent')