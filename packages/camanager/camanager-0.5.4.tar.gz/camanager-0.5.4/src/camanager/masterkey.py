import base64
from typing import Optional

from Crypto.Hash import SHA512
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

from .utils import singleton, ask_password, encrypt_to_b64, decrypt_from_b64


@singleton
class MasterKeyHelper:
    """
    Helper to get encrypt and decrypt with the master key.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.masterkey = None
        self.encrypted_masterkey = None
        self.password_derivation_salt = None

    def set_encrypted_masterkey(self, encrypted_masterkey: bytes, password_derivation_salt: bytes):
        """
        Set the encrypted version of the master key

        :param encrypted_masterkey: the encrypted version of the master key (and it's tag)
        :param password_derivation_salt: salt used for the password derivation
        """
        self.encrypted_masterkey = encrypted_masterkey
        self.password_derivation_salt = password_derivation_salt

    def generate_new_to_b64(self, vault_password: Optional[str] = None) -> (str, bytes):
        """
        Generate a new master key and return its encrypted version as base64.

        The master key is encrypted with a user provided password that can be provided by parameter or by asking the user.

        :param vault_password: the vault password
        :return: the base64-encoded string of the encrypted master key
        """
        if vault_password is None or len(vault_password) == 0:
            vault_password = ask_password('Enter the password that will be used to encrypt the CA vault')
            vault_password_confirm = ask_password('Confirm it')

            if vault_password != vault_password_confirm:
                raise ValueError('The two provided passwords are not matching')

        self.masterkey = get_random_bytes(32)
        self.password_derivation_salt = get_random_bytes(16)

        self.encrypted_masterkey = encrypt_to_b64(self.masterkey, self._derive_password(vault_password))

        return self.encrypted_masterkey, base64.b64encode(self.password_derivation_salt).decode('utf8')

    def _get(self):
        """
        Get the master key.

        If it's the first time, the user must provide the password.
        """
        if not self.masterkey:
            password = ask_password('Enter the CA vault password')

            try:
                self.masterkey = decrypt_from_b64(self.encrypted_masterkey,
                                                  self._derive_password(password))

            except ValueError:
                print('Error: the provided CA vault password is incorrect')
                exit(-1)

        return self.masterkey

    def _derive_password(self, password: str) -> bytes:
        """
        Derive the user provided password to a key
        """
        return PBKDF2(password, self.password_derivation_salt, 32, count=1000000, hmac_hash_module=SHA512)

    def encrypt_to_b64(self, data: bytes) -> str:
        """
        Encrypt the data and return it as base64 encoded string
        """
        if data is None or len(data) == 0:
            raise ValueError('Cannot encrypt "nothing"')

        return encrypt_to_b64(data, self._get())

    def decrypt_from_b64(self, b64_data: str) -> bytes:
        """
        Encrypt the data and return it as base64 encoded string
        """
        return decrypt_from_b64(b64_data, self._get())
