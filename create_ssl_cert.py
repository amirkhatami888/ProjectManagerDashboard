#!/usr/bin/env python
"""
Create self-signed SSL certificates using Python cryptography library
"""
import os
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

def create_ssl_certificates():
    """Create self-signed SSL certificates"""
    
    # Create ssl directory
    ssl_dir = Path("ssl")
    ssl_dir.mkdir(exist_ok=True)
    
    cert_file = ssl_dir / "cert.pem"
    key_file = ssl_dir / "key.pem"
    
    print("🔐 Creating self-signed SSL certificates...")
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Save private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        print(f"✅ Private key saved: {key_file}")
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tehran"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Tehran"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ProjectManager"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"✅ Certificate saved: {cert_file}")
        
        print("\n🎉 SSL certificates created successfully!")
        print(f"Certificate: {cert_file}")
        print(f"Private Key: {key_file}")
        print("\n📝 To use with Django:")
        print("python manage.py runserver_plus --cert-file ssl/cert.pem --key-file ssl/key.pem")
        
    except ImportError:
        print("❌ cryptography library not found.")
        print("Install it with: pip install cryptography")
    except Exception as e:
        print(f"❌ Error creating certificates: {e}")

if __name__ == "__main__":
    create_ssl_certificates()
