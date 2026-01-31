import unittest
import base64
from unittest.mock import patch, MagicMock
from io import StringIO

from src.camanager.masterkey import MasterKeyHelper
from src.camanager.utils import ask_password


class TestMasterKeyHelper(unittest.TestCase):
    """Tests for MasterKeyHelper"""

    def setUp(self):
        """Reset the singleton before each test"""
        # Clean the singleton for each test
        if hasattr(MasterKeyHelper, '__wrapped__'):
            # If using functools.wraps
            MasterKeyHelper.__wrapped__._instances = {}
        else:
            # Direct access to the closure
            # The decorator creates a function that has 'instances' in its closure
            try:
                # Get the function created by the decorator
                func = MasterKeyHelper
                # Access the closure variables
                if hasattr(func, '__closure__') and func.__closure__:
                    for cell in func.__closure__:
                        try:
                            obj = cell.cell_contents
                            if isinstance(obj, dict):
                                obj.clear()
                                break
                        except (ValueError, AttributeError):
                            pass
            except Exception:
                pass

    def test_singleton_behavior(self):
        """Test that MasterKeyHelper is a singleton"""
        helper1 = MasterKeyHelper()
        helper2 = MasterKeyHelper()

        self.assertIs(helper1, helper2)
        self.assertEqual(id(helper1), id(helper2))

    def test_singleton_shared_state(self):
        """Test that state is shared between instances"""
        helper1 = MasterKeyHelper()
        helper1.masterkey = b'test_key'

        helper2 = MasterKeyHelper()
        self.assertEqual(helper2.masterkey, b'test_key')

    def test_init_default_values(self):
        """Test default values at initialization"""
        helper = MasterKeyHelper()

        self.assertIsNone(helper.masterkey)
        self.assertIsNone(helper.encrypted_masterkey)
        self.assertIsNone(helper.password_derivation_salt)

    def test_set_encrypted_masterkey(self):
        """Test the set_encrypted_masterkey method"""
        helper = MasterKeyHelper()

        encrypted_key = b'encrypted_master_key_data'
        salt = b'random_salt_16_b'

        helper.set_encrypted_masterkey(encrypted_key, salt)

        self.assertEqual(helper.encrypted_masterkey, encrypted_key)
        self.assertEqual(helper.password_derivation_salt, salt)

    @patch('src.camanager.masterkey.ask_password')
    @patch('src.camanager.masterkey.get_random_bytes')
    @patch('src.camanager.masterkey.encrypt_to_b64')
    def test_generate_new_to_b64_success(self, mock_encrypt, mock_random, mock_ask_password):
        """Test generating a new master key successfully"""
        # Setup mocks
        mock_ask_password.side_effect = ['mypassword', 'mypassword']
        mock_random.side_effect = [
            b'master_key_32_bytes_long_here!',  # masterkey
            b'salt_16_bytes!!'  # salt
        ]
        mock_encrypt.return_value = 'encrypted_base64_string'

        helper = MasterKeyHelper()
        encrypted_key, salt_b64 = helper.generate_new_to_b64()

        # Assertions
        self.assertEqual(encrypted_key, 'encrypted_base64_string')
        self.assertEqual(salt_b64, base64.b64encode(b'salt_16_bytes!!').decode('utf8'))
        self.assertEqual(helper.masterkey, b'master_key_32_bytes_long_here!')
        self.assertEqual(helper.password_derivation_salt, b'salt_16_bytes!!')

        # Verify calls
        self.assertEqual(mock_ask_password.call_count, 2)
        self.assertEqual(mock_random.call_count, 2)
        mock_random.assert_any_call(32)  # masterkey
        mock_random.assert_any_call(16)  # salt

    @patch('src.camanager.masterkey.ask_password')
    def test_generate_new_to_b64_password_mismatch(self, mock_ask_password):
        """Test generation with mismatched passwords"""
        mock_ask_password.side_effect = ['password1', 'password2']

        helper = MasterKeyHelper()

        with self.assertRaises(ValueError) as cm:
            helper.generate_new_to_b64()

        self.assertIn('not matching', str(cm.exception))

    @patch('src.camanager.masterkey.ask_password', return_value='correct_password')
    @patch('src.camanager.masterkey.decrypt_from_b64')
    def test_get_masterkey_first_time(self, mock_decrypt, mock_ask_password):
        """Test retrieving the master key for the first time"""
        helper = MasterKeyHelper()
        helper.encrypted_masterkey = 'encrypted_data'
        helper.password_derivation_salt = b'salt'

        mock_decrypt.return_value = b'decrypted_master_key'

        result = helper._get()

        self.assertEqual(result, b'decrypted_master_key')
        self.assertEqual(helper.masterkey, b'decrypted_master_key')
        mock_ask_password.assert_called_once_with('Enter the CA vault password')

    @patch('src.camanager.masterkey.ask_password')
    def test_get_masterkey_already_loaded(self, mock_ask_password):
        """Test that password is not requested again if already loaded"""
        helper = MasterKeyHelper()
        helper.masterkey = b'already_loaded_key'

        result = helper._get()

        self.assertEqual(result, b'already_loaded_key')
        mock_ask_password.assert_not_called()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('src.camanager.masterkey.ask_password', return_value='wrong_password')
    @patch('src.camanager.masterkey.decrypt_from_b64', side_effect=ValueError('Decryption failed'))
    def test_get_masterkey_wrong_password(self, mock_decrypt, mock_ask_password, mock_stdout):
        """Test with incorrect password"""
        helper = MasterKeyHelper()
        helper.encrypted_masterkey = 'encrypted_data'
        helper.password_derivation_salt = b'salt'

        with self.assertRaises(SystemExit) as cm:
            helper._get()

        self.assertEqual(cm.exception.code, -1)
        self.assertIn('incorrect', mock_stdout.getvalue())

    @patch('src.camanager.masterkey.PBKDF2')
    def test_derive_password(self, mock_pbkdf2):
        """Test password derivation"""
        mock_pbkdf2.return_value = b'derived_key'

        helper = MasterKeyHelper()
        helper.password_derivation_salt = b'test_salt'

        result = helper._derive_password('mypassword')

        self.assertEqual(result, b'derived_key')
        mock_pbkdf2.assert_called_once()
        # Verify PBKDF2 parameters
        args = mock_pbkdf2.call_args[0]
        self.assertEqual(args[0], 'mypassword')
        self.assertEqual(args[1], b'test_salt')
        self.assertEqual(args[2], 32)  # key length

    @patch('src.camanager.masterkey.encrypt_to_b64')
    def test_encrypt_to_b64_success(self, mock_encrypt):
        """Test encrypting data"""
        mock_encrypt.return_value = 'encrypted_base64'

        helper = MasterKeyHelper()
        helper.masterkey = b'master_key'

        result = helper.encrypt_to_b64(b'data_to_encrypt')

        self.assertEqual(result, 'encrypted_base64')
        mock_encrypt.assert_called_once_with(b'data_to_encrypt', b'master_key')

    def test_encrypt_to_b64_empty_data(self):
        """Test encryption with empty data"""
        helper = MasterKeyHelper()

        with self.assertRaises(ValueError) as cm:
            helper.encrypt_to_b64(None)

        self.assertIn('Cannot encrypt "nothing"', str(cm.exception))

        with self.assertRaises(ValueError):
            helper.encrypt_to_b64(b'')

    @patch('src.camanager.masterkey.encrypt_to_b64')
    @patch('src.camanager.masterkey.ask_password', return_value='password')
    @patch('src.camanager.masterkey.decrypt_from_b64')
    def test_encrypt_to_b64_loads_key_if_needed(self, mock_decrypt_func, mock_ask_password, mock_encrypt_func):
        """Test that master key is loaded if necessary during encryption"""
        mock_decrypt_func.return_value = b'decrypted_master_key'
        mock_encrypt_func.return_value = 'encrypted_result'

        helper = MasterKeyHelper()
        helper.encrypted_masterkey = 'encrypted_mk'
        helper.password_derivation_salt = b'salt'

        result = helper.encrypt_to_b64(b'test_data')

        # Verify that _get() was called (requests password)
        mock_ask_password.assert_called_once()
        self.assertEqual(helper.masterkey, b'decrypted_master_key')
        self.assertEqual(result, 'encrypted_result')

    @patch('src.camanager.masterkey.decrypt_from_b64')
    def test_decrypt_from_b64_success(self, mock_decrypt):
        """Test decrypting data"""
        mock_decrypt.return_value = b'decrypted_data'

        helper = MasterKeyHelper()
        helper.masterkey = b'master_key'

        result = helper.decrypt_from_b64('encrypted_base64_data')

        self.assertEqual(result, b'decrypted_data')
        mock_decrypt.assert_called_once_with('encrypted_base64_data', b'master_key')

    @patch('src.camanager.masterkey.decrypt_from_b64')
    @patch('src.camanager.masterkey.ask_password', return_value='password')
    def test_decrypt_from_b64_loads_key_if_needed(self, mock_ask_password, mock_decrypt_func):
        """Test that master key is loaded if necessary during decryption"""
        # First decrypt_from_b64 call is for _get() which loads the masterkey
        # Second is for the decrypt_from_b64() method itself
        mock_decrypt_func.side_effect = [
            b'decrypted_master_key',  # For _get()
            b'final_decrypted_data'  # For decrypt_from_b64()
        ]

        helper = MasterKeyHelper()
        helper.encrypted_masterkey = 'encrypted_mk'
        helper.password_derivation_salt = b'salt'

        result = helper.decrypt_from_b64('encrypted_data')

        mock_ask_password.assert_called_once()
        self.assertEqual(helper.masterkey, b'decrypted_master_key')
        self.assertEqual(result, b'final_decrypted_data')


class TestMasterKeyHelperIntegration(unittest.TestCase):
    """Integration tests for MasterKeyHelper"""

    def setUp(self):
        """Reset the singleton before each test"""
        if hasattr(MasterKeyHelper, '_instances'):
            MasterKeyHelper._instances = {}

    @patch('src.camanager.masterkey.ask_password')
    @patch('src.camanager.masterkey.get_random_bytes')
    @patch('src.camanager.masterkey.encrypt_to_b64')
    @patch('src.camanager.masterkey.decrypt_from_b64')
    def test_full_workflow(self, mock_decrypt_func, mock_encrypt_func,
                           mock_random, mock_ask_password):
        """Test a complete workflow: generation, encryption, decryption"""
        # Setup
        mock_ask_password.side_effect = [
            'mypassword', 'mypassword',  # For generate_new_to_b64
            'mypassword'  # For _get()
        ]
        mock_random.side_effect = [b'master_key_32b', b'salt_16b']
        mock_encrypt_func.side_effect = ['encrypted_mk', 'encrypted_data']
        mock_decrypt_func.side_effect = [b'master_key_32b', b'decrypted_data']

        # 1. Generate a new master key
        helper = MasterKeyHelper()
        encrypted_mk, salt_b64 = helper.generate_new_to_b64()

        self.assertEqual(encrypted_mk, 'encrypted_mk')

        # 2. Simulate reloading (new instance)
        helper2 = MasterKeyHelper()  # Same instance because singleton
        helper2.masterkey = None  # Reset to simulate reloading
        helper2.set_encrypted_masterkey(encrypted_mk, b'salt_16b')

        # 3. Encrypt data
        encrypted = helper2.encrypt_to_b64(b'sensitive_data')
        self.assertEqual(encrypted, 'encrypted_data')

        # 4. Decrypt data
        decrypted = helper2.decrypt_from_b64('encrypted_data')
        self.assertEqual(decrypted, b'decrypted_data')

    @patch('src.camanager.masterkey.ask_password')
    @patch('src.camanager.masterkey.get_random_bytes')
    def test_password_derivation_uses_salt(self, mock_random, mock_ask_password):
        """Test that derivation properly uses the salt"""
        mock_ask_password.side_effect = ['password', 'password']
        mock_random.side_effect = [b'mk' * 16, b'salt' * 4]

        helper = MasterKeyHelper()

        with patch('src.camanager.masterkey.PBKDF2') as mock_pbkdf2:
            with patch('src.camanager.masterkey.encrypt_to_b64', return_value='encrypted'):
                mock_pbkdf2.return_value = b'derived_key'

                helper.generate_new_to_b64()

                # Verify that PBKDF2 was called with the correct salt
                mock_pbkdf2.assert_called_once()
                call_args = mock_pbkdf2.call_args[0]
                self.assertEqual(call_args[1], b'salt' * 4)


class TestMasterKeyHelperEdgeCases(unittest.TestCase):
    """Edge case tests"""

    def setUp(self):
        """Reset the singleton"""
        if hasattr(MasterKeyHelper, '_instances'):
            MasterKeyHelper._instances = {}

    def test_encrypt_with_none_data(self):
        """Test encryption with None"""
        helper = MasterKeyHelper()

        with self.assertRaises(ValueError):
            helper.encrypt_to_b64(None)

    def test_encrypt_with_empty_bytes(self):
        """Test encryption with empty bytes"""
        helper = MasterKeyHelper()

        with self.assertRaises(ValueError):
            helper.encrypt_to_b64(b'')

    @patch('src.camanager.masterkey.ask_password')
    def test_multiple_password_attempts(self, mock_ask_password):
        """Test multiple attempts with the same helper"""
        helper = MasterKeyHelper()
        helper.masterkey = b'key1'

        # First call uses cached key
        result1 = helper._get()
        self.assertEqual(result1, b'key1')

        # Second call still uses cached key
        result2 = helper._get()
        self.assertEqual(result2, b'key1')

        # No password should be requested
        mock_ask_password.assert_not_called()

    def test_set_encrypted_masterkey_overwrites(self):
        """Test that set_encrypted_masterkey overwrites previous values"""
        helper = MasterKeyHelper()

        helper.set_encrypted_masterkey(b'first', b'salt1')
        self.assertEqual(helper.encrypted_masterkey, b'first')
        self.assertEqual(helper.password_derivation_salt, b'salt1')

        helper.set_encrypted_masterkey(b'second', b'salt2')
        self.assertEqual(helper.encrypted_masterkey, b'second')
        self.assertEqual(helper.password_derivation_salt, b'salt2')


if __name__ == '__main__':
    unittest.main()