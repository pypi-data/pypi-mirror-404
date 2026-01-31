"""
SSL Certificate Manager for XPyCode Addin Server.

Generates self-signed certificates using the cryptography package
and installs the CA in Windows trust store.
"""

import os
import sys
import subprocess
import ipaddress
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import NamedTuple, Optional

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class CertificatePaths(NamedTuple):
    """Paths to certificate files."""
    ca_cert: Path
    ca_key: Path
    server_cert: Path
    server_key: Path

class CertificateManager:
    """
    Manages SSL certificates for the addin server.
    
    - Generates CA and server certificates if they don't exist
    - Regenerates if expired
    - Installs CA in Windows trust store
    """
    
    DEFAULT_CERT_DIR = Path.home() / ".xpycode" / "certs"
    CA_CERT_NAME = "xpycode-ca.crt"
    CA_KEY_NAME = "xpycode-ca.key"
    SERVER_CERT_NAME = "localhost.crt"
    SERVER_KEY_NAME = "localhost.key"
    
    # Certificate validity period (10 years)
    VALIDITY_DAYS = 3650
    
    # Regenerate if less than this many days until expiration
    RENEWAL_THRESHOLD_DAYS = 30
    
    def __init__(self, cert_dir: Optional[Path] = None):
        """
        Initialize the certificate manager.
        
        Args:
            cert_dir: Directory to store certificates. Defaults to ~/.xpycode_certs/
        """
        self.cert_dir = cert_dir or self.DEFAULT_CERT_DIR
        self.cert_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def paths(self) -> CertificatePaths:
        """Get paths to all certificate files."""
        return CertificatePaths(
            ca_cert=self.cert_dir / self.CA_CERT_NAME,
            ca_key=self.cert_dir / self.CA_KEY_NAME,
            server_cert=self.cert_dir / self.SERVER_CERT_NAME,
            server_key=self.cert_dir / self.SERVER_KEY_NAME,
        )
    
    def ensure_certificates(self) -> CertificatePaths:
        """
        Ensure valid certificates exist, generating if necessary.
        
        Returns:
            CertificatePaths with paths to all certificate files.
        """
        paths = self.paths
        
        # Check if CA is registered but files are missing
        # This handles the case where user deleted .xpycode folder
        if self._is_ca_trusted() and not self._all_files_exist(paths):
            print("Certificate files missing but CA is still registered in trust store.")
            print("Unregistering old CA before generating new certificates...")
            self._unregister_ca()
        
        # Check if certificates need to be generated or regenerated
        if self._needs_generation(paths):
            self._generate_certificates(paths)
        
        # Ensure CA is trusted (Won't do anything on linux)
        self._ensure_ca_trusted(paths.ca_cert)
        
        return paths
    
    def _all_files_exist(self, paths: CertificatePaths) -> bool:
        """Check if all certificate files exist."""
        for path in paths:
            if not path.exists():
                return False
        return True
    
    def _needs_generation(self, paths: CertificatePaths) -> bool:
        """Check if certificates need to be generated or regenerated."""
        # Check if all files exist
        if not self._all_files_exist(paths):
            return True
        
        # Check if server certificate is expired or expiring soon
        try:
            cert_data = paths.server_cert.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check expiration
            # Note: Certificates store times as naive UTC datetimes
            expires = cert.not_valid_after_utc
            now = datetime. now(timezone.utc)
            days_until_expiry = (expires - now).days
            
            if days_until_expiry < self.RENEWAL_THRESHOLD_DAYS:
                return True
                
        except Exception:
            return True
        
        return False
    
    def _generate_certificates(self, paths: CertificatePaths) -> None:
        """Generate CA and server certificates."""
        print("Generating SSL certificates for XPyCode Addin Server...")
        
        # Generate CA
        ca_key, ca_cert = self._generate_ca()
        
        # Generate server certificate signed by CA
        server_key, server_cert = self._generate_server_cert(ca_key, ca_cert)
        
        # Save all certificates
        self._save_key(ca_key, paths.ca_key)
        self._save_cert(ca_cert, paths.ca_cert)
        self._save_key(server_key, paths.server_key)
        self._save_cert(server_cert, paths.server_cert)
        
        print(f"Certificates saved to: {self.cert_dir}")
    
    def _generate_ca(self):
        """Generate a Certificate Authority."""
        # Generate CA private key
        ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "XPyCode Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "XPyCode Development CA"),
        ])
        
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc).replace(tzinfo=None))
            .not_valid_after(datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=self.VALIDITY_DAYS))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256())
        )
        
        return ca_key, ca_cert
    
    def _generate_server_cert(self, ca_key, ca_cert):
        """Generate a server certificate signed by the CA."""
        # Generate server private key
        server_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate server certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "XPyCode Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        server_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc).replace(tzinfo=None))
            .not_valid_after(datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=self.VALIDITY_DAYS))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )
        
        return server_key, server_cert
    
    def _save_key(self, key, path: Path) -> None:
        """Save a private key to a file."""
        path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    
    def _save_cert(self, cert, path: Path) -> None:
        """Save a certificate to a file."""
        path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    
    def _ensure_ca_trusted(self, ca_cert_path: Path) -> None:
        """
        Ensure the CA certificate is trusted in Windows certificate store.
        Uses certutil to add to the current user's trusted root store.
        """
        # Check if already trusted
        if self._is_ca_trusted():
            return
        
        print("Installing CA certificate in Windows trust store...")
        print("(You may see a security prompt - please accept it)")
        
        try:
            # Add to current user's trusted root store
            result=None
            if sys.platform == 'win32': 
                # Windows:  certutil
                result = subprocess.run(
                   ["certutil", "-user", "-addstore", "Root", str(ca_cert_path)],
                   capture_output=True,
                   text=True,
                   )
            elif sys.platform == 'darwin':
                # macOS: security command
                result = subprocess.run(
                    ["security", "add-trusted-cert", "-r", "trustRoot", 
                               "-k", os.path.expanduser("~/Library/Keychains/login.keychain-db"),
                               str(ca_cert_path)],
                    capture_output=True,
                    text=True,
                )
            else:
                # Linux: print instructions (too many distro variations)
                print(f"Please manually trust the CA certificate:  {ca_cert_path}")
            if result:
                if result.returncode == 0:
                    print("CA certificate installed successfully.")
                else:
                    print(f"Warning: Could not install CA certificate: {result.stderr}")
                    print("You may need to manually trust the certificate.")
                    print(f"Certificate location: {ca_cert_path}")
                
        except FileNotFoundError:
            print("Warning: certutil not found. Please manually install the CA certificate.")
            print(f"Certificate location: {ca_cert_path}")
    
    def _unregister_ca(self) -> None:
        """
        Remove the CA certificate from the system trust store.
        
        This is used when certificate files are deleted but CA is still trusted,
        to clean up the old CA before generating new certificates.
        """
        print("Removing old CA certificate from trust store...")
        
        try:
            result = None
            if sys.platform == 'win32':
                # Windows: remove using certutil
                result = subprocess.run(
                    ["certutil", "-user", "-delstore", "Root", "XPyCode Development CA"],
                    capture_output=True,
                    text=True,
                )
            elif sys.platform == 'darwin':
                # macOS: remove using security delete-certificate
                result = subprocess.run(
                    ["security", "delete-certificate", "-c", "XPyCode Development CA",
                     os.path.expanduser("~/Library/Keychains/login.keychain-db")],
                    capture_output=True,
                    text=True,
                )
            else:
                # Linux: print instructions (manual process)
                print("Please manually remove the 'XPyCode Development CA' certificate from your system trust store.")
                return
            
            if result:
                if result.returncode == 0:
                    print("Old CA certificate removed successfully.")
                else:
                    print(f"Warning: Could not remove old CA certificate: {result.stderr}")
                    print("You may need to manually remove the certificate from your trust store.")
        
        except FileNotFoundError:
            print("Warning: Certificate management tool not found.")
            print("Please manually remove 'XPyCode Development CA' from your trust store.")
        except Exception as e:
            print(f"Warning: Error removing CA certificate: {e}")
            print("Please manually remove 'XPyCode Development CA' from your trust store.")
    
    def _is_ca_trusted(self) -> bool:
        """Check if the XPyCode CA is already in the trusted store."""
        try:
            if sys.platform == 'win32':
                # Windows: check using certutil
                result = subprocess.run(
                    ["certutil", "-user", "-store", "Root"],
                    capture_output=True,
                    text=True,
                )
                return "XPyCode Development CA" in result.stdout
            elif sys.platform == 'darwin':
                # macOS: check using security find-certificate
                result = subprocess.run(
                    ["security", "find-certificate", "-c", "XPyCode Development CA",
                     os.path.expanduser("~/Library/Keychains/login.keychain-db")],
                    capture_output=True,
                    text=True,
                )
                return result.returncode == 0
        except Exception:
            return False
        return False
