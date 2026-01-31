import base64
import binascii
import datetime
import getpass
import ipaddress
import os.path
import re
import secrets
import sys
from enum import IntEnum
from typing import Optional, cast, Protocol
from urllib.parse import urlparse

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtensionOID, NameOID, AuthorityInformationAccessOID
from cryptography.exceptions import InvalidSignature

"""
The RegEx to match a domain. Examples :
  - wiki
  - wiki.internal-domain.lan
  - *.sub.internal-domain.lan
"""
regex_domain = re.compile(r'^(\*\.)?([a-zA-Z0-9_-]+\.?)+$')

"""
The RegEx to match a Subject Alternate Name.

  - DNS: host, DNS: host2.domain.lan, IP: 10.0.0.1, IP: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
"""
regex_san = re.compile(r'^(('
                       r'(DNS:[ ]?((\*\.)?([a-zA-Z0-9_-]+\.?))+)'  # DNS, see regex_domain
                       r'|'
                       r'(IP:[ ]?('  # IPv4
                       r'((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))'
                       r'|'  # or IPv6
                       r'((?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4})'
                       r')))'
                       r'(,?[ ]?))+'  # Followed by "," or ", "
                       r'(?<![ ,])$')  # But the string cannot be ending with "," or ", "

"""
The RegEx for the Common Name : host or IPv4 or IPv6
"""
regex_cn = re.compile(r'^(((\*\.)?([a-zA-Z0-9_-]+\.?)+)|'
                      r'((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))|'
                      r'((?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}))$')


def ask(prompt: str, values: Optional[list] = None, disable_show_values: bool = False, can_be_empty: bool = False,
        disable_lowering: bool = False) -> Optional[str]:
    """
    Ask the user for an input.

    The prompt is written to stdout and the value is read from stdin.

    The prompt will be like that :
        "<prompt message> : "
        "<prompt message> (<value 1>, <value 2>, <value 3>) : "

    The optional disable_show_values parameter disable showing values in the prompt.

    The optional values parameter is the fixed list of the authorized values. If defined, the prompt is asking until the
    user is entering one of these values.

    The optional can_be_empty parameter allows the user to not enter a value but send back a empty value.

    By default, the input string is lower(). If you doesn't want that, you can use the disable_lowering parameter.

    :param prompt: the prompt message
    :param values: the list of valid values
    :param disable_show_values: disable showing values
    :param can_be_empty: indicate if the response can be empty
    :param disable_lowering: disable the lower() of the response
    :return: the user response
    """
    if values:
        values = [str(v).lower() for v in values]

        if not disable_show_values:
            prompt += f' ({", ".join(values)})'

    prompt += ' : '

    while True:
        print(prompt, end='')
        answer = input().strip()
        answer_lower = answer.lower()

        if values:
            if answer_lower in values or (can_be_empty and len(answer) == 0):
                break
        else:
            if (len(answer) == 0 and can_be_empty) or len(answer) > 0:
                break

    if len(answer) == 0:
        return None

    if disable_lowering:
        return answer
    else:
        return answer_lower

class PEMFormatType(IntEnum):
    """
    The PEM type
    """
    CERT = 1
    KEY = 2
    CSR = 3

def ask_pem_format(prompt: str, pem_type: PEMFormatType) -> Optional[str]:
    """
    Ask the user for data in the PEM format.

    The targeted data is providing through the pem_type parameter.

    This function accepts multi-line PEM. The first line must be the ASCII armored definition "----- BEGIN...". This
    function will stop reading from stdin when the the "----- END..." is reached.

    The PEM data is not checked.

    :param prompt: the prompt message
    :param pem_type: the PEM format type
    :return: the entered PEM data
    """
    answer = ''

    prompt += ' :'
    print(prompt)

    if pem_type == PEMFormatType.CERT:
        re_start_line = re.compile('-----BEGIN CERTIFICATE-----')
        re_end_line = re.compile('-----END CERTIFICATE-----')
    elif pem_type == PEMFormatType.KEY:
        re_start_line = re.compile('-----BEGIN (RSA )?PRIVATE KEY-----')
        re_end_line = re.compile('-----END (RSA )?PRIVATE KEY-----')
    elif pem_type.CSR:
        re_start_line = re.compile('-----BEGIN CERTIFICATE REQUEST-----')
        re_end_line = re.compile('-----END CERTIFICATE REQUEST-----')
    else:
        raise RuntimeError(f'PEM type {pem_type} not supported')

    end_line_detected = False
    first = True
    while 1:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            break

        if first:
            first = False
            if not re_start_line.match(line.rstrip()):
                raise ValueError('No or bad start line')

        answer += line

        if re_end_line.match(line.rstrip()):
            end_line_detected = True
            break

    if not end_line_detected:
        raise ValueError('No end line detected')

    return answer

def ask_date_in_future() -> datetime.datetime:
    """
    Ask the user for a date in the future.

    If an error is detected, the error is written on stdout and the same question is prompted again.

    :return: the date
    """
    error = True
    d = ''

    while error:
        d = ask('Enter a date in the future (DD/MM/YYYY)')

        try:
            d = datetime.datetime.strptime(d, '%d/%m/%Y').replace(hour=0, minute=0, second=0, microsecond=0,
                                                                  tzinfo=datetime.timezone.utc)

            if d.date() <= datetime.date.today():
                print(f'\tThe date must be in the future')
            else:
                error = False
        except ValueError:
            print(f'\t{d} is invalid')

    return d

def ask_cn() -> str:
    """
    Ask the user for Common Name.

    The user can enter 1 host or IP.

    If an error is detected, the error is written on strerr and the same question is prompted again.

    :return: the CN
    """
    error = True
    cn = ''

    while error:
        cn = ask('Common Name')

        if not regex_cn.match(cn):
            print(f'\t{cn} is invalid')
        else:
            error = False

    return cn

def ask_hosts() -> list[str]:
    """
    Ask the user for hosts.

    The user can enter 0, 1 or n hosts separated by a comma. The host value can be :
        * the hostname : wiki
        * the FQDN : wiki.internal-domain.lan
        * the * wildcard : *.sub.internal-domain.lan

    If an error is detected, the error is written on strerr and the same question is prompted again.

    :return: the hosts
    """
    error = True
    domains = set()

    while error:
        input_domains = ask('Enter alternative names separated by a comma (eg: srv.internal.lan)', can_be_empty=True)
        domains.clear()

        if not input_domains or len(input_domains) == 0:
            break

        error = False
        for d in input_domains.split(','):
            d = d.strip()

            if regex_domain.match(d):
                try:
                    ipaddress.ip_address(d)
                    error = True
                    print(f'\t{d} is an IP address')
                except ValueError:
                    domains.add(d)
            else:
                error = True
                print(f'\t{d} is invalid')

    return list(sorted(domains))

def ask_ips() -> list[str]:
    """
    Ask the user for IP addresses.

    The user can enter 0, 1 or n IP addresses separated by a comma. IPv4 and IPv6 are supported.

    If an error is detected, the error is written on strerr and the same question is prompted again.

    :return: the IPs
    """
    error = True
    ips = set()

    while error:
        input_ips = ask('Enter IPs separated by a comma (eg: 10.0.0.1, 10.254.0.1)', can_be_empty=True)
        ips.clear()

        if not input_ips or len(input_ips) == 0:
            break

        error = False
        for ip in input_ips.split(','):
            ip = ip.strip()

            try:
                ipaddress.ip_address(ip)
                ips.add(ip)
            except ValueError:
                error = True
                print(f'\t{ip} is invalid')

    return list(sorted(ips))

def ask_cn_and_san() -> tuple[str, x509.SubjectAlternativeName]:
    """
    Ask the user for the CN, the alternative hosts and alternative IPS.

    :return: the CN and the build SAN
    """
    cn = ask_cn()
    alternate_hosts = ask_hosts()
    alternate_ips = ask_ips()

    try:  # CN is IP
        ipaddress.ip_address(cn)
        alternate_ips.append(cn)
    except ValueError:
        alternate_hosts.append(cn)

    san = [x509.DNSName(h) for h in alternate_hosts]
    san += [x509.IPAddress(ipaddress.ip_address(i)) for i in alternate_ips]

    return cn, x509.SubjectAlternativeName(san)

def confirm(prompt: str) -> bool:
    """
    Ask user to enter Y or N (case-insensitive) to confirm an action.

    :param prompt: the prompt message
    :return: True if the answer is Y.
    """
    return ask(f'{prompt} ? [y/n]', ['y', 'n'], disable_show_values=True) == 'y'

def ask_password(prompt: str) -> str:
    """
    Ask (securely) the user to enter a password.

    :param prompt: the prompt message
    :return: the password encoded
    """
    prompt += ' : '

    return getpass.getpass(prompt)

def ask_private_key_passphrase() -> str:
    """
    Ask the user for the private key passphrase.

    :return: the passphrase
    """
    return ask_password('Enter the private key passphrase')

def generate_random_serial_number() -> int:
    """
    Generate (securely) a random serial number for a certificate [0, 2^64].

    :return: the serial number
    """
    return secrets.randbelow(2 ** 64)

class HasExtensions(Protocol):
    """
    Protocol describing any object exposing X.509 extensions.

    This protocol is used for static duck typing: any object that provides
    an ``extensions`` attribute of type ``x509.Extensions`` is considered
    compatible, regardless of its concrete class.

    This allows writing generic functions operating on both
    ``x509.Certificate`` and ``x509.CertificateSigningRequest`` (and any
    future compatible type) without requiring a common base class.

    Notes:
       - This protocol is only used by static type checkers (mypy, pyright).
       - It has no effect at runtime and introduces no performance cost.
       - No inheritance is required from the implementing classes.
    """
    @property
    def extensions(self) -> x509.Extensions: ...

def get_san(obj: HasExtensions) -> Optional[x509.SubjectAlternativeName]:
    """
    Get the Subject Alternative Name from a certificate object.

    :param obj: the certificate or
    :return: the SAN if defined
    """
    try:
        extension = obj.extensions.get_extension_for_oid(
            ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )

        return cast(x509.SubjectAlternativeName, extension.value)
    except x509.ExtensionNotFound:
        pass

    return None

def get_san_str(san_extension_value: x509.SubjectAlternativeName) -> Optional[str]:
    """
    Get a string from the SAN extension value.

    A host is "DNS:<host>".
    An IP is "IP:<ip>"
    Each value is separated with a coma + space

    :param san_extension_value: the SAN extension value
    :return: the SAN if defined
    """
    san_list = []
    for name in san_extension_value:
        if isinstance(name, x509.DNSName):
            san_list.append(f'DNS:{name.value}')
        elif isinstance(name, x509.IPAddress):
            san_list.append(f'IP:{name.value}')
    return ', '.join(san_list) if san_list else None

def get_cn(o: x509.Certificate|x509.CertificateSigningRequest) -> str:
    """
    Get the Common Name from a certificate signing request object.

    :param o: the certificate or the certificate signing request
    :return: the CN
    """
    cn_attributes = o.subject.get_attributes_for_oid(NameOID.COMMON_NAME)

    if cn_attributes:
        return cn_attributes[0].value
    else:
        return ""

def get_crl_urls(cert: x509.Certificate) -> Optional[list[str]]:
    """
    Get the CRL URLs from a certificate.

    :param cert: the certificate
    :return: a list of URL or None
    """

    crl_urls = []
    try:
        ext = cert.extensions.get_extension_for_oid(ExtensionOID.CRL_DISTRIBUTION_POINTS)
        for dp in ext.value:
            for name in dp.full_name:
                if isinstance(name, x509.UniformResourceIdentifier):
                    crl_urls.append(name.value)
    except x509.ExtensionNotFound:
        pass

    if len(crl_urls) > 0:
        return crl_urls
    else:
        return None

def get_ocsp_url(cert: x509.Certificate) -> Optional[list[str]]:
    """
    Get the OCSP URLs from a certificate.

    :param cert: the certificate
    :return: a list of URL or None
    """
    ocsp_urls = []

    try:
        aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value

        for access_desc in aia:
            if access_desc.access_method == AuthorityInformationAccessOID.OCSP:
                ocsp_urls.append(access_desc.access_location.value)
    except x509.ExtensionNotFound:
        pass

    if len(ocsp_urls) > 0:
        return ocsp_urls
    else:
        return None

def validate_or_build_san(cn: str, san: Optional[x509.SubjectAlternativeName]) -> x509.SubjectAlternativeName:
    """
    Ensure that the CN is in the SAN. Create SAN if empty.

    :param cn: the Common Name
    :param san: the optional Subject Alternative Name
    :return: the final Subject Alternative Name
    """
    # Checking if the CN is an IP address or a hostname
    try:
        cn_obj = x509.IPAddress(ipaddress.ip_address(cn))
    except ValueError:
        cn_obj = x509.DNSName(cn)

    #  Browse SAN
    san_entries = []
    cn_found_in_san = False

    if san is not None:
        for i in san:
            if i.value == cn_obj.value:
                cn_found_in_san = True

            san_entries.append(i)

    if cn_found_in_san:
        return san

    san_entries.append(cn_obj)

    return x509.SubjectAlternativeName(san_entries)

def get_cert_text(cert: x509.Certificate) -> str:
    """
    Get the text version of a certificate object.

    :param cert: the certificate
    :return: the text version
    """
    lines = [f"Certificate:"]

    lines.append(f"\tSerial Number: {cert.serial_number:x}")
    lines.append(f"\tSignature Algorithm: {cert.signature_algorithm_oid._name}")
    lines.append(f"\tIssuer: {cert.issuer.rfc4514_string()}")
    lines.append(f"\tValidity:")
    lines.append(f"\t\tNot Before: {cert.not_valid_before_utc}")
    lines.append(f"\t\tNot After : {cert.not_valid_after_utc}")
    lines.append(f"\tSubject: {cert.subject.rfc4514_string()}")

    # Extensions
    if len(cert.extensions):
        lines.append("\tX509v3 extensions:")
        lines.append(x509v3_extensions_to_str(cert.extensions))

    return "\n".join(lines)

def get_cert_builder_text(cert_builder: x509.CertificateBuilder) -> str:
    """
    Get the text version of a certificate builder object.

    :param cert_builder: the certificate builder
    :return: the text version
    """
    lines = [f"Certificate:"]

    lines.append(f"\tIssuer: {cert_builder._issuer_name.rfc4514_string()}")
    lines.append(f"\tValidity:")
    lines.append(f"\t\tNot Before: {cert_builder._not_valid_before}")
    lines.append(f"\t\tNot After : {cert_builder._not_valid_after}")
    lines.append(f"\tSubject: {cert_builder._subject_name.rfc4514_string()}")

    # Extensions
    if len(cert_builder._extensions):
        lines.append("\tX509v3 extensions:")
        lines.append(x509v3_extensions_to_str(cert_builder._extensions))

    return "\n".join(lines)

def get_csr_text(csr: x509.CertificateSigningRequest) -> str:
    """
    Get the text version of a certificate signing request object.

    :param csr: the certificate signing request
    :return: the text version
    """
    lines = [f"Certificate Request:"]

    lines.append(f"\tSignature Algorithm: {csr.signature_algorithm_oid._name}")
    lines.append(f"\tSubject: {csr.subject.rfc4514_string()}")

    # Extensions
    if len(csr.extensions):
        lines.append("\tX509v3 extensions:")
        lines.append(x509v3_extensions_to_str(csr.extensions))

    return "\n".join(lines)

def x509v3_extensions_to_str(extensions: x509.Extensions) -> str:
    """
    Convert the x509 v3 extensions to a string.

    :param extensions: the x509 v3 extensions
    :return: the text version, can be empty
    """
    lines = []
    for ext in extensions:
        name = ext.oid._name
        value = ext.value
        if isinstance(value, x509.SubjectAlternativeName):
            value = get_san_str(value)
        elif isinstance(value, x509.SubjectKeyIdentifier):
            value = binascii.hexlify(value.digest, sep=':').decode('utf8')
        elif isinstance(value, x509.AuthorityKeyIdentifier):
            value = binascii.hexlify(value.key_identifier, sep=':').decode('utf8')
        elif isinstance(value, x509.CRLDistributionPoints):
            values_str = []

            for v in value:
                for res in v.full_name:
                    values_str.append(res.value)

            value =  ', '.join(values_str)
        elif isinstance(value, x509.AuthorityInformationAccess):
            values_str = []

            for d in value:
                if isinstance(d, x509.AccessDescription):
                    if d.access_method == AuthorityInformationAccessOID.OCSP:
                        values_str.append(f'OCSP:{d.access_location.value}')
                else:
                    values_str.append(str(d))

            value = ', '.join(values_str)

        lines.append(f"\t\t{name}: {value}")


    return "\n".join(lines)

def nb_seconds_to_date(expire_date: datetime.date) -> int:
    """
    Compute the number of seconds between now and the expired date. Note that the date is given without the time part
    so we use the current hours/minutes/seconds.

    :param expire_date: the expiration date
    :return: the number of seconds
    """
    if expire_date < datetime.date.today():
        raise ValueError('The expire date is not in the future')

    expire_dt = datetime.datetime.now().replace(year=expire_date.year, month=expire_date.month, day=expire_date.day)
    return int((expire_dt - datetime.datetime.now()).total_seconds())

def print_tabulated(text: str) -> None:
    """
    Print the text with one tabulation.

    :param text: the text to print
    """

    text = '\t' + text.replace('\n', '\n\t')
    print(text)

def get_cert_pem(cert: x509.Certificate) -> str:
    """
    Get the certificate in PEM format.

    :param cert: the certificate
    :return: The PEM string
    """
    return cert.public_bytes(encoding=serialization.Encoding.PEM).decode('utf8')

def get_private_key_pem(key: PrivateKeyTypes) -> str:
    """
    Get the private key in PEM format

    :param key: the private key
    :return: the PEM string
    """
    return key.private_bytes(encoding=serialization.Encoding.PEM,
                             format=serialization.PrivateFormat.TraditionalOpenSSL,
                             encryption_algorithm=serialization.NoEncryption()).decode('utf8')

def write_cert_pem(cert: x509.Certificate, filepath: str):
    """
    Write the certificate in PEM format into the provided filepath.

    If the file already exists, a RuntimeError is raised.

    :param cert: the certificate
    :param filepath: the target filepath
    """
    if os.path.exists(filepath):
        raise RuntimeError(f'The filepath "{filepath}" already exists')

    with open(filepath, 'wb') as f:
        f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))

def write_private_key_pem(key: PrivateKeyTypes, filepath: str):
    """
    Write the private key in PEM format into the provided filepath.

    If the file already exists, a RuntimeError is raised.

    :param key: the private key
    :param filepath: the target filepath
    """
    if os.path.exists(filepath):
        raise RuntimeError(f'The filepath "{filepath}" already exists')

    with open(filepath, 'wb') as f:
        f.write(
            get_private_key_pem(key).encode('utf8')
        )

def get_private_key_from_pem(pem: str) -> PrivateKeyTypes:
    """
    Get the private key from PEM format.

    Ask password if needed. Raise RuntimeError if the PEM is invalid or if the password is incorrect

    :param pem: the PEM string
    :return: the private key
    :raise RuntimeError: if the private key or the password is incorrect
    """
    try:
        try:
            key_obj = serialization.load_pem_private_key(pem.encode('utf8'),
                                                         password=None,
                                                         backend=default_backend())
        except TypeError:  # Key encrypted
            key_obj = serialization.load_pem_private_key(pem.encode('utf8'),
                                                         password=ask_private_key_passphrase().encode('utf8'),
                                                         backend=default_backend())
    except ValueError:
        raise RuntimeError('Invalid passphrase or invalid private key')

    return key_obj

def verify_signature(child: x509.Certificate, issuer: x509.Certificate) -> bool:
    """
    Verify that child is signed by issuer_public_key

    :param child: the child certificate
    :param issuer: the issuer certificate
    :return: bool
    """
    issuer_public_key = issuer.public_key()
    try:
        if isinstance(issuer_public_key, rsa.RSAPublicKey):
            issuer_public_key.verify(
                signature=child.signature,
                data=child.tbs_certificate_bytes,
                padding=padding.PKCS1v15(),
                algorithm=child.signature_hash_algorithm,
            )

        elif isinstance(issuer_public_key, ec.EllipticCurvePublicKey):
            issuer_public_key.verify(
                signature=child.signature,
                data=child.tbs_certificate_bytes,
                signature_algorithm=ec.ECDSA(child.signature_hash_algorithm),
            )
        else:
            raise TypeError("Unsupported public key type")

        return True
    except InvalidSignature:
        return False

def write_p12(filepath: str, passphrase: str, name: str, cert: x509.Certificate, key: Optional[PrivateKeyTypes] = None):
    """
    Write the certificate (and the private key if provided) in PKCS12 format.

    If the file already exists, a RuntimeError is raised.

    :param filepath: the target filepath
    :param passphrase: the password
    :param name: the certificate name
    :param cert: the certificate
    :param key: the private key
    """
    if os.path.exists(filepath):
        raise RuntimeError(f'The filepath "{filepath}" already exists')

    if passphrase is not None and len(passphrase) == 0:
        raise ValueError('The provided passphrase is empty')

    if passphrase:
        encryption = serialization.BestAvailableEncryption(passphrase.encode())
    else:
        encryption = serialization.NoEncryption()

    p12 = pkcs12.serialize_key_and_certificates(
        name=name.encode('utf8'),
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=encryption
    )

    with open(filepath, "wb") as f:
        f.write(p12)

def decrypt(data: bytes, key: bytes, nonce: bytes, tag: Optional[bytes] = None) -> bytes:
    """
    Decrypt data with the key (AES_EAX).
    """
    cipher = AES.new(key, AES.MODE_GCM, nonce)

    if tag:
        return unpad(cipher.decrypt_and_verify(data, tag), 16)
    else:
        return unpad(cipher.decrypt(data), 16)

def decrypt_from_b64(data: str, key: bytes) -> bytes:
    """
    Decrypt data with the key (AES_EAX) from base64
    """
    data = base64.b64decode(data)

    return decrypt(data=data[32:], key=key, nonce=data[:16], tag=data[16:32])

def encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
    """
    Encrypt data with the key (AES_EAX)
    """
    cipher = AES.new(key, AES.MODE_GCM)

    encrypted, tag = cipher.encrypt_and_digest(pad(plaintext, 16))
    return cipher.nonce, tag, encrypted

def encrypt_to_b64(plaintext: bytes, key: bytes) -> str:
    """
    Encrypt data with the key (AES_EAX) and return it encrypted as a base64 string
    """
    nonce, tag, encrypted = encrypt(plaintext, key)

    return base64.b64encode(nonce + tag + encrypted).decode('utf8')

def singleton(c):
    """
    Singleton decorator

    :param c: the class
    :return: the class instance
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if c not in instances:
            instances[c] = c(*args, **kwargs)

        return instances[c]

    return getinstance

def is_valid_http_url(url: str) -> bool:
    """
    Check if a URL is a valid HTTP(S) URL.

    :param url: the URL
    :return: True or False
    """
    try:
        result = urlparse(url)
        return (
            result.scheme in ("http", "https") and
            bool(result.netloc)
        )
    except Exception:
        return False

def format_serial_number(cert: x509.Certificate) -> str:
    """
    Convert a certificate serial_number to OpenSSL-style hex with colons.

    :param cert: the certificate
    """
    serial = cert.serial_number  #
    hex_serial = f"{serial:x}"

    # Add "0" if needed
    if len(hex_serial) % 2 != 0:
        hex_serial = "0" + hex_serial

    # Regrouper par octets
    octets = [hex_serial[i:i+2] for i in range(0, len(hex_serial), 2)]

    return ":".join(octets)