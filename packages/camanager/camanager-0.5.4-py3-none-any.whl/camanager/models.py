import datetime
import enum

import peewee
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import HashAlgorithm

from .masterkey import MasterKeyHelper
from .utils import get_private_key_from_pem

"""
The database filename
"""
DATABASE_FILENAME = 'ca.db'

"""
The database filename backup
"""
DATABASE_FILENAME_BACKUP = f'{DATABASE_FILENAME}.bak'

"""
The database object
"""
database = peewee.SqliteDatabase(None)

class FixedDateTimeField(peewee.DateTimeField):
    def python_value(self, value):
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value
        return datetime.datetime.fromisoformat(value)

class BaseModel(peewee.Model):
    """
    Base model
    """
    class Meta:
        database = database


class BaseCertKeyModel(BaseModel):
    """
    Base certificate model which may have a key.

    The certificate must be stored into the "cert" attribute in the PEM format.
    The optional private key must be stored into the "key" attribute in the PEM format.

    The x509.Certificate and PrivateKeyTypes can be loaded as self.cert_obj and self.key_obj. If the key is
    passphrase protected, the user is asking for this passphrase.
    """
    cert = peewee.TextField()
    encrypted_key = peewee.TextField(null=True)
    _key = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cert_obj = None
        self.key_obj = None

    def load_cert(self) -> None:
        """
        Load the certificate as x509.Certificate object into the attribute "cert_obj".
        """
        self.cert_obj = x509.load_pem_x509_certificate(str(self.cert).encode('utf8'), default_backend())

    def load_key(self) -> None:
        """
        Load the private key as PrivateKeyTypes object into the attribute "key_obj".

        If the key is passphrase protected, the user is asking for this passphrase (prompt to stdout, read from stdin).

        If no key is available (self.key is None), a RuntimeError is raised.

        :except: RunTime
        """
        if not self.key:
            raise RuntimeError('No key available')

        self.key_obj = get_private_key_from_pem(str(self.key))


    def clear_key(self) -> None:
        """
        Clear the attribute "key_obj".
        """
        self.key_obj = None

    def _get_key(self):
        if self.encrypted_key is None:
            return None

        return MasterKeyHelper().decrypt_from_b64(self.encrypted_key).decode('utf8')

    def _set_key(self, data: bytes):
        if data is None:
            self.encrypted_key = None
        else:
            if isinstance(data, str):
                data = data.encode('utf8')

            self.encrypted_key = MasterKeyHelper().encrypt_to_b64(data)

    key = property(fget=_get_key, fset=_set_key, doc="Private Key (PEM)")


class CRLSigningCertificate(BaseModel):
    """
    A CRL Signing Certificate.

    The certificate and the key are stored in the PEM format, in plain text !
    """
    cert = peewee.TextField()
    key = peewee.TextField()


class CA(BaseCertKeyModel):
    """
    A Certificate Authority model.

    The certificate and the key are stored in the PEM format.
    """
    id = peewee.IntegerField(primary_key=True)
    is_default = peewee.BooleanField(default=False, unique=True)
    name = peewee.CharField(unique=True)
    is_intermediate = peewee.BooleanField()
    crl_signing = peewee.ForeignKeyField(CRLSigningCertificate, backref='ca', null=True)
    crl_last_generated = FixedDateTimeField(null=True)
    crl_output_filename = peewee.CharField(unique=True)
    crl_url = peewee.TextField(null=True)
    ocsp_url = peewee.TextField(null=True)
    crl_post_script_path = peewee.TextField(null=True)


class CertificateRevokedReason(enum.Enum):
    """
    The certificate revoked reason
    """
    UNSPECIFIED = 'unspecified'
    KEY_COMPRISE = 'keyCompromise'
    CESSATION_OF_OPERATION = 'cessationOfOperation'

    @staticmethod
    def from_string(s: str):
        s = s.lower()

        if s in ['keycompromise', 'key compromise', 'compromise', 'compromised']:
            return CertificateRevokedReason.KEY_COMPRISE
        elif s in ['cessationOfOperation', 'cessation of operation', 'eol']:
            return CertificateRevokedReason.CESSATION_OF_OPERATION
        else:
            return CertificateRevokedReason.UNSPECIFIED

    def to_reason_flags(self) -> x509.ReasonFlags:
        match self:
            case self.KEY_COMPRISE:
                return x509.ReasonFlags.key_compromise
            case self.CESSATION_OF_OPERATION:
                return x509.ReasonFlags.cessation_of_operation
            case _:
                return x509.ReasonFlags.unspecified


class Certificate(BaseCertKeyModel):
    """
    A certificate model.

    The created_timestamp and not_after are precise to the second.
    The serial is provided in the official X509 output, so in hex format using ":" separator in the big endian
    representation of the 64 bits integer.
    The certificate and the key (optional) are stored in the PEM format.
    """
    id = peewee.IntegerField(primary_key=True)
    ca = peewee.ForeignKeyField(CA, backref='ca')
    cn = peewee.CharField()
    san = peewee.CharField(null=True)
    created_timestamp = FixedDateTimeField()
    not_after = FixedDateTimeField()
    serial = peewee.IntegerField()
    is_revoked = peewee.BooleanField()
    revoked_timestamp = FixedDateTimeField(null=True)
    revoked_reason = peewee.TextField(null=True)
    revoked_comment = peewee.TextField(null=True)
    is_renewed = peewee.BooleanField()

    @property
    def serial_as_int64(self):
        return int.from_bytes(bytes.fromhex(self.serial.replace(':', '')), 'big')

    def __str__(self):
        now = datetime.datetime.now(datetime.UTC)

        s = f'#{self.id}. CN:{self.cn}'\

        if self.san:
            s += f' / {self.san}'

        s += ' ('

        if self.not_after <= now:
            s += 'expired'
        elif self.is_revoked:
            s += 'revoked'

            if self.revoked_comment:
                s += f' [comment: {self.revoked_comment}]'
        elif self.is_renewed:
            s += 'renewed [must not be used anymore]'
        else:
            s += f'expire on {self.not_after.strftime("%d/%m/%Y %H:%M:%S %Z")}'

        s += f', serial: {self.serial}, '
        s += 'no private key stored' if not self.encrypted_key else 'private key available'
        s += ')'

        return s


class ConfigType(enum.IntEnum):
    """
    The configuration value type
    """
    INT = 1
    STRING = 2
    BINARY = 3
    EPOCH = 4


class Config(BaseModel):
    """
    A Configuration model
    """
    name = peewee.CharField(primary_key=True)
    type = peewee.IntegerField()
    value = peewee.CharField()

class HashAlgo(enum.Enum):
    SHA1 = hashes.SHA1()
    SHA256 = hashes.SHA256()
    SHA512 = hashes.SHA512()

    @staticmethod
    def from_string(s: str) -> "HashAlgo":
        match s.lower():
            case 'sha1':
                return HashAlgo.SHA1
            case 'sha256':
                return HashAlgo.SHA256
            case 'sha512':
                return HashAlgo.SHA512
            case _:
                raise NotImplementedError

    @staticmethod
    def from_x509_hash_algorithm(h: HashAlgorithm):
        return HashAlgo.from_string(h.name)

    @staticmethod
    def get_str_values():
        return ['sha1', 'sha256', 'sha512']
