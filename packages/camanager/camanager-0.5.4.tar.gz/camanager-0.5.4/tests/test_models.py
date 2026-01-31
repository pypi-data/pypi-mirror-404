import binascii
import datetime
import unittest

from cryptography.hazmat.primitives import hashes

from src.camanager.models import CertificateRevokedReason, Certificate, FixedDateTimeField, HashAlgo, BaseCertKeyModel
from src.camanager.masterkey import MasterKeyHelper
from .data import *


class TestFixedDateTimeField(unittest.TestCase):
    def setUp(self):
        """Initialize the field before each test"""
        self.field = FixedDateTimeField()

    def test_python_value_with_none(self):
        """Test that None returns None"""
        result = self.field.python_value(None)
        self.assertIsNone(result)

    def test_python_value_with_datetime_object(self):
        """Test that a datetime object is returned as-is"""
        dt = datetime.datetime(2025, 1, 4, 12, 30, 45)
        result = self.field.python_value(dt)
        self.assertEqual(result, dt)
        self.assertIsInstance(result, datetime.datetime)

    def test_python_value_with_iso_string(self):
        """Test conversion from ISO string to datetime"""
        iso_string = "2025-01-04T12:30:45"
        result = self.field.python_value(iso_string)
        expected = datetime.datetime(2025, 1, 4, 12, 30, 45)
        self.assertEqual(result, expected)
        self.assertIsInstance(result, datetime.datetime)

    def test_python_value_with_iso_string_with_microseconds(self):
        """Test with microseconds"""
        iso_string = "2025-01-04T12:30:45.123456"
        result = self.field.python_value(iso_string)
        expected = datetime.datetime(2025, 1, 4, 12, 30, 45, 123456)
        self.assertEqual(result, expected)

    def test_python_value_with_iso_string_with_timezone(self):
        """Test with timezone"""
        iso_string = "2025-01-04T12:30:45+01:00"
        result = self.field.python_value(iso_string)
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.hour, 12)

    def test_python_value_with_invalid_string(self):
        """Test that an invalid string raises an exception"""
        with self.assertRaises(ValueError):
            self.field.python_value("invalid-date-string")


class TestBaseCertKeyModel(unittest.TestCase):
    def setUp(self):
        helper = MasterKeyHelper()
        helper.masterkey = (b'\xf8\x48\x0f\xd8\xe7\xcd\xf0\x86\xfe\x12\x5e\x5a\xd0\x6f\x14\xc3'
                            b'\xa2\x44\xe2\x4c\xee\x10\x15\xcd\x58\x12\x52\xd6\x04\x11\xcc\x1a')


    def test_cert_obj(self):
        base_certkey = BaseCertKeyModel()
        base_certkey.cert = load_txt('tests/data/cert.pem')
        base_certkey.load_cert()

        self.assertEqual(base_certkey.cert_obj, get_cert_obj())

    def test_no_key(self):
        base_certkey = BaseCertKeyModel()
        base_certkey.cert = load_txt('tests/data/cert.pem')

        with self.assertRaises(RuntimeError):
            base_certkey.load_key()

        self.assertIsNone(base_certkey.key)

    def test_set_key(self):
        base_certkey = BaseCertKeyModel()
        base_certkey.cert = load_txt('tests/data/cert.pem')

        self.assertIsNone(base_certkey.key)
        self.assertIsNone(base_certkey.encrypted_key)

        base_certkey.key = load_txt('tests/data/pkey.key')

        self.assertIsNotNone(base_certkey.key)
        self.assertIsNotNone(base_certkey.encrypted_key)

        base_certkey.load_key()
        self.assertEqual(base_certkey.key_obj.private_bytes(serialization.Encoding.PEM,
                                                            serialization.PrivateFormat.TraditionalOpenSSL,
                                                            serialization.NoEncryption()),
                         get_privatekey_obj().private_bytes(serialization.Encoding.PEM,
                                                            serialization.PrivateFormat.TraditionalOpenSSL,
                                                            serialization.NoEncryption()))

        base_certkey.clear_key()
        self.assertIsNone(base_certkey.key_obj)
        self.assertIsNotNone(base_certkey.key)
        self.assertIsNotNone(base_certkey.encrypted_key)

        base_certkey.key = None

        self.assertIsNone(base_certkey.key_obj)
        self.assertIsNone(base_certkey.key)
        self.assertIsNone(base_certkey.encrypted_key)

class TestCertificateRevokedReason(unittest.TestCase):
    def test_from_string(self):
        self.assertEqual(CertificateRevokedReason.from_string('key compromise'), CertificateRevokedReason.KEY_COMPRISE)
        self.assertEqual(CertificateRevokedReason.from_string('compromise'), CertificateRevokedReason.KEY_COMPRISE)
        self.assertEqual(CertificateRevokedReason.from_string('eol'), CertificateRevokedReason.CESSATION_OF_OPERATION)

        self.assertEqual(CertificateRevokedReason.from_string('other'), CertificateRevokedReason.UNSPECIFIED)
        self.assertEqual(CertificateRevokedReason.from_string('key'), CertificateRevokedReason.UNSPECIFIED)

    def test_to_reason_flags(self):
        self.assertEqual(CertificateRevokedReason.KEY_COMPRISE.to_reason_flags(), x509.ReasonFlags.key_compromise)
        self.assertEqual(CertificateRevokedReason.CESSATION_OF_OPERATION.to_reason_flags(), x509.ReasonFlags.cessation_of_operation)
        self.assertEqual(CertificateRevokedReason.UNSPECIFIED.to_reason_flags(), x509.ReasonFlags.unspecified)


class TestCertificate(unittest.TestCase):
    def test_serial_as_int64(self):
        c = Certificate(serial='6b:8c:02:7a:8a:64:11:d0:e0:94:e9:22:58:99:1a:d6:95:58:0e:0e')
        self.assertEqual(613984332728918798661844833697261882337094274574, c.serial_as_int64)

        c = Certificate(serial='06:9a:8b:0b:aa:2a:53:a8')
        self.assertEqual(475845592856810408, c.serial_as_int64)

        c = Certificate(serial='28:11:59:2f:b8:5e:ed:be:0e:98:4c:e9:c6:2e:21:b1:27:bf:5a:17')
        self.assertEqual(228746512733118622626861842270018213062574561815, c.serial_as_int64)


    def test_str(self):
        now = datetime.datetime.now(datetime.UTC)
        expire = now + datetime.timedelta(days=365)

        c = Certificate(id=5,
                        cn='test.example.com',
                        created_timestamp=now,
                        not_after=expire,
                        serial='01:02:03:04:05:06:07:09')
        s = f'#5. CN:test.example.com (expire on {expire.strftime('%d/%m/%Y %H:%M:%S UTC')}, serial: 01:02:03:04:05:06:07:09, no private key stored)'
        self.assertEqual(s, str(c))

        c = Certificate(id=5,
                        cn='test.example.com',
                        san='DNS:test.example.com',
                        created_timestamp=now,
                        not_after=expire,
                        serial='01:02:03:04:05:06:07:09',
                        is_revoked=True,
                        is_renewed=False)
        s = f'#5. CN:test.example.com / DNS:test.example.com (revoked, serial: 01:02:03:04:05:06:07:09, no private key stored)'
        self.assertEqual(s, str(c))

        c = Certificate(id=5,
                        cn='test.example.com',
                        san='DNS:test.example.com',
                        created_timestamp=now,
                        not_after=expire,
                        serial='01:02:03:04:05:06:07:09',
                        is_revoked=True,
                        revoked_reason=CertificateRevokedReason.KEY_COMPRISE,
                        revoked_comment='test comment',
                        is_renewed=False)
        s = f'#5. CN:test.example.com / DNS:test.example.com (revoked [comment: test comment], serial: 01:02:03:04:05:06:07:09, no private key stored)'
        self.assertEqual(s, str(c))

        c = Certificate(id=5,
                        cn='test.example.com',
                        san='DNS:test.example.com',
                        created_timestamp=now,
                        not_after=expire,
                        serial='01:02:03:04:05:06:07:09',
                        is_revoked=False,
                        is_renewed=True)
        s = f'#5. CN:test.example.com / DNS:test.example.com (renewed [must not be used anymore], serial: 01:02:03:04:05:06:07:09, no private key stored)'
        self.assertEqual(s, str(c))

        c = Certificate(id=5,
                        cn='test.example.com',
                        created_timestamp=now,
                        not_after=now - datetime.timedelta(days=1),
                        serial='01:02:03:04:05:06:07:09')
        s = f'#5. CN:test.example.com (expired, serial: 01:02:03:04:05:06:07:09, no private key stored)'
        self.assertEqual(s, str(c))


class TestHashAlgo(unittest.TestCase):
    def test_from_string(self):
        self.assertEqual(HashAlgo.from_string('sha1'), HashAlgo.SHA1)
        self.assertEqual(HashAlgo.from_string('SHA256'), HashAlgo.SHA256)
        self.assertEqual(HashAlgo.from_string('SHA512'), HashAlgo.SHA512)

        with self.assertRaises(NotImplementedError):
            HashAlgo.from_string('SHA 512')

    def test_from_x509_hash_algorithm(self):
        self.assertEqual(HashAlgo.from_x509_hash_algorithm(hashes.SHA1()), HashAlgo.SHA1)

    def test_get_str_values(self):
        self.assertEqual(['sha1', 'sha256', 'sha512'], HashAlgo.get_str_values())
