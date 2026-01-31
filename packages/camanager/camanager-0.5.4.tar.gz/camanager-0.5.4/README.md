
CAManager stands for Certificate Authority Manager. This is a simple tool for managing a certification authority.

With this tool, you can :

- list and view the metadata of all your certificates
- generate a new certificate
- sign a Certificate Signing Request
- export a certificate in PEM or PCKS#12 format (.p12)
- renew a certificate
- make a backup or a restore of the CA vault
- generate a CRL

# Important remark

Please use a venv. This tool is updated without providing the code necessary to upgrade to the new version each time.

# Installation

    pip3 install camanager

# Recommendations for use

The tool was developed to meet a specific need. Here is how it is used:

- This script runs on a server with access restricted to administrators.
- A root CA has been generated and deployed on the clients. The private key is stored offline (not present on the server)
- A CRL Signing Certificate is generated whose sole purpose (and authorization) is to sign the CRL. The private key is 
not stored encrypted, which means that the CRL can be generated periodically without user input.
- You can use the `update_crl.sh` script to upload the update the `crl.pem` to a remote server (CRL/OCSP)

See ([the guide to create the CA](CREATE_CA_AND_INTERMDIATE.md)).

# Security

- If you generate a certificate with the tool, the private key is kept in the vault. However, this is not good 
practice: the correct way to do this is to generate a key and a CSR on the server and have the CSR signed by this tool.
- The vault is a SQLite3 DB, all private keys are encrypted with AES-256. The master key is encrypted with a derived 
password of the user (PBKDF2-SHA512) 
- Passwords are requested via secure input
- No network communication

# Initial setup for the first usage

This tool doesn't generate the Certificate Authority. You must already have one or generate a new one.

Once you have the Certificate Authority private and public keys, run `camanager setup`:

    $ python -m camanager setup
    Enter the password that will be used to encrypt the CA vault : [secure input, nothing will appear]
    Confirm it : [same]
    Paste your CA certificate in PEM format :
    [paste here]
    Paste your CA key in PEM format :
    [paste here]
    ...
    
The tool verifies that the keys match. If the private key is encrypted using a passphrase, you will be prompted for it.

The vault is saved in the `ca.db` file of the directory you are in. You must therefore run `camanager` each time 
from the same directory if you want to use the same vault.

# Usage

## Backup the vault

    python -m camanager backup


Create a copy of the `ca.db` into `ca.db.bak`.

## Restore a backup vault

    python -m camanager restore

Restore the `ca.db` from `ca.db.bak`.

Please note that certificates generated since the last backup will no longer be managed, which will cause security 
issues.

## Setup

    python -m camanager setup

Create the vault for the first time and add a CA.

## Add CA

    python -m camanager add-ca

Add another CA to the vault. You will be prompted if you want to use this CA as the default one.


## List certificates

    python -m camanager list [--ca ca_name] [--all | --soon-expired]

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing
- `--all` : show also the revoked/expired/renewed certificates
- `--soon-expired` : show only soon expired (less than 1 month) certificates

By default, show only active certificates.

## Generate a new certificate

    python -m camanager newcert [--ca ca_name] 

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing

Generate a new certificate. You will be able to use default algo / key size / validity period or specify your own. 
You will be prompted for the Common Name and Subject Alternative Names.

**Warning :** a certificate is normally generated on the server and a Certificate Signing Request is generated for 
the CA. It is not advisable to generate the certificate and its key from this tool. However, this behavior is copied 
from how easy-rsa works.

## Sign a CSR

    python -m camanager sign [--ca ca_name] [csr_file]

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing
- `csr_file` : the Certificate Signin Request file

Sign the CSR with the selected CA. You will be prompted if you want to override the Common Name / 
Subject Alternative Names / validity period.

If `csr_file` is not specified, the CSR will be requested on stdin.

## Export a certificate

    python -m camanager export [--ca ca_name] --pem|--p12 [--out output_file] [certificate CN or ID]

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing
- `--pem` or `--p12` : the output format
- `--out` : the output file
- `certificate CN or ID` : the Common Name or certificate ID that you want to export

Export the selected certificate in PEM or PCKS#12 format. 

## Revoke a certificate

    python -m camanager revoke [--ca ca_name] [certificate CN or ID]

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing
- `certificate CN or ID` : the Common Name or certificate ID that you want to export

Revoke the selected certificate. The CRL will be generated automatically. If a post-CRL update script is defined, 
it will be executed.

## Generate the CRL

    python -m camanager crl [--ca ca_name] 

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing
 
Generate the actual CRL. If a post-CRL update script is defined, it will be executed.

## Add a certificate generated externally to the vault

    python -m camanager add [--ca ca_name] [pem_file]

- `--ca` : specify the CA to use. If not provided, use the default CA or the only one existing
- `pem_fime` : the Certificate file

Add a certificate signed by the CA but generated off this tool.

If `csr_file` is not specified, the certificate will be requested on stdin.
