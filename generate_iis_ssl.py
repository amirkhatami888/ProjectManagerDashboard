#!/usr/bin/env python
"""
Generate SSL certificates suitable for IIS deployment
"""
import os
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

def create_iis_ssl_certificates():
    """Create SSL certificates suitable for IIS"""
    
    # Create ssl directory
    ssl_dir = Path("ssl")
    ssl_dir.mkdir(exist_ok=True)
    
    cert_file = ssl_dir / "iis_cert.pem"
    key_file = ssl_dir / "iis_key.pem"
    pfx_file = ssl_dir / "iis_cert.pfx"
    
    print("🔐 Creating SSL certificates for IIS deployment...")
    
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
        
        # Create certificate with IIS-friendly subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tehran"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Tehran"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ProjectManager"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "IT Department"),
            x509.NameAttribute(NameOID.COMMON_NAME, "projecthelal.rcs.ir"),
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
                x509.DNSName("projecthelal.rcs.ir"),
                x509.DNSName("www.projecthelal.rcs.ir"),
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"✅ Certificate saved: {cert_file}")
        
        # Create PFX file for IIS
        from cryptography.hazmat.primitives.serialization import pkcs12
        
        pfx_data = pkcs12.serialize_key_and_certificates(
            name=b"iis_cert",
            key=private_key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(pfx_file, "wb") as f:
            f.write(pfx_data)
        print(f"✅ PFX certificate saved: {pfx_file}")
        
        print("\n🎉 IIS SSL certificates created successfully!")
        print(f"Certificate (PEM): {cert_file}")
        print(f"Private Key (PEM): {key_file}")
        print(f"PFX Certificate: {pfx_file}")
        
        print("\n📝 IIS Setup Instructions:")
        print("1. Open IIS Manager")
        print("2. Go to Server Certificates")
        print("3. Import Certificate")
        print(f"4. Select: {pfx_file}")
        print("5. Set password (if prompted)")
        print("6. Bind certificate to your site on port 443")
        
        return True
        
    except ImportError:
        print("❌ cryptography library not found.")
        print("Install it with: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Error creating certificates: {e}")
        return False

if __name__ == "__main__":
    create_iis_ssl_certificates()
