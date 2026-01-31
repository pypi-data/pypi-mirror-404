import base64
import datetime
import os
import re
import sys
from typing import Optional
import subprocess

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509.oid import NameOID, AuthorityInformationAccessOID
from peewee import DatabaseError

from .masterkey import MasterKeyHelper
from .models import (CRLSigningCertificate, CA, Config, ConfigType, Certificate, database, CertificateRevokedReason,
                     DATABASE_FILENAME, HashAlgo)
from .utils import ask_pem_format, get_san, generate_random_serial_number, get_csr_text, PEMFormatType, \
    validate_or_build_san, regex_domain, confirm, ask, ask_password, ask_date_in_future, get_cn, write_cert_pem, \
    write_private_key_pem, write_p12, ask_cn_and_san, get_private_key_from_pem, get_cert_pem, get_private_key_pem, \
    get_san_str, get_cert_builder_text, print_tabulated, is_valid_http_url, get_ocsp_url, verify_signature, \
    get_crl_urls, format_serial_number

"""
Valid key sizes
"""
VALID_KEY_SIZES = [1024, 2048, 4096, 8192]

class CAManager:
    """
    Certificate Authority Manager
    """
    def __init__(self):
        """
        Constructor.

        By default, the manager is not loaded. This is useful for the first start because the vault must be created.
        """
        # Containing the Certificate Authority when loaded from the vault
        self.ca = None

        # CA vault password
        self.masterkey_helper = MasterKeyHelper()

    def create_vault(self, vault_password: Optional[str] = None) -> None:
        """
        Setup the vault for the first use.

        The vault cannot be existing. The user is prompted to enter :
            - a password to encrypt the vault
            - the CA certificate
            - the CA key (and the password protecting the key if any)
        """
        if os.path.isfile(DATABASE_FILENAME):
            sys.stderr.write(f'Vault "{DATABASE_FILENAME}" is already existing\n')
            exit(-1)

        # Master key and password salt
        master_key, password_salt = self.masterkey_helper.generate_new_to_b64()

        database.init(DATABASE_FILENAME)

        with database:
            # Create table
            database.create_tables([CA, Certificate, CRLSigningCertificate, Config])

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

        self.add_ca()

        print('The vault has been successfully created.')

    def load(self, ca_name: Optional[str] = None, dont_load_ca: bool = False) -> None:
        """
        Load the vault.

        The password is asking.

        :param ca_name: the name of the CA to load. If not provided, the default CA is loaded.
        :param dont_load_Ca: if True, do not load the CA
        """
        if not os.path.isfile(DATABASE_FILENAME):
            sys.stderr.write('The vault doesn\'t exist yet. Please run with "setup" mode to initialize it.\n')
            exit(-1)

        # Ask the vault password and initialize the database with it
        database.init(DATABASE_FILENAME)

        try:
            database.get_tables()
        except DatabaseError as exc:
            if exc.args[0] == 'file is not a database':
                raise exc
            else:
                raise exc

        if dont_load_ca is False:
            nb_ca = CA.select().count()
            if nb_ca == 0:
                sys.stderr.write('The vault doesn\'t contains a CA. Please run with add-ca to add one\n')
                exit(-1)

            if ca_name:
                selected_ca = CA.select().where(CA.name ** f'%{ca_name}%')
                if selected_ca.count() == 0 or selected_ca.count() > 1:
                    sys.stderr.write('The selected CA cannot be found. Here is the possible values :\n')
                    sys.stderr.write(self._get_available_ca_str())

                    exit(-1)
            else:
                if nb_ca == 1:
                    selected_ca = CA.select()
                else:
                    selected_ca = CA.select().where(CA.is_default == True)

                    if selected_ca.count() == 0:
                        sys.stderr.write('There is not default CA, please select a CA :\n')
                        sys.stderr.write(self._get_available_ca_str())
                        exit(-1)

            self.ca = selected_ca.first()

            self.masterkey_helper.set_encrypted_masterkey(self._get_config('encrypted_masterkey'),
                                                          self._get_config('password_salt'))

            self.ca.load_cert()

            if nb_ca > 0:
                print(f'** Loaded using CA "{self.ca.name}" **')

    @database.connection_context()
    def _get_available_ca_str(self) -> str:
        s = ''
        for ca in CA.select():
            s += f'\t- {ca.name}\n'

        return s

    @database.connection_context()
    def add_ca(self) -> None:
        """
        Add a CA to the manager.

        The user is prompted to enter :
            - a name
            - the CA certificate
            - the CA key (and the password protecting the key if any)
            - an optional CRL Signing Certificate (certificate and key)
        """
        # Name
        name = ask('Enter the name of the CA to add', disable_lowering=True)
        if CA.select().where(CA.name == name).count() > 0:
            sys.stderr.write('This name is already in use. Please choose a different name')
            exit(-1)

        # Read CA pem from stdin
        ca_cert = None
        pem_ca_cert = None
        try:
            pem_ca_cert = ask_pem_format('Paste your CA certificate in PEM format', PEMFormatType.CERT)
            ca_cert = x509.load_pem_x509_certificate(pem_ca_cert.encode('utf8'), default_backend())
        except (ValueError, RuntimeError):
            sys.stderr.write(f'Invalid PEM certificate')
            exit(-1)

        # Read CA key from stdin
        ca_key = None
        pem_ca_key = None
        try:
            pem_ca_key = ask_pem_format('Paste your CA key in PEM format', PEMFormatType.KEY)
            ca_key = get_private_key_from_pem(pem_ca_key)
        except (ValueError, RuntimeError):
            sys.stderr.write(f'Invalid PEM key or password')
            exit(-1)

        # Check CA cert and key correspondence
        if ca_cert.public_key() != ca_key.public_key():
            sys.stderr.write(f'The certificate and the private key are not corresponding')
            exit(-1)

        # Ask if we need to create a CRL Signing Certificate
        crl_signer_cert = None
        crl_signer_key = None
        if confirm('Do you want to create a CRL Signing Certificate (if not, the CA will be used)'):
            try:
                pem_crl_signer_cert= ask_pem_format('Paste your CRL Signing certificate in PEM format', PEMFormatType.CERT)
                crl_signer_cert = x509.load_pem_x509_certificate(pem_crl_signer_cert.encode('utf8'), default_backend())
            except (ValueError, RuntimeError):
                sys.stderr.write(f'Invalid PEM certificate')
                exit(-1)

            try:
                pem_crl_signer_key = ask_pem_format('Paste your CRL Signing key in PEM format', PEMFormatType.KEY)
                crl_signer_key = get_private_key_from_pem(pem_crl_signer_key)
            except (ValueError, RuntimeError):
                sys.stderr.write(f'Invalid PEM key or password')
                exit(-1)

            # Check cert and key correspondence
            if crl_signer_cert.public_key() != crl_signer_key.public_key():
                sys.stderr.write(f'The certificate and the private key are not corresponding')
                exit(-1)

            # Check that this certificate is signed by the CA
            if not verify_signature(crl_signer_cert, ca_cert):
                sys.stderr.write(f'The CRL certificate is not signed by the CA')
                exit(-1)

        crl_output_path = ask('Enter the output path for the CRL file')
        if not crl_output_path.lower().endswith('.pem'):
            crl_output_path = crl_output_path + '.pem'

        if os.path.isdir(crl_output_path):
            sys.stderr.write(f'The provided output path is a directory')
            exit(-1)

        crl_urls = get_crl_urls(ca_cert)
        if not crl_urls:
            crl_url = ask('Enter the CRL URL (if not used, leave empty)', disable_lowering=True, can_be_empty=True)
            if crl_url and not is_valid_http_url(crl_url):
                sys.stderr.write(f'Invalid CRL URL')
                exit(-1)
        else:
            if len(crl_urls) > 1:
                print('WARNING: doesn\'t support multiple CRL URLs, using only the first one')

            crl_url = crl_urls[0]

        ocsp_urls = get_ocsp_url(ca_cert)
        if not ocsp_urls:
            ocsp_url = ask('Enter the OCSP URL (if not used, leave empty)', disable_lowering=True, can_be_empty=True)
            if ocsp_url and not is_valid_http_url(ocsp_url):
                sys.stderr.write(f'Invalid OCSP responder URL')
                exit(-1)
        else:
            if len(ocsp_urls) > 1:
                print('WARNING: doesn\'t support multiple OCSP URLs, using only the first one')

            ocsp_url = ocsp_urls[0]

        crl_post_script_path = ask('If you want, you may enter a script that will be executed after each CRL generation (leave empty if not used)',
                                   can_be_empty=True)
        if crl_post_script_path and not os.path.isfile(crl_post_script_path):
            sys.stderr.write(f'This path is invalid')
            exit(-1)

        is_default = confirm('Do you want to use this CA as default')
        if is_default:
            CA.update(is_default=False).where(CA.is_default == True).execute()

        crl_signing = None
        if crl_signer_cert:
            crl_signing = CRLSigningCertificate.create(
                cert=get_cert_pem(crl_signer_cert),
                key=get_private_key_pem(crl_signer_key),
            )

        # Create the CA in the database
        CA.create(
            name=name,
            is_default=is_default,
            is_intermediate=ca_cert.issuer != ca_cert.subject,
            cert=pem_ca_cert,
            key=pem_ca_key.encode('utf8'),
            crl_signing=crl_signing,
            crl_output_filename=crl_output_path,
            crl_url=crl_url,
            ocsp_url=ocsp_url,
            crl_post_script_path=crl_post_script_path,
        )

        print('The CA has been added.')

    @database.connection_context()
    def list(self, all_certificates: bool = False, only_soon_expired: bool = False):
        """
        Print the list of managed certificates.

        :param all_certificates: also the revoked/expired/renewed certificates
        :param only_soon_expired: only the soon expired certificates
        """
        if all_certificates and only_soon_expired:
            raise RuntimeError('Cannot use all and only_soon_expired')

        certs = Certificate.select()

        if only_soon_expired:
            now = datetime.datetime.now()
            next_month = now + datetime.timedelta(days=31)

            certs = certs.where((Certificate.ca == self.ca) & (Certificate.is_renewed == False) & (Certificate.not_after >= now) &
                                (Certificate.not_after <= next_month) & (Certificate.is_revoked == False))
        elif not all_certificates:
            certs = certs.where((Certificate.ca == self.ca) & (Certificate.is_revoked == False) & (Certificate.is_renewed == False) &
                                (Certificate.not_after > datetime.datetime.now()))

        nb_certs_found = certs.count()

        if nb_certs_found == 0:
            print('No certificate found')
        else:
            print(f'{nb_certs_found} {"certificate" if nb_certs_found < 2 else "certificates"} found :')

            for c in certs.iterator():
                print(f'\t{c}')

    def generate_new_cert(self) -> None:
        """
        Generate a new certificate with interactive prompt
        """

        key_size = self._get_config('default_key_size')
        hash_algo = HashAlgo.from_string(self._get_config('default_hash_algo'))
        use_crl = self.ca.crl_url is not None
        use_ocsp = self.ca.ocsp_url is not None

        if not confirm(f'Use default params ({self._get_config("default_key_size")} bits - '
                       f'{hash_algo.name}) - CRL: {'yes' if use_crl else 'no'} - OCSP: {'yes' if use_ocsp else 'no'}'):
            key_size = int(ask('Key size', values=VALID_KEY_SIZES))
            hash_algo = HashAlgo.from_string(ask('Hash algorithm', values=HashAlgo.get_str_values()))

            if self.ca.crl_url is not None:
                use_crl = confirm('Do you want to use the CRL for this certificate')

            if self.ca.ocsp_url is not None:
                use_ocsp = confirm('Do you want to use the OCSP for this certificate')

        cn, san = ask_cn_and_san()

        not_after = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=self._get_config("default_validity_seconds"))
        if not confirm(f'Use the default validity (will expire on {not_after.strftime("%d/%m/%Y")})'):
            not_after = ask_date_in_future()

        # Generate key
        key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

        try:
            cert, certificate = self._generate_signed_cert(cn, san, key, hash_algo, not_after, use_crl, use_ocsp)

            print('Certificate successfully created !\n')


            print_ca_chain = self.ca.is_intermediate and confirm('Print the CA chain after the certificate (required for nginx for example)')

            print(certificate.cert, end='')

            if print_ca_chain:
                print(self.ca.cert)
            else:
                print('')

            print(certificate.key)
        except (ValueError, RuntimeError) as e:
            sys.stderr.write(f'Error: {e}.\n')
            sys.stderr.write(f'The certificate cannot be created.\n')
            exit(-1)

    def sign_csr(self, csr_filepath: Optional[str] = None) -> None:
        """
        Sign a certificate.

        If the filepath is not provided, the content is read from stdin.

        :param csr_filepath: the Certificate Signing Request filepath (optional)
        """

        if csr_filepath:
            if not os.path.exists(csr_filepath):
                sys.stderr.write(f'The file "{csr_filepath}" doesn\'t exist\n')
                exit(-1)

            with open(csr_filepath, 'rb') as f:
                csr_content = f.read()
        else:
            csr_content = ask_pem_format('Paste your CSR in PEM format', PEMFormatType.CSR).encode('utf8')

        csr = None
        try:
            csr = x509.load_pem_x509_csr(csr_content, default_backend())
        except ValueError:
            sys.stderr.write(f'Invalid PEM CSR')
            exit(-1)

        print('You\'re going to process the following Certificate Signing Request :\n')
        print_tabulated(get_csr_text(csr))

        cn = get_cn(csr)
        san = get_san(csr)

        print('\nThis CSR apply to :')
        print(f'\tCommon Name : {cn}')
        print(f'\tSubject Alternative Name : {san if san else "*** not defined ***"}\n')

        print('Please note that the CN will automatically be added to the SAN if it is missing.\n')

        if confirm(f'Do you want to overwrite theses values'):
            cn, san = ask_cn_and_san()

            print('\nYou will overwrite the following values :')
            print(f'\tCommon Name : {cn}')
            print(f'\tSubject Alternative Name : {san}')

        if self.ca.crl_url is not None:
            use_crl = confirm('Do you want to use the CRL for this certificate')
        else:
            use_crl = False

        if self.ca.ocsp_url is not None:
            use_ocsp = confirm('Do you want to use the OCSP for this certificate')
        else:
            use_ocsp = False

        try:
            print('')
            cert, certificate = self._sign_csr(csr,
                                               overwrite_cn=cn,
                                               overwrite_san=san,
                                               use_crl_if_available=use_crl,
                                               use_ocsp_if_available=use_ocsp,
                                               ask_confirm=True)

            print('Certificate successfully signed !\n')
            print_ca_chain = self.ca.is_intermediate and confirm('Print the CA chain after the certificate (required for nginx for example)')

            print(certificate.cert, end='')

            if print_ca_chain:
                print(self.ca.cert)
            else:
                print('')

        except (ValueError, RuntimeError) as e:
            sys.stderr.write(f'Error: {e}.\n')
            sys.stderr.write(f'The certificate cannot be signed.')

    @database.connection_context()
    def renew(self, target_certificate: str):
        """
        Renew a certificate.

        :param target_certificate: CN or ID of the certificate
        """
        certificate = self.select_certificate(target_certificate)
        certificate.load_cert()

        try:
            certificate.load_key()
        except RuntimeError:
            sys.stderr.write(f'No private key stored, this certificate cannot be renewed\n')
            exit(-1)

        pub_key = certificate.cert_obj
        priv_key = certificate.key_obj

        not_after = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=self._get_config("default_validity_seconds"))
        if not confirm(f'Use the default validity (will expire on {not_after.strftime("%d/%m/%Y")})'):
            not_after = ask_date_in_future()

        if self.ca.crl_url is not None:
            use_crl = confirm('Do you want to use the CRL for this certificate')
        else:
            use_crl = False

        if self.ca.ocsp_url is not None:
            use_ocsp = confirm('Do you want to use the OCSP for this certificate')
        else:
            use_ocsp = False

        try:
            new_cert, new_certificate = self._generate_signed_cert(get_cn(pub_key),
                                                                   get_san(pub_key),
                                                                   priv_key,
                                                                   HashAlgo.from_x509_hash_algorithm(pub_key.signature_hash_algorithm),
                                                                   not_after,
                                                                   use_crl,
                                                                   use_ocsp,
                                                                   skip_cert_existence_check=True)

            # Set the previous certificate as renewed
            certificate.is_renewed = True
            certificate.save()

            print('Certificate renewed successfully !\n')

            print(new_certificate.cert)

            if confirm('Would you like to revoke the previous certificate'):
                self._revoke(certificate, CertificateRevokedReason.UNSPECIFIED, "Certificate renewal")

        except (ValueError, RuntimeError) as e:
            sys.stderr.write(f'Error: {e}.\n')
            sys.stderr.write(f'The certificate cannot be created.\n')
            exit(-1)

    def export(self, target_certificate: str, output_format: str, out_path: Optional[str]):
        """
        Export the certificate and its private key if available.

        If the output_format is "pem", the data is exported to a file if the out_path is provided (the file extension
        .pem is added for the certificate and .key for the key). If no out_path is provided, the data is printed to
        stdout.

        If the output_format is "p12", the data is exported to the out_path. If the out_path doesn't have the ".p12"
        extension, this method add the extension. The p12_passphrase must be provided.

        :param target_certificate: the certificate CN or ID
        :param output_format: the output format : "pem" or "p12"
        :param out_path: the output path
        """
        if output_format not in ('pem', 'p12'):
            raise ValueError(f'Output format "{output_format}" not supported')

        certificate = self.select_certificate(target_certificate)
        if not certificate:
            return

        print(f'You\'re going to export the certificate {certificate}...')

        p12_passphrase = None
        if output_format == 'p12':
            p12_passphrase = ask_password('Enter the password that will be used protect the .p12', )
            if len(p12_passphrase) == 0:
                if not confirm('No password entered. This is NOT RECOMMENDED. Do you want to continue without a password'):
                    exit(0)

                p12_passphrase = None
            else:
                p12_passphrase_confirm = ask_password('Confirm it')

                if p12_passphrase != p12_passphrase_confirm:
                    sys.stderr.write(f'The two provided passwords are not matching\n')
                    exit(-1)

        try:
            self._export(certificate, output_format, out_path, p12_passphrase)
        except RuntimeError as e:
            sys.stderr.write(f'Error: {str(e)}\n')
            exit(-1)

    def revoke(self, target_certificate: str):
        certificate = self.select_certificate(target_certificate)
        if not certificate:
            return

        print(f'You\'re going to REVOKE the certificate which therefore will no longer be valid : \n\t'
              f'{certificate}..\n')

        if not confirm(f'Are you sure'):
            return

        reason = CertificateRevokedReason.from_string(
            ask('What is the reason for the revocation?', ['Compromised', 'EoL', 'Other']))

        comment = ask('Comment (optional, for traceability)', can_be_empty=True)

        self._revoke(certificate, reason, comment)

    @database.connection_context()
    def _revoke(self, certificate: Certificate, revoke_reason: CertificateRevokedReason,
                revoke_comment: Optional[str] = None):
        """
        Revoke the provided certificate with the provided reason and comment.

        Generate a new CRL.

        :param certificate: the certificate to revoke
        :param revoke_reason: the revocation reason
        :param revoke_comment: the comment to revoke (optional)
        """
        certificate.is_revoked = True
        certificate.revoked_timestamp = datetime.datetime.now(datetime.UTC)
        certificate.revoked_reason = revoke_reason.value.encode('utf8')
        certificate.revoked_comment = revoke_comment

        certificate.save()

        print('The certificate was successfully revoked, generating CRL...')

        self.generate_crl()

    @database.connection_context()
    def generate_crl(self):
        """
        Generate a new CRL.
        """
        now = datetime.datetime.now(datetime.UTC)

        # Builder CRL
        builder = x509.CertificateRevocationListBuilder()
        builder = builder.last_update(self.ca.crl_last_generated if self.ca.crl_last_generated else datetime.datetime.fromtimestamp(0, datetime.timezone.utc))
        builder = builder.next_update(now + datetime.timedelta(days=7))

        for c in Certificate.select().where((Certificate.ca == self.ca) & (Certificate.is_revoked == True)):
            revoked_builder = x509.RevokedCertificateBuilder()
            revoked_builder = revoked_builder.serial_number(c.serial_as_int64)
            revoked_builder = revoked_builder.revocation_date(c.revoked_timestamp)

            if c.revoked_reason:
                revoked_reason = CertificateRevokedReason.from_string(c.revoked_reason)
                if revoked_reason != CertificateRevokedReason.UNSPECIFIED:
                    revoked_builder = revoked_builder.add_extension(
                        x509.CRLReason(
                            revoked_reason.to_reason_flags()
                        ),
                        critical=False,
                    )

            revoked_cert = revoked_builder.build()
            builder = builder.add_revoked_certificate(revoked_cert)

        if self.ca.crl_signing:
            try:
                crl_cert = x509.load_pem_x509_certificate(self.ca.crl_signing.cert.encode('utf8'), default_backend())
            except ValueError as e:
                sys.stderr.write(f'Invalid CRL certificate')
                exit(-1)

            if crl_cert.not_valid_after_utc <= now:
                sys.stderr.write(f'CRL expired')
                exit(-1)
            elif crl_cert.not_valid_after_utc < now + datetime.timedelta(days=30):
                print(f'WARNING: the CRL will expire in less than 30 days : '
                      f'{crl_cert.not_valid_after_utc.strftime("%d/%m/%Y %H:%M:%S %Z")}')

            crl_sign_private_key = get_private_key_from_pem(self.ca.crl_signing.key)
        else:
            crl_sign_private_key = self._get_ca_key()
            crl_cert = self.ca.cert_obj

        builder = builder.issuer_name(crl_cert.subject)

        # Sign the CRL
        crl = builder.sign(private_key=crl_sign_private_key, algorithm=hashes.SHA256())

        # CRL as PEM
        with open(self.ca.crl_output_filename, "wb") as f:
            f.write(crl.public_bytes(serialization.Encoding.PEM))

        # Mise à jour du timestamp
        self.ca.crl_last_generated = now
        self.ca.save()

        print(f'CRL successfully generated at "{self.ca.crl_output_filename}"')

        if self.ca.crl_post_script_path:
            print(f'Running CRL post-script "{self.ca.crl_post_script_path}"...')
            subprocess.run([self.ca.crl_post_script_path])

    def add_external(self, pem_filepath: Optional[str] = None) -> None:
        """
        Add a certificate that have been generated by this CA but not with this tool

        If the filepath is not provided, the content is read from stdin.

        :param pem_filepath: the Certificate in PEM format (optional)
        """

        if pem_filepath:
            if not os.path.exists(pem_filepath):
                sys.stderr.write(f'The file "{pem_filepath}" doesn\'t exist\n')
                exit(-1)

            with open(pem_filepath, 'rb') as f:
                pem_content = f.read()
        else:
            pem_content = ask_pem_format('Paste your certificate in PEM format', PEMFormatType.CERT).encode('utf8')

        try:
            cert = x509.load_pem_x509_certificate(pem_content, default_backend())
        except ValueError:
            sys.stderr.write(f'Invalid PEM CSR')
            exit(-1)

        if not verify_signature(cert, self.ca.cert_obj):
            sys.stderr.write(f'This certificate is not signed by the CA')
            exit(-1)

        cn = get_cn(cert)
        san = get_san(cert)
        sn = format_serial_number(cert)

        print('You\'re going to add the following certificate to the vault :')
        print(f'\tCommon Name : {cn}')
        print(f'\tSubject Alternative Name : {san if san else "*** not defined ***"}\n')

        if not confirm('Do you want to continue'):
            print('*** aborted ***')
            exit(0)

        if Certificate.select().where((Certificate.ca == self.ca) & (Certificate.serial == sn)).count() != 0:
            sys.stderr.write(f'The serial number "{sn}" already exists\n')
            exit(-1)

        c = Certificate.create(ca=self.ca,
                               cn=cn,
                               san=san,
                               created_timestamp=cert.not_valid_before_utc,
                               not_after=cert.not_valid_after_utc,
                               serial=sn,
                               cert=pem_content,
                               key=None,
                               is_revoked=False,
                               is_renewed=False,
        )
        c.save()

        print('Certificate added successfully')


    def _export(self, certificate: Certificate, output_format: str, out_path: Optional[str],
                p12_passphrase: Optional[str] = None):
        """
        Export the certificate and its private key if available.

        If the output_format is "pem", the data is exported to a file if the out_path is provided (the file extension
        .pem is added for the certificate and .key for the key). If no out_path is provided, the data is printed to
        stdout.

        If the output_format is "p12", the data is exported to the out_path. If the out_path doesn't have the ".p12"
        extension, this method add the extension. The p12_passphrase must be provided.

        :param certificate: the certificate
        :param output_format: the output format : "pem" or "p12"
        :param out_path: the output path
        :param p12_passphrase: the P12 passphrase
        """
        output_format = output_format.lower()
        if output_format not in ('pem', 'p12'):
            raise ValueError(f'Output format "{output_format}" not supported')

        if output_format == 'p12' and not out_path:
            out_path = certificate.cn

        certificate.load_cert()

        if certificate.key:
            certificate.load_key()

        if output_format == 'pem':
            if out_path:
                out_path_cert = out_path + '.pem'
                out_path_key = out_path + '.key'

                if os.path.exists(out_path_cert):
                    raise RuntimeError(f'The output certificate file "{out_path_cert}" already exists')

                if certificate.key:
                    if os.path.exists(out_path_key):
                        raise RuntimeError(f'The output private key file "{out_path_key}" already exists')

                write_cert_pem(certificate.cert_obj, out_path_cert)

                if certificate.key:
                    write_private_key_pem(certificate.key_obj, out_path_key)

                if certificate.key:
                    print(f'The certificate and its private key have been exported to {out_path}[.pem|.key]')
                else:
                    print(f'The certificate has been exported to {out_path}.pem. There is no private key linked.')
            else:
                print(certificate.cert)

                if certificate.key:
                    print(certificate.key)
                else:
                    print('There is no private key linked.')
        else:
            if not out_path.endswith('.p12'):
                out_path += '.p12'

            write_p12(out_path, p12_passphrase, certificate.cn, certificate.cert_obj, certificate.key_obj)

            if certificate.key:
                print(f'The certificate and its private key have been exported to {out_path}')
            else:
                print(f'The certificate has been exported to {out_path}. There is no private key linked.')

        certificate.clear_key()

    def _get_ca_key(self) -> PrivateKeyTypes:
        """
        Get the CA private key. If the key is passphrase protected, the user is prompted to enter it.
        After the key is retrieved, the CA key object is cleared from the self.ca.

        :return: the CA private key
        """
        self.ca.load_key()
        ca_key = self.ca.key_obj
        self.ca.clear_key()

        return ca_key

    def _get_config(self, config_name: str):
        """
        Get the value from a config parameter.

        The value is casted to the right type depending of the config parameter type in the vault.

        :param config_name: the config name
        :return: the value in int, string or bytes
        """
        c = Config.get_by_id(config_name)
        if not c:
            raise RuntimeError(f'The config name "{config_name}" is unknown')

        if c.type == ConfigType.INT:
            return int(c.value)
        elif c.type == ConfigType.STRING:
            return c.value
        elif c.type == ConfigType.BINARY:
            return base64.b64decode(c.value)
        elif c.type == ConfigType.EPOCH:
            return datetime.datetime.fromtimestamp(int(c.value))
        else:
            raise NotImplementedError(f'Config type "{c.type}" not implemented')

    def _set_config(self,  config_name: str, value):
        """
        Set the value of a config parameter.
        """

        c = Config.get_by_id(config_name)
        if not c:
            raise RuntimeError(f'The config name "{config_name}" is unknown')

        if c.type == ConfigType.INT:
            value = int(c.value)
        elif c.type == ConfigType.STRING:
            value = value
        elif c.type == ConfigType.BINARY:
            value = base64.b64encode(value)
        elif c.type == ConfigType.EPOCH:
            value = int(value.timestamp())
        else:
            raise NotImplementedError(f'Config type "{c.type}" not implemented')

        c.value = value
        c.save()

    @database.connection_context()
    def select_certificate(self, search_term: str, show_all_if_no_match: bool = False) -> Optional[Certificate]:
        """
        Select a certificate by specifying a search term or by giving the certificate ID.

        :param search_term: CN part or ID
        :param show_all_if_no_match: show all certificate if no match
        :return: the certificate
        """
        if re.match('^[0-9]+$', search_term):
            certificate = Certificate.get_by_id(int(search_term))
        else:
            now = datetime.datetime.now()
            certificates = Certificate.\
                select().where((Certificate.ca == self.ca) &
                               (Certificate.cn.contains(search_term)) & (Certificate.is_renewed == False) &
                               ((Certificate.is_revoked == False) & (Certificate.not_after >= now)))

            if certificates.count() == 1:
                certificate = certificates[0]
            else:
                if certificates.count() == 0:
                    print('No certificate found for this search !')

                    if not show_all_if_no_match:
                        return None

                    print('\nListing all certificates :')

                    certificates = Certificate.select().where((Certificate.ca == self.ca) &
                                                              (Certificate.is_renewed == False) &
                                                              (Certificate.not_after > datetime.datetime.now()) &
                                                              (Certificate.is_revoked == False))
                else:
                    print(f'{certificates.count()} certificates found :')

                valid_ids = []
                for c in certificates:
                    valid_ids.append(c.id)
                    print(str(c))

                print('')
                target_certificate = ask('Please enter the ID of one of these certificates', values=valid_ids)
                certificate = Certificate.get_by_id(int(target_certificate))

        return certificate

    @database.connection_context()
    def _sign_csr(self, csr: x509.CertificateSigningRequest, overwrite_hash_algo: HashAlgo = None,
                  overwrite_cn: Optional[str] = None, overwrite_san: Optional[x509.SubjectAlternativeName] = None,
                  overwrite_expire: datetime.datetime = None, use_crl_if_available: bool = True,
                  use_ocsp_if_available: bool = True, ask_confirm: bool = False,
                  skip_cert_existence_check: bool = False) -> tuple[x509.Certificate, Certificate]:
        """
        Sign the Certificate Signing Request with the Certificate Authority.

        The overwrite_hash_algo parameter can be used to overwrite the default hash algorithm.
        The overwrite_cn parameter can be used to overwrite the Common Name in the CSR.
        The overwrite_san parameter can be used to overwrite the Subject Alternative Name in the CSR.
        The overwrite_expire parameter can be used to overwrite the expiration date (must be in the future).

        The SAN must always include an entry matching the CN. If the CSR doesn't contain a SAN, this method create it.

        A unique (and non already used) serial number is assigned to the certificate. The certificate is valid for time
        configured in the Config<default_validity_seconds>.

        This method save the certificate in the vault. Note that the private key is not saved because not known. The
        calling function must update the vault with the private key if needed.

        This method returns a tuple :
            * the certificate object
            * the certificate model instance

        :param csr: the Certificate Signing Request
        :param overwrite_hash_algo: the optional hash algorithm
        :param overwrite_cn: the optional Command Name that must be used
        :param overwrite_san: the optional Subject Alternative Name that must be used
        :param overwrite_expire: the optional expired date
        :param use_crl_if_available: use the CRL URL if available for this CA
        :param use_ocsp_if_available: use the OCSP URL if available for this CA
        :param ask_confirm: the optional flag to print the CSR and ask the confirmation before continuing
        :param skip_cert_existence_check: skip the certificate existing check
        :return: (the OpenSSL certificate object, the Certificate model instance)
        """
        final_cn = overwrite_cn if overwrite_cn else get_cn(csr)
        if not regex_domain.match(final_cn):
            raise ValueError(f'CN "{final_cn}" is invalid')

        final_san = validate_or_build_san(final_cn, overwrite_san if overwrite_san else get_san(csr))

        hash_algo = overwrite_hash_algo if overwrite_hash_algo else HashAlgo.from_string(self._get_config('default_hash_algo'))

        if overwrite_expire:
            if overwrite_expire < datetime.datetime.now(datetime.timezone.utc):
                raise ValueError(f'The expire date is not in the future')

            not_after = overwrite_expire
        else:
            not_after = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=self._get_config("default_validity_seconds"))

        if not skip_cert_existence_check:
            # Check if a certificate with the same CN already exists
            c = Certificate.select().where((Certificate.ca == self.ca) &
                                           (Certificate.cn == final_cn) &
                                           (Certificate.is_renewed == False) &
                                           (Certificate.not_after > datetime.datetime.now()) &
                                           (Certificate.is_revoked == False))

            assert c.count() < 2, 'Critical error : there is more that one actual certificate matching this CN'

            if c.count() == 1:
                raise RuntimeError(f'The following certificate is matching this CN and it\'s not expired, revoked or '
                                   f'renewed : {c[0]}')

        # Generate unique serial number
        is_serial_validated = False
        serial_number_float64 = None
        serial_number_hex = None
        while not is_serial_validated:
            serial_number_float64 = generate_random_serial_number()
            serial_number_hex = serial_number_float64.to_bytes(8, 'big').hex(':')

            # We ensure that the random serial number is not already used
            is_serial_validated = Certificate.select().where((Certificate.ca == self.ca) &
                                                             (Certificate.serial == serial_number_hex)).count() == 0

        now = datetime.datetime.now(datetime.timezone.utc)

        # Generate the final certificate
        builder = (
            x509.CertificateBuilder()
            .serial_number(serial_number_float64)
            .subject_name(
                x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, final_cn)])
            )
            .issuer_name(self.ca.cert_obj.subject)
            .public_key(csr.public_key())
            .not_valid_before(now)
            .not_valid_after(not_after)
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
                critical=False
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(
                    self.ca.cert_obj.public_key()
                ),
                critical=False
            ).add_extension(
                final_san,
                critical=False
            )
        )

        if use_crl_if_available and self.ca.crl_url:
            crl_dp = x509.CRLDistributionPoints([
                x509.DistributionPoint(
                    full_name=[x509.UniformResourceIdentifier(self.ca.crl_url)],
                    relative_name=None,
                    reasons=None,
                    crl_issuer=None,
                ),
            ])

            builder = builder.add_extension(crl_dp, critical=False)

        if use_ocsp_if_available and self.ca.ocsp_url:
            aia = x509.AuthorityInformationAccess([
                x509.AccessDescription(
                    AuthorityInformationAccessOID.OCSP, x509.UniformResourceIdentifier(self.ca.ocsp_url),
                ),
            ])

            builder = builder.add_extension(aia, critical=False)

        if ask_confirm:
            print('You are about to sign the following certificate :\n')
            print_tabulated(get_cert_builder_text(builder))

            print('')

            if not confirm('Do you want to sign it'):
                exit(0)

        cert = builder.sign( private_key=self._get_ca_key(), algorithm=hash_algo.value)

        # Persist
        c = Certificate.create(
            ca=self.ca,
            cn=final_cn,
            san=get_san_str(final_san),
            created_timestamp=now.replace(microsecond=0),
            not_after=not_after.replace(microsecond=0),
            serial=serial_number_hex,
            cert=get_cert_pem(cert),
            key=None,
            is_revoked=False,
            is_renewed=False,
        )

        return cert, c

    @database.connection_context()
    def _generate_signed_cert(self, cn: str, san: x509.SubjectAlternativeName,  key: PrivateKeyTypes,
                              hash_algo: HashAlgo, not_after: datetime.datetime, use_crl_if_available: bool,
                              use_ocsp_if_available: bool, skip_cert_existence_check: bool = False) -> tuple[x509.Certificate, Certificate]:
        """
        Generate a Certificate and sign it with the Certificate Authority.

        The cn parameter is the Common Name. See Utils.regex_domain for valid values.

        If the key is provided, the key is used. If not, key_size must be defined.

        If the CSR doesn't contain a SAN, this method create it. If the SAN doesn't contain the CN, it will be added.

        A unique (and non already used) serial number is assigned to the certificate. The certificate is valid for time
        configured in the Config<default_validity_seconds>.

        This method save the certificate in the vault.

        This method returns a tuple :
            * the certificate object
            * the certificate model instance

        :param cn: the Common Name
        :param san: the optional Subject Alternative Name
        :param key: the optional private key. Cannot be used in conjunction with key_size
        :param hash_algo: the optional hash algorithm
        :param not_after: the expiration date of the certification
        :param use_crl_if_available: use the CRL URL if available
        :param use_ocsp_if_available: use the OCSP URL if available
        :param skip_cert_existence_check: skip the certificate existing check
        :return: (the OpenSSL certificate object, the Certificate model instance)
        """
        if not regex_domain.match(cn):
            raise ValueError(f'CN "{cn}" is invalid')

        # Generate CSR
        # The expiration date and SAN are set by _sign_csr()
        builder = x509.CertificateSigningRequestBuilder()
        builder = builder.subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, cn)
            ])
        )
        csr = builder.sign(private_key=key, algorithm=hashes.SHA256())

        # Sign the CSR
        signed_cert, vault_certificate = self._sign_csr(csr,
                                                        overwrite_hash_algo=hash_algo,
                                                        overwrite_expire=not_after,
                                                        overwrite_san=san,
                                                        use_crl_if_available=use_crl_if_available,
                                                        use_ocsp_if_available=use_ocsp_if_available,
                                                        ask_confirm=True,
                                                        skip_cert_existence_check=skip_cert_existence_check)

        # Save the private key into the vault
        vault_certificate.key = get_private_key_pem(key)
        vault_certificate.save()

        return signed_cert, vault_certificate

