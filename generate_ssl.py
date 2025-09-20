#!/usr/bin/env python
"""
Generate self-signed SSL certificates for Django development server
"""
import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_certificates():
    """Generate self-signed SSL certificates"""
    
    # Create ssl directory if it doesn't exist
    ssl_dir = Path("ssl")
    ssl_dir.mkdir(exist_ok=True)
    
    cert_file = ssl_dir / "cert.pem"
    key_file = ssl_dir / "key.pem"
    
    print("🔐 Generating self-signed SSL certificates...")
    
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_file), "2048"
        ], check=True)
        print(f"✅ Private key generated: {key_file}")
        
        # Generate certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(key_file), 
            "-out", str(cert_file), "-days", "365", "-subj",
            "/C=IR/ST=Tehran/L=Tehran/O=ProjectManager/OU=IT/CN=localhost"
        ], check=True)
        print(f"✅ Certificate generated: {cert_file}")
        
        print("\n🎉 SSL certificates generated successfully!")
        print(f"Certificate: {cert_file}")
        print(f"Private Key: {key_file}")
        print("\n📝 To use with Django:")
        print("python manage.py runserver_plus --cert-file ssl/cert.pem --key-file ssl/key.pem")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificates: {e}")
        print("Make sure OpenSSL is installed on your system.")
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL first.")
        print("On Windows, you can install it via:")
        print("1. Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("2. Or use Git Bash (comes with OpenSSL)")
        print("3. Or use WSL (Windows Subsystem for Linux)")

if __name__ == "__main__":
    generate_ssl_certificates()
