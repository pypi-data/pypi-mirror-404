import datetime
import os
import re
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch, Mock
import ipaddress
from freezegun import freeze_time

from .data import *
from src.camanager import utils


class TestRegex(unittest.TestCase):
    def test_regex_domain(self):
        regex = re.compile(utils.regex_domain)

        self.assertFalse(regex.match(''))

        self.assertTrue(regex.match('host'))
        self.assertTrue(regex.match('my-host'))
        self.assertTrue(regex.match('host.'))
        self.assertTrue(regex.match('host.sub.domain.lan'))
        self.assertTrue(regex.match('*.domain.lan'))

        self.assertFalse(regex.match('http://domain.lan'))
        self.assertFalse(regex.match('cool*domain.lan'))

    def test_regex_san(self):
        regex = re.compile(utils.regex_san)

        self.assertFalse(regex.match(''))

        self.assertTrue(regex.match('DNS:myhost'))
        self.assertTrue(regex.match('DNS: myhost'))
        self.assertTrue(regex.match('DNS:myhost,DNS:myhost.domain.lan'))
        self.assertTrue(regex.match('DNS:myhost, DNS: myhost.domain.lan'))
        self.assertTrue(regex.match('DNS:myhost,IP:10.0.0.1'))
        self.assertTrue(regex.match('DNS:myhost,IP:10.0.0.1,DNS:host2'))
        self.assertTrue(regex.match('DNS:myhost,IP:10.0.0.1,DNS:host2,IP:10.0.254.1'))
        self.assertTrue(regex.match('IP: 10.0.0.1'))
        self.assertTrue(regex.match('IP: 2001:0620:0000:0000:0211:24FF:FE80:C12C'))
        self.assertTrue(regex.match('DNS:myhost,IP:10.0.0.1,DNS: host2, IP: 2001:0620:0000:0000:0211:24FF:FE80:C12C'))

        self.assertFalse(regex.match('myhost'))
        self.assertFalse(regex.match('myhost,10.0.0.1'))

    def test_regex_cn(self):
        regex = re.compile(utils.regex_cn)

        self.assertFalse(regex.match(''))

        self.assertTrue(regex.match('host'))
        self.assertTrue(regex.match('my-host'))
        self.assertTrue(regex.match('host.'))
        self.assertTrue(regex.match('host.sub.domain.lan'))
        self.assertTrue(regex.match('*.domain.lan'))
        self.assertTrue(regex.match('10.0.0.1'))
        self.assertTrue(regex.match('2001:0620:0000:0000:0211:24FF:FE80:C12C'))

        self.assertFalse(regex.match('http://domain.lan'))
        self.assertFalse(regex.match('cool*domain.lan'))


class TestAsk(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_ask(self,  mock_stdout):
        with patch('builtins.input', return_value='test'):
            ret = utils.ask('test prompt')

            self.assertEqual('test prompt : ', mock_stdout.getvalue())
            self.assertEqual('test', ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ask_with_empty(self, mock_stdout):
        with patch('builtins.input',  side_effect=['', 'test2']):
            ret = utils.ask('test prompt')
            self.assertEqual('test prompt : test prompt : ', mock_stdout.getvalue())
            self.assertEqual('test2', ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ask_empty(self,  mock_stdout):
        with patch('builtins.input', return_value=''):
            ret = utils.ask('prompt', can_be_empty=True)

            self.assertEqual('prompt : ', mock_stdout.getvalue())
            self.assertIsNone(ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ask_values(self, mock_stdout):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('builtins.input', return_value='one'):
                ret = utils.ask('message', values=['one', 'two'])

                self.assertEqual('message (one, two) : ', mock_stdout.getvalue())
                self.assertEqual('one', ret)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('builtins.input', side_effect=['', 'two']):
                ret = utils.ask('message', values=['one', 'two'])

                self.assertEqual('message (one, two) : message (one, two) : ', mock_stdout.getvalue(),)
                self.assertEqual('two', ret)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('builtins.input', side_effect=['', 'two']):
                ret = utils.ask('msg', values=['one', 'two'], can_be_empty=True)

                self.assertEqual('msg (one, two) : ', mock_stdout.getvalue())
                self.assertIsNone(ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ask_lower(self, mock_stdout):
        with patch('builtins.input', return_value='TeSt'):
            ret = utils.ask('prompt')
            self.assertEqual('test', ret)

        with patch('builtins.input', return_value='TeSt'):
            ret = utils.ask('prompt', disable_lowering=True)
            self.assertEqual('TeSt', ret)


class TestAskPemFormat(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_askpemformat_cert(self, mock_stdout):
        cert = load_txt('tests/data/cert.pem')

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write(cert)
            sys.stdin.seek(0)

            ret = utils.ask_pem_format('cert', utils.PEMFormatType.CERT)

            self.assertEqual('cert :\n', mock_stdout.getvalue())
            self.assertEqual(cert, ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askpemformat_cert(self,  mock_stdout):
        cert = '-----BEGIN CERTIFICATE-----\n*** FAKE LINE 1 ***\n*** FAKE LINE 2 ***\n-----END CERTIFICATE-----\n'

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write(cert)
            sys.stdin.seek(0)

            ret = utils.ask_pem_format('cert', utils.PEMFormatType.CERT)

            self.assertEqual('cert :\n', mock_stdout.getvalue())
            self.assertEqual(cert, ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askpemformat_cert_type_not_supported(self, mock_stdout):
        cert = '-----BEGIN CERTIFICATE-----\n*** FAKE LINE 1 ***\n*** FAKE LINE 2 ***\n-----END CERTIFICATE-----\n'

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write(cert)
            sys.stdin.seek(0)

            unknown_type = Mock(spec=utils.PEMFormatType)
            unknown_type.CERT = utils.PEMFormatType.CERT
            unknown_type.KEY = utils.PEMFormatType.KEY
            unknown_type.CSR = utils.PEMFormatType.CSR
            unknown_type.value = 99  # The unknown value

            with self.assertRaises(ValueError):
                utils.ask_pem_format('cert', unknown_type)


    @patch('sys.stdout', new_callable=StringIO)
    def test_askpemformat_privatekey(self, mock_stdout):
        pkey = '-----BEGIN RSA PRIVATE KEY-----\n*** FAKE LINE ***\n*** FAKE LINE ***\n-----END RSA PRIVATE KEY-----\n'

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write(pkey)
            sys.stdin.seek(0)

            ret = utils.ask_pem_format('private key', utils.PEMFormatType.KEY)

            self.assertEqual('private key :\n', mock_stdout.getvalue())
            self.assertEqual(pkey, ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askpemformat_badtype(self, mock_stdout):
        pkey = '-----BEGIN RSA PRIVATE KEY-----\n*** FAKE LINE ***\n*** FAKE LINE ***\n-----END RSA PRIVATE KEY-----\n'

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write(pkey)
            sys.stdin.seek(0)

            with self.assertRaises(ValueError):
                utils.ask_pem_format('private key', utils.PEMFormatType.CERT)

        with patch('sys.stdin', new_callable=StringIO):
            sys.stdin.write(pkey)
            sys.stdin.seek(0)

            with self.assertRaises(ValueError):
                utils.ask_pem_format('private key', utils.PEMFormatType.CSR)


class TestAskDateInFuture(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_askdateinfuture(self, mock_stdout):
        with patch('builtins.input', side_effect=['01/01/3000']):
            ret = utils.ask_date_in_future()

            self.assertEqual('Enter a date in the future (DD/MM/YYYY) : ', mock_stdout.getvalue())
            self.assertEqual(datetime.date(3000, 1, 1), ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askdateinfuture_nofuture(self, mock_stdout):
        with patch('builtins.input', side_effect=['01/01/1980', '01/01/3000']):
            ret = utils.ask_date_in_future()

            self.assertEqual('Enter a date in the future (DD/MM/YYYY) : \tThe date must be in the future\n'
                             'Enter a date in the future (DD/MM/YYYY) : ', mock_stdout.getvalue())
            self.assertEqual(datetime.date(3000, 1, 1), ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askdateinfuture_notadate(self, mock_stdout):
        with patch('builtins.input', side_effect=['not-a-date', '01/01/3000']):
            ret = utils.ask_date_in_future()

            self.assertEqual('Enter a date in the future (DD/MM/YYYY) : \tnot-a-date is invalid\n'
                             'Enter a date in the future (DD/MM/YYYY) : ', mock_stdout.getvalue())
            self.assertEqual(datetime.date(3000, 1, 1), ret)


class TestAskCn(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_askcn(self, mock_stdout):
        with patch('builtins.input', return_value='host'):
            ret = utils.ask_cn()

            self.assertEqual('Common Name : ', mock_stdout.getvalue())
            self.assertEqual('host', ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askcn_badcn(self, mock_stdout):
        with patch('builtins.input', side_effect=['****', 'my-host']):
            ret = utils.ask_cn()

            self.assertEqual('Common Name : \t**** is invalid\nCommon Name : ', mock_stdout.getvalue())
            self.assertEqual('my-host', ret)


class TestAskHosts(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_askhosts_onehost(self, mock_stdout):
        with patch('builtins.input', return_value='host'):
            ret = utils.ask_hosts()

            self.assertEqual('Enter alternative names separated by a comma (eg: srv.internal.lan) : ',
                             mock_stdout.getvalue())
            self.assertEqual(['host'], ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askhosts_nohost(self, mock_stdout):
        with patch('builtins.input', return_value=''):
            ret = utils.ask_hosts()

            self.assertEqual([], ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askhosts_multiplehosts(self, mock_stdout):
        with patch('builtins.input', return_value='my-host, my-super.gigadomain.lan'):
            ret = utils.ask_hosts()

            self.assertEqual(['my-host', 'my-super.gigadomain.lan'], ret)

        with patch('builtins.input', return_value='duplicate, host, duplicate'):
            ret = utils.ask_hosts()

            self.assertEqual(['duplicate', 'host'], ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askhosts_ip(self, mock_stdout):
        with patch('builtins.input', side_effect=['10.0.0.1', 'host']):
            ret = utils.ask_hosts()

            self.assertEqual('Enter alternative names separated by a comma (eg: srv.internal.lan) : '
                             '\t10.0.0.1 is an IP address\n'
                             'Enter alternative names separated by a comma (eg: srv.internal.lan) : ',
                             mock_stdout.getvalue())
            self.assertEqual(['host'], ret)


class TestAskIps(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_askips_oneip(self, mock_stdout):
        with patch('builtins.input', return_value='10.0.0.1'):
            ret = utils.ask_ips()

            self.assertEqual('Enter IPs separated by a comma (eg: 10.0.0.1, 10.254.0.1) : ',
                             mock_stdout.getvalue())
            self.assertEqual(['10.0.0.1'], ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askips_nohip(self, mock_stdout):
        with patch('builtins.input', return_value=''):
            ret = utils.ask_ips()

            self.assertEqual([], ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askips_multipleips(self, mock_stdout):
        with patch('builtins.input', return_value='2001:0620:0000:0000:0211:24FF:FE80:C12C, 10.0.0.1'):
            ret = utils.ask_ips()

            self.assertEqual(['10.0.0.1', '2001:0620:0000:0000:0211:24ff:fe80:c12c'], ret)

        with patch('builtins.input', return_value='192.168.0.10, 10.0.0.1, 192.168.0.10'):
            ret = utils.ask_ips()

            self.assertEqual(['10.0.0.1', '192.168.0.10'], ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_askips_badvalue(self, mock_stdout):
        with patch('builtins.input', side_effect=['host', '10.0.0.1']):
            ret = utils.ask_ips()

            self.assertEqual('Enter IPs separated by a comma (eg: 10.0.0.1, 10.254.0.1) : \thost is invalid\n'
                             'Enter IPs separated by a comma (eg: 10.0.0.1, 10.254.0.1) : ', mock_stdout.getvalue())
            self.assertEqual(['10.0.0.1'], ret)


class TestAskCnAndSan(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_cn_with_all(self, mock_stdout):
        with patch('builtins.input', side_effect=['host', 'host2', '10.0.0.1']):
            cn, san = utils.ask_cn_and_san()

            self.assertEqual('host', cn)
            self.assertEqual('DNS:host2, DNS:host, IP:10.0.0.1', utils.get_san_str(san))

    @patch('sys.stdout', new_callable=StringIO)
    def test_cn_without_alternative_host(self, mock_stdout):
        with patch('builtins.input', side_effect=['host', '', '10.0.0.1']):
            cn, san = utils.ask_cn_and_san()

            self.assertEqual('host', cn)
            self.assertEqual('DNS:host, IP:10.0.0.1', utils.get_san_str(san))

    @patch('sys.stdout', new_callable=StringIO)
    def test_cn_without_alternative_ip(self, mock_stdout):
        with patch('builtins.input', side_effect=['host', 'host2', '']):
            cn, san = utils.ask_cn_and_san()

            self.assertEqual('host', cn)
            self.assertEqual('DNS:host2, DNS:host', utils.get_san_str(san))

    @patch('sys.stdout', new_callable=StringIO)
    def test_cn_without_alternative(self, mock_stdout):
        with patch('builtins.input', side_effect=['host', '', '']):
            cn, san = utils.ask_cn_and_san()

            self.assertEqual('host', cn)
            self.assertEqual('DNS:host', utils.get_san_str(san))

    @patch('sys.stdout', new_callable=StringIO)
    def test_cn_with_host_is_an_ip(self, mock_stdout):
        with patch('builtins.input', side_effect=['192.168.0.1', '', '']):
            cn, san = utils.ask_cn_and_san()

            self.assertEqual('192.168.0.1', cn)
            self.assertEqual('IP:192.168.0.1', utils.get_san_str(san))


class TestConfirm(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_confirm_yes(self, mock_stdout):
        with patch('builtins.input', return_value='y'):
            ret = utils.confirm('message prompt')

            self.assertEqual('message prompt ? [y/n] : ', mock_stdout.getvalue())
            self.assertTrue(ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_confirm_no(self, mock_stdout):
        with patch('builtins.input', return_value='n'):
            ret = utils.confirm('prompt')
            self.assertFalse(ret)

    @patch('sys.stdout', new_callable=StringIO)
    def test_confirm_badanswer(self, mock_stdout):
        with patch('builtins.input', side_effect=['x', 'y']):
            ret = utils.confirm('confirm')

            self.assertEqual('confirm ? [y/n] : confirm ? [y/n] : ', mock_stdout.getvalue())
            self.assertTrue(ret)


class TestAskPassword(unittest.TestCase):
    def test_ask_password(self):
        with patch('getpass.getpass', return_value='myP@sswOrd'):
            ret = utils.ask_password('Enter your password')
            self.assertEqual('myP@sswOrd', ret)

class TestAskPrivateKeyPassphrase(unittest.TestCase):
    @patch('getpass.getpass', return_value='myP@sswOrd')
    def test_ask_private_key_passphrase(self, mock_getpass):
        ret = utils.ask_private_key_passphrase()
        mock_getpass.assert_called_once_with('Enter the private key passphrase : ')
        self.assertEqual('myP@sswOrd', ret)

class TestGenerateRandomSerialNumber(unittest.TestCase):
    def test_generate_random_serial_number(self):
        for i in range(0, 10):
            sn = utils.generate_random_serial_number()

            self.assertGreater(sn, 0)
            self.assertLess(sn,  2 ** 64)


class TestSAN(unittest.TestCase):
    def test_get_cert_san(self,):
        cert = get_cert_obj()
        self.assertEqual('DNS:host2.domain.lan, DNS:my-host, DNS:host, IP:10.0.0.1', 
                         utils.get_san_str(utils.get_san(cert)))

    def test_get_csr_san(self):
        csr = get_csr_obj()
        self.assertEqual('DNS:host2.domain.lan, DNS:my-host, DNS:host, IP:10.0.0.1',
                         utils.get_san_str(utils.get_san(csr)))


    def test_validate_or_build_san(self):
        self.assertEqual('DNS:host', utils.get_san_str(utils.validate_or_build_san('host', None)))

        san = [x509.DNSName('host')]
        self.assertEqual('DNS:host',utils.get_san_str(
            utils.validate_or_build_san('host', x509.SubjectAlternativeName(san))))

        san = [x509.DNSName('host'), x509.DNSName('host2')]
        self.assertEqual('DNS:host, DNS:host2',utils.get_san_str(
            utils.validate_or_build_san('host', x509.SubjectAlternativeName(san))))

        san = [x509.DNSName('host2')]
        self.assertEqual('DNS:host2, DNS:host',utils.get_san_str(
            utils.validate_or_build_san('host', x509.SubjectAlternativeName(san))))

        self.assertEqual('IP:10.0.0.1', utils.get_san_str(utils.validate_or_build_san('10.0.0.1', None)))

        san = [x509.IPAddress(ipaddress.ip_address('10.0.0.1'))]
        self.assertEqual('IP:10.0.0.1',utils.get_san_str(
            utils.validate_or_build_san('10.0.0.1', x509.SubjectAlternativeName(san))))

        san = [x509.IPAddress(ipaddress.ip_address('10.0.254.1'))]
        self.assertEqual('IP:10.0.254.1, IP:10.0.0.1', utils.get_san_str(
            utils.validate_or_build_san('10.0.0.1', x509.SubjectAlternativeName(san))))

        san = [x509.IPAddress(ipaddress.ip_address('10.0.0.1')), x509.DNSName('host')]
        self.assertEqual('IP:10.0.0.1, DNS:host',utils.get_san_str(
            utils.validate_or_build_san('10.0.0.1', x509.SubjectAlternativeName(san))))

        san = [x509.DNSName('host')]
        self.assertEqual('DNS:host, IP:10.0.0.1',utils.get_san_str(
            utils.validate_or_build_san('10.0.0.1', x509.SubjectAlternativeName(san))))

        san = [x509.IPAddress(ipaddress.ip_address('10.0.0.1'))]
        self.assertEqual('IP:10.0.0.1, DNS:host', utils.get_san_str(
            utils.validate_or_build_san('host', x509.SubjectAlternativeName(san))))

    def test_get_san_from_certificate_without_extensions(self):
        cert  = get_selfsign_cert_obj()
        self.assertIsNone(utils.get_san(cert))


class TestCryptoObjText(unittest.TestCase):
    def test_get_cert_text(self):
        # Little bug in the OpenSSL which add a space after "X509v3 Subject Alternative Name:" in specific case
        self.assertEqual(get_cert_text().replace('X509v3 Subject Alternative Name:',
                                                      'X509v3 Subject Alternative Name: '),
                         utils.get_cert_text(get_cert_obj()))

    def test_get_csr_text(self):
        # Little bug in the OpenSSL which add a space after "X509v3 Subject Alternative Name:" in specific case
        self.assertEqual(get_csr_text().replace('X509v3 Subject Alternative Name:',
                                                     'X509v3 Subject Alternative Name: '),
                         utils.get_csr_text(get_csr_obj()))


class TestNbSecondsToDate(unittest.TestCase):
    @freeze_time("2021-12-04 12:30:00")
    def test_nb_seconds_to_date(self):
        self.assertEqual(0, utils.nb_seconds_to_date(datetime.date(2021, 12, 4)))
        self.assertEqual(60 * 60 * 24, utils.nb_seconds_to_date(datetime.date(2021, 12, 5)))

    def test_nb_seconds_to_date_old_date(self):
        with self.assertRaises(ValueError):
            utils.nb_seconds_to_date(datetime.date.today() - datetime.timedelta(days=1))


class TestPrintTabulated(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_tabulated_oneline(self, mock_stdout):
        utils.print_tabulated('my line')
        self.assertEqual('\tmy line\n', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_tabulated_multiline(self, mock_stdout):
        utils.print_tabulated('line1\n\tline2\nline3')
        self.assertEqual('\tline1\n\t\tline2\n\tline3\n', mock_stdout.getvalue())


class TestWritePEM(unittest.TestCase):
    def test_write_cert_pem_file_already_existing(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp()
        os.close(tmp_file_fd)

        with self.assertRaises(RuntimeError):
            utils.write_cert_pem(get_cert_obj(), tmp_file_path)

        os.remove(tmp_file_path)

    def test_write_cert_pem_file(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp()
        os.close(tmp_file_fd)
        os.remove(tmp_file_path)

        utils.write_cert_pem(get_cert_obj(), tmp_file_path)
        self.assertEqual(load_txt('tests/data/cert.pem'), load_txt(tmp_file_path))

        os.remove(tmp_file_path)

    def test_write_private_key_pem_file_already_existing(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp()
        os.close(tmp_file_fd)

        with self.assertRaises(RuntimeError):
            utils.write_private_key_pem(get_privatekey_obj(), tmp_file_path)

        os.remove(tmp_file_path)

    def test_write_private_key_pem_file(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp()
        os.close(tmp_file_fd)
        os.remove(tmp_file_path)

        utils.write_private_key_pem(get_privatekey_obj(), tmp_file_path)
        self.assertEqual(load_txt('tests/data/pkey.key'), load_txt(tmp_file_path))

        os.remove(tmp_file_path)


class TestGetCrlUrls(unittest.TestCase):
    def test_empty(self):
        cert = get_selfsign_cert_obj()
        self.assertIsNone(utils.get_crl_urls(cert))

    def test_one_crl(self):
        cert = get_cert_with_crl_ocsp_obj()
        self.assertEqual(['http://crl.example.com/crl.pem'], utils.get_crl_urls(cert))


class TestGetOcsplUrls(unittest.TestCase):
    def test_empty(self):
        cert = get_selfsign_cert_obj()
        self.assertIsNone(utils.get_ocsp_url(cert))

    def test_one_crl(self):
        cert = get_cert_with_crl_ocsp_obj()
        self.assertEqual(['http://ocsp.example.com'], utils.get_ocsp_url(cert))

class TestGetCertPem(unittest.TestCase):
    def test(self):
        cert = get_cert_obj()
        with open('tests/data/cert.pem', 'r') as f:
            pem_data = f.read()

        self.assertEqual(pem_data, utils.get_cert_pem(cert))

class TestGetPrivateKeyFromPem(unittest.TestCase):
    def test_not_a_key(self):
        with open('tests/data/cert.pem', 'r') as f:
            pem_data = f.read()

        with self.assertRaises(RuntimeError):
            utils.get_private_key_from_pem(pem_data)

    def test_without_password(self):
        with open('tests/data/ca.key', 'r') as f:
            pem_data = f.read()

        utils.get_private_key_from_pem(pem_data)

    @patch('getpass.getpass', return_value='password')
    def test_with_password(self, mock_getpass):
        with open('tests/data/key-with-password.key', 'r') as f:
            pem_data = f.read()

        utils.get_private_key_from_pem(pem_data)

        mock_getpass.assert_called_once_with('Enter the private key passphrase : ')

    @patch('getpass.getpass', return_value='incorrect-password')
    def test_with_bad_password(self, mock_getpass):
        with open('tests/data/key-with-password.key', 'r') as f:
            pem_data = f.read()

        with self.assertRaises(RuntimeError):
            utils.get_private_key_from_pem(pem_data)

        mock_getpass.assert_called_once_with('Enter the private key passphrase : ')

class TestVerifySignature(unittest.TestCase):
    def test_rsa_matching(self):
        ca_cert = load_cert('tests/data/ca2.pem')
        cert = load_cert('tests/data/cert-with-crl-ocsp.pem')

        self.assertTrue(utils.verify_signature(cert, ca_cert))

    def test_rsa_not_matching(self):
        ca_cert = get_cert_obj()
        cert = get_selfsign_cert_obj()

        self.assertFalse(utils.verify_signature(cert, ca_cert))

class TestWriteP12(unittest.TestCase):
    def test_file_existing(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(suffix='.p12')
        os.close(tmp_file_fd)

        with self.assertRaises(RuntimeError):
            utils.write_p12(tmp_file_path, 'mypass', 'mycert', get_cert_obj())

        os.remove(tmp_file_path)

    def test_empty_passphrase(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(suffix='.p12')
        os.close(tmp_file_fd)
        os.remove(tmp_file_path)

        with self.assertRaises(ValueError):
            utils.write_p12(tmp_file_path, '', 'mycert', get_cert_obj())

    def test_write_password(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(suffix='.p12')
        os.close(tmp_file_fd)
        os.remove(tmp_file_path)

        utils.write_p12(tmp_file_path, 'password', 'mycert', get_cert_obj())
        os.remove(tmp_file_path)

    def test_write_without_password(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(suffix='.p12')
        os.close(tmp_file_fd)
        os.remove(tmp_file_path)

        utils.write_p12(tmp_file_path, None, 'mycert', get_cert_obj())
        os.remove(tmp_file_path)

    def test_write_private_key(self):
        tmp_file_fd, tmp_file_path = tempfile.mkstemp(suffix='.p12')
        os.close(tmp_file_fd)
        os.remove(tmp_file_path)

        utils.write_p12(tmp_file_path, None, 'mycert', get_cert_obj(), get_privatekey_obj())
        os.remove(tmp_file_path)

class TestEncryptDecrypt(unittest.TestCase):
    def test_without_padding(self):
        plaintext = b'helloworld123456'
        key = b'\xea\xe3\x5a\xfe\x65\x83\xf3\x73\x92\x6b\xe8\x07\xf4\xe2\x38\xe8\x5c\xf4\x06\xf9\x13\x10\x0d\x42\x18\x91\x8b\xd5\xaf\x56\x83\x54'
        nonce, tag, encrypted = utils.encrypt(plaintext, key)
        self.assertEqual(utils.decrypt(encrypted, key, nonce), plaintext)

    def test_with_padding(self):
        plaintext = b'helloworl'
        key = b'\xea\xe3\x5a\xfe\x65\x83\xf3\x73\x92\x6b\xe8\x07\xf4\xe2\x38\xe8\x5c\xf4\x06\xf9\x13\x10\x0d\x42\x18\x91\x8b\xd5\xaf\x56\x83\x54'
        nonce, tag, encrypted = utils.encrypt(plaintext, key)
        self.assertEqual(utils.decrypt(encrypted, key, nonce), plaintext)

    def test_b64_without_padding(self):
        plaintext = b'helloworld123456'
        key = b'\xea\xe3\x5a\xfe\x65\x83\xf3\x73\x92\x6b\xe8\x07\xf4\xe2\x38\xe8\x5c\xf4\x06\xf9\x13\x10\x0d\x42\x18\x91\x8b\xd5\xaf\x56\x83\x54'
        b64 = utils.encrypt_to_b64(plaintext, key)
        self.assertEqual(utils.decrypt_from_b64(b64, key), plaintext)

    def test_b64_with_padding(self):
        plaintext = b'helloworl'
        key = b'\xea\xe3\x5a\xfe\x65\x83\xf3\x73\x92\x6b\xe8\x07\xf4\xe2\x38\xe8\x5c\xf4\x06\xf9\x13\x10\x0d\x42\x18\x91\x8b\xd5\xaf\x56\x83\x54'
        b64 = utils.encrypt_to_b64(plaintext, key)
        self.assertEqual(utils.decrypt_from_b64(b64, key), plaintext)


class TestSingleton(unittest.TestCase):
    def test_singleton_returns_same_instance(self):
        @utils.singleton
        class TestClass:
            def __init__(self):
                self.value = 0

        instance1 = TestClass()
        instance2 = TestClass()

        self.assertIs(instance1, instance2)
        self.assertEqual(id(instance1), id(instance2))

    def test_singleton_shared_state(self):
        @utils.singleton
        class Counter:
            def __init__(self):
                self.count = 0

            def increment(self):
                self.count += 1

        counter1 = Counter()
        counter1.increment()

        counter2 = Counter()
        counter2.increment()

        self.assertEqual(counter1.count, 2)
        self.assertEqual(counter2.count, 2)
        self.assertIs(counter1, counter2)

    def test_singleton_with_init_args(self):

        @utils.singleton
        class ConfigClass:
            def __init__(self, name, value=10):
                self.name = name
                self.value = value

        instance1 = ConfigClass("first", value=100)
        self.assertEqual(instance1.name, "first")
        self.assertEqual(instance1.value, 100)

        instance2 = ConfigClass("second", value=200)
        self.assertIs(instance1, instance2)
        self.assertEqual(instance2.name, "first")  # Garde les valeurs originales
        self.assertEqual(instance2.value, 100)


class TestIsValidHttpUrl(unittest.TestCase):
    def test_valid_url(self):
        self.assertTrue(utils.is_valid_http_url("https://www.example.com"))
        self.assertTrue(utils.is_valid_http_url("https://example.com"))
        self.assertTrue(utils.is_valid_http_url("http://www.example.com"))
        self.assertTrue(utils.is_valid_http_url("http://example.com"))
        self.assertFalse(utils.is_valid_http_url("ftp://www.example.com"))
        self.assertFalse(utils.is_valid_http_url("scp://example.com"))

        self.assertFalse(utils.is_valid_http_url("not url"))
        self.assertFalse(utils.is_valid_http_url("http: // example.com"))
        self.assertFalse(utils.is_valid_http_url("http:\x10// example.com"))

class TestFormatSerialNumber(unittest.TestCase):
    def test(self):
        cert = get_ca_obj()
        self.assertEqual('6b:8c:02:7a:8a:64:11:d0:e0:94:e9:22:58:99:1a:d6:95:58:0e:0e', utils.format_serial_number(cert))

        cert = load_cert('tests/data/cert-with-crl-ocsp.pem')
        self.assertEqual('06:9a:8b:0b:aa:2a:53:a8', utils.format_serial_number(cert))

        cert = load_cert('tests/data/self-sign.pem')
        self.assertEqual('28:11:59:2f:b8:5e:ed:be:0e:98:4c:e9:c6:2e:21:b1:27:bf:5a:17', utils.format_serial_number(cert))


if __name__ == '__main__':
    unittest.main()
