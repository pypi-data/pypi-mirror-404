"""Security utilities for Skyhook including auth and SSL certificate generation."""

import os
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic(auto_error=False)


class AuthManager:
    """Manages HTTP Basic Authentication."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username
        self.password = password
        self.enabled = username is not None and password is not None
    
    def verify_credentials(
        self, credentials: HTTPBasicCredentials = Depends(security)
    ) -> bool:
        """Verify HTTP Basic Auth credentials."""
        if not self.enabled:
          return True

        if credentials is None:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

        if not credentials.username or not credentials.password:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

        username_correct = secrets.compare_digest(
        credentials.username,
        self.username
    )
        password_correct = secrets.compare_digest(
        credentials.password,
        self.password
    )

        if not (username_correct and password_correct):
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

        return True



def sanitize_path(base_path: Path, requested_path: str) -> Path:
    """
    Sanitize and validate file paths to prevent directory traversal attacks.
    
    Args:
        base_path: The root directory being served
        requested_path: The requested file path from user input
    
    Returns:
        Validated absolute path
    
    Raises:
        HTTPException: If path traversal is detected
    """
    # Remove leading slashes and normalize
    requested_path = requested_path.lstrip("/")
    
    # Resolve the full path
    full_path = (base_path / requested_path).resolve()
    
    # Ensure the resolved path is within the base directory
    try:
        full_path.relative_to(base_path.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Path traversal attempt detected"
        )
    
    return full_path


def generate_self_signed_cert() -> Tuple[str, str]:
    """
    Generate a self-signed SSL certificate for HTTPS.
    
    Returns:
        Tuple of (cert_file_path, key_file_path)
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Skyhook"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    
    # Create temporary files for cert and key
    cert_fd, cert_path = tempfile.mkstemp(suffix=".crt", prefix="skyhook_")
    key_fd, key_path = tempfile.mkstemp(suffix=".key", prefix="skyhook_")
    
    # Write certificate
    with os.fdopen(cert_fd, "wb") as cert_file:
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Write private key
    with os.fdopen(key_fd, "wb") as key_file:
        key_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    
    return cert_path, key_path


def parse_auth_string(auth_string: str) -> Tuple[str, str]:
    """
    Parse authentication string in format 'username:password'.
    
    Args:
        auth_string: String in format 'user:pass'
    
    Returns:
        Tuple of (username, password)
    
    Raises:
        ValueError: If format is invalid
    """
    parts = auth_string.split(":", 1)
    if len(parts) != 2:
        raise ValueError(
            "Invalid auth format. Use 'username:password'"
        )
    
    username, password = parts
    if not username or not password:
        raise ValueError(
            "Username and password cannot be empty"
        )
    
    return username, password