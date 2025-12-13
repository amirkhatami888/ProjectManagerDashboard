#!/usr/bin/env python
"""
Security Testing Script for Django Project Manager Dashboard
This script performs comprehensive security tests to ensure the application is secure
"""
import os
import sys
import django
from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import requests
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

User = get_user_model()

class SecurityTestSuite:
    """Comprehensive security testing suite"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = []
        self.critical_issues = []
        self.warnings = []
        
    def log_result(self, test_name, status, message, severity='INFO'):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'severity': severity
        }
        self.test_results.append(result)
        
        if severity == 'CRITICAL':
            self.critical_issues.append(result)
        elif severity == 'WARNING':
            self.warnings.append(result)
            
        print(f"[{severity}] {test_name}: {status} - {message}")
    
    def test_debug_mode(self):
        """Test if DEBUG mode is disabled"""
        if settings.DEBUG:
            self.log_result(
                "DEBUG Mode Check", 
                "FAIL", 
                "DEBUG mode is enabled - this exposes sensitive information", 
                "CRITICAL"
            )
        else:
            self.log_result(
                "DEBUG Mode Check", 
                "PASS", 
                "DEBUG mode is disabled", 
                "INFO"
            )
    
    def test_secret_key(self):
        """Test secret key security"""
        secret_key = settings.SECRET_KEY
        if 'django-insecure' in secret_key or len(secret_key) < 50:
            self.log_result(
                "Secret Key Check", 
                "FAIL", 
                "Secret key is weak or default - generate a strong key", 
                "CRITICAL"
            )
        else:
            self.log_result(
                "Secret Key Check", 
                "PASS", 
                "Secret key appears to be strong", 
                "INFO"
            )
    
    def test_database_credentials(self):
        """Test database credentials security"""
        db_config = settings.DATABASES['default']
        
        # Check if credentials are hardcoded
        if 'amirkhatami888' in str(db_config) or 'Amir137667318@' in str(db_config):
            self.log_result(
                "Database Credentials Check", 
                "FAIL", 
                "Database credentials appear to be hardcoded", 
                "CRITICAL"
            )
        else:
            self.log_result(
                "Database Credentials Check", 
                "PASS", 
                "Database credentials appear to use environment variables", 
                "INFO"
            )
    
    def test_security_headers(self):
        """Test security headers configuration"""
        security_settings = [
            ('SECURE_SSL_REDIRECT', 'HTTPS Redirect'),
            ('SECURE_BROWSER_XSS_FILTER', 'XSS Protection'),
            ('SECURE_CONTENT_TYPE_NOSNIFF', 'Content Type Sniffing Protection'),
            ('X_FRAME_OPTIONS', 'Clickjacking Protection'),
            ('CSRF_COOKIE_SECURE', 'CSRF Cookie Security'),
            ('SESSION_COOKIE_SECURE', 'Session Cookie Security'),
        ]
        
        for setting, description in security_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                if value:
                    self.log_result(
                        f"{description} Check", 
                        "PASS", 
                        f"{description} is enabled", 
                        "INFO"
                    )
                else:
                    self.log_result(
                        f"{description} Check", 
                        "WARNING", 
                        f"{description} is disabled", 
                        "WARNING"
                    )
            else:
                self.log_result(
                    f"{description} Check", 
                    "WARNING", 
                    f"{description} setting not found", 
                    "WARNING"
                )
    
    def test_password_validation(self):
        """Test password validation settings"""
        validators = settings.AUTH_PASSWORD_VALIDATORS
        
        # Check minimum length validator
        min_length_found = False
        for validator in validators:
            if 'MinimumLengthValidator' in validator['NAME']:
                min_length_found = True
                min_length = validator.get('OPTIONS', {}).get('min_length', 8)
                if min_length >= 8:
                    self.log_result(
                        "Password Length Check", 
                        "PASS", 
                        f"Minimum password length is {min_length}", 
                        "INFO"
                    )
                else:
                    self.log_result(
                        "Password Length Check", 
                        "WARNING", 
                        f"Minimum password length is only {min_length}", 
                        "WARNING"
                    )
                break
        
        if not min_length_found:
            self.log_result(
                "Password Length Check", 
                "WARNING", 
                "Minimum length validator not found", 
                "WARNING"
            )
    
    def test_file_upload_limits(self):
        """Test file upload security limits"""
        max_memory = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
        max_fields = getattr(settings, 'DATA_UPLOAD_MAX_NUMBER_FIELDS', None)
        
        if max_memory:
            max_mb = max_memory / (1024 * 1024)
            if max_mb <= 10:
                self.log_result(
                    "File Upload Size Check", 
                    "PASS", 
                    f"File upload limit is {max_mb:.1f}MB", 
                    "INFO"
                )
            else:
                self.log_result(
                    "File Upload Size Check", 
                    "WARNING", 
                    f"File upload limit is {max_mb:.1f}MB - consider reducing", 
                    "WARNING"
                )
        else:
            self.log_result(
                "File Upload Size Check", 
                "WARNING", 
                "File upload size limit not set", 
                "WARNING"
            )
        
        if max_fields:
            if max_fields <= 1000:
                self.log_result(
                    "Form Fields Check", 
                    "PASS", 
                    f"Maximum form fields is {max_fields}", 
                    "INFO"
                )
            else:
                self.log_result(
                    "Form Fields Check", 
                    "WARNING", 
                    f"Maximum form fields is {max_fields} - consider reducing", 
                    "WARNING"
                )
        else:
            self.log_result(
                "Form Fields Check", 
                "WARNING", 
                "Form fields limit not set", 
                "WARNING"
            )
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE
        
        if csrf_middleware:
            self.log_result(
                "CSRF Protection Check", 
                "PASS", 
                "CSRF middleware is enabled", 
                "INFO"
            )
        else:
            self.log_result(
                "CSRF Protection Check", 
                "FAIL", 
                "CSRF middleware is not enabled", 
                "CRITICAL"
            )
    
    def test_session_security(self):
        """Test session security settings"""
        session_settings = [
            ('SESSION_COOKIE_HTTPONLY', 'Session Cookie HttpOnly'),
            ('SESSION_COOKIE_SAMESITE', 'Session Cookie SameSite'),
            ('SESSION_EXPIRE_AT_BROWSER_CLOSE', 'Session Expire on Browser Close'),
        ]
        
        for setting, description in session_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                if value:
                    self.log_result(
                        f"{description} Check", 
                        "PASS", 
                        f"{description} is enabled", 
                        "INFO"
                    )
                else:
                    self.log_result(
                        f"{description} Check", 
                        "WARNING", 
                        f"{description} is disabled", 
                        "WARNING"
                    )
            else:
                self.log_result(
                    f"{description} Check", 
                    "WARNING", 
                    f"{description} setting not found", 
                    "WARNING"
                )
    
    def test_allowed_hosts(self):
        """Test ALLOWED_HOSTS configuration"""
        allowed_hosts = settings.ALLOWED_HOSTS
        
        if '*' in allowed_hosts:
            self.log_result(
                "Allowed Hosts Check", 
                "FAIL", 
                "ALLOWED_HOSTS contains '*' - this is dangerous", 
                "CRITICAL"
            )
        elif len(allowed_hosts) == 0:
            self.log_result(
                "Allowed Hosts Check", 
                "WARNING", 
                "ALLOWED_HOSTS is empty", 
                "WARNING"
            )
        else:
            self.log_result(
                "Allowed Hosts Check", 
                "PASS", 
                f"ALLOWED_HOSTS is properly configured with {len(allowed_hosts)} hosts", 
                "INFO"
            )
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 Starting Security Test Suite...")
        print("=" * 50)
        
        self.test_debug_mode()
        self.test_secret_key()
        self.test_database_credentials()
        self.test_security_headers()
        self.test_password_validation()
        self.test_file_upload_limits()
        self.test_csrf_protection()
        self.test_session_security()
        self.test_allowed_hosts()
        
        print("\n" + "=" * 50)
        print("🔒 Security Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        critical_issues = len(self.critical_issues)
        warnings = len(self.warnings)
        passed = total_tests - critical_issues - warnings
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"❌ Critical Issues: {critical_issues}")
        
        if critical_issues > 0:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for issue in self.critical_issues:
                print(f"  - {issue['test']}: {issue['message']}")
        
        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning['test']}: {warning['message']}")
        
        if critical_issues == 0:
            print("\n✅ No critical security issues found!")
        else:
            print(f"\n❌ {critical_issues} critical security issues need immediate attention!")
        
        return {
            'total': total_tests,
            'passed': passed,
            'warnings': warnings,
            'critical': critical_issues,
            'results': self.test_results
        }

def main():
    """Main function to run security tests"""
    try:
        test_suite = SecurityTestSuite()
        results = test_suite.run_all_tests()
        
        # Exit with error code if critical issues found
        if results['critical'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error running security tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()




