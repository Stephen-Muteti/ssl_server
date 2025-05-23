# SSL SETUP

## Purpose

This guide documents the steps to set up mutual TLS (mTLS) between the client and server to ensure both ends of the connection are authenticated and encrypted. This protects your system against impersonation by malicious actors posing as clients or servers.


## Directory Structure
algorithmic_sciences_task
├── certs
   ├── server_openssl.cnf
   ├── client_openssl.cnf
   ├── server.key
   ├── server.crt
   ├── client.key
   ├── client.crt
   └── ca.pem


## Certificate Generation Steps

1. Navigate to the `certs/` directory

```bash
cd certs
```

2. Ensure Configuration Files Exist

You will need two OpenSSL configuration files: one for the server and one for the client because the server needs to be connected to via a specific IP unlike the client.

**server_openssl.cnf**
```bash
[ req ]
default_bits       = 2048
default_md         = sha256
default_keyfile    = privkey.pem
distinguished_name = req_distinguished_name
x509_extensions    = v3_req
prompt             = no

[ req_distinguished_name ]
C  = KE
ST = Nairobi
L  = Nairobi
O  = Algorithmic Sciences
OU = Software Engineering
CN = localhost

[ v3_req ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = localhost
IP.1  = 127.0.0.1
```

**client_openssl.cnf**
```bash
[ req ]
default_bits       = 2048
default_md         = sha256
default_keyfile    = privkey.pem
distinguished_name = req_distinguished_name
x509_extensions    = v3_req
prompt             = no

[ req_distinguished_name ]
C  = KE
ST = Nairobi
L  = Nairobi
O  = Algorithmic Sciences
OU = Software Engineering
CN = client

[ v3_req ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = client
```

3. Generate Server Certificate and Key

Run the following command:
```bash
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -config server_openssl.cnf
```

The following files will be generated:

    > server.key: server private key

    > server.crt: self-signed server certificate

4. Generate Client Certificate & Key

Run the following command:

```bash
openssl req -x509 -newkey rsa:2048 -keyout client.key -out client.crt -days 365 -nodes -config client_openssl.cnf
```

The following files will be generated:

    > client.key: client private key

    > client.crt: self-signed client certificate

5. Create Certificate Authority Bundle

Concatenate both certificates to form a `ca.pem` file used for peer verification:

```bash
cat server.crt client.crt > ca.pem    # Linux/macOS
# or
type server.crt client.crt > ca.pem   # Windows
```

> `ca.pem`: combined trust store containing valid server and client certs is generated

These files are use for the mTLS for the server and client connection.

## Permissions

Ensure that the user `stephen_algorithmic_sciences` has read access to the certificate and key files.
For SSL Certificates and Private Keys restrict access strictly to the daemon user, preventing security risks.

```bash
sudo chmod 600 /opt/algorithmic_sciences_task/certs/server.key
sudo chmod 600 /opt/algorithmic_sciences_task/certs/client.key
```

## Author

Stephen Muteti
