# IIS SSL Deployment Guide for Django Project Manager Dashboard

## 🔐 SSL Certificates Generated

The following SSL certificates have been created for IIS deployment:

- **PEM Certificate**: `ssl/iis_cert.pem`
- **Private Key**: `ssl/iis_key.pem` 
- **PFX Certificate**: `ssl/iis_cert.pfx` (for IIS import)

## 📋 IIS SSL Setup Steps

### 1. Import SSL Certificate to IIS

1. Open **IIS Manager**
2. Select your server in the left panel
3. Double-click **"Server Certificates"**
4. Click **"Import..."** in the right panel
5. Browse to `ssl/iis_cert.pfx`
6. Enter password (if prompted)
7. Click **"OK"**

### 2. Configure Website SSL Binding

1. In IIS Manager, expand **"Sites"**
2. Select your **"ProjectManagerDashboard"** website
3. Click **"Bindings..."** in the right panel
4. Click **"Add..."**
5. Configure:
   - **Type**: `https`
   - **Port**: `443`
   - **SSL Certificate**: Select the imported certificate
6. Click **"OK"**

### 3. Enable HTTPS Redirect

The `web.config` file has been updated with URL Rewrite rules to:
- Force HTTPS redirect for all HTTP traffic
- Handle static files properly
- Route Django requests correctly

### 4. Run Deployment Script

Execute the deployment script:
```batch
deploy_to_iis_ssl.bat
```

Or run PowerShell script (as Administrator):
```powershell
.\setup_iis_ssl.ps1
```

## 🔧 Manual Configuration

### IIS Manager Steps:
1. **Server Certificates** → Import `ssl/iis_cert.pfx`
2. **Sites** → Your Site → **Bindings** → Add HTTPS binding
3. **URL Rewrite** → Verify rules are applied
4. **Application Pools** → Set .NET Framework version
5. **Default Documents** → Ensure `manage.py` is listed

### Security Headers Configured:
- ✅ HSTS (HTTP Strict Transport Security)
- ✅ XSS Protection
- ✅ Content Type Options
- ✅ Frame Options
- ✅ Referrer Policy

## 🌐 Access Your Application

After deployment, access your application at:
- **HTTPS**: `https://projecthelal.rcs.ir`
- **HTTP**: `http://projecthelal.rcs.ir` (redirects to HTTPS)

## 🔍 Troubleshooting

### Common Issues:

1. **Certificate not trusted**: This is normal for self-signed certificates
2. **HTTP not redirecting**: Check URL Rewrite rules in web.config
3. **Static files not loading**: Verify static files are collected
4. **Django not responding**: Check FastCGI configuration

### Verification Commands:
```bash
# Test SSL certificate
openssl x509 -in ssl/iis_cert.pem -text -noout

# Check certificate validity
certutil -store -user My
```

## 📝 Production Notes

- Self-signed certificates are for development/testing
- For production, use a trusted CA certificate (Let's Encrypt, etc.)
- Consider using IIS ARR (Application Request Routing) for load balancing
- Monitor SSL certificate expiration dates

## 🚀 Next Steps

1. Test HTTPS access to your application
2. Create a superuser account
3. Configure production database (MySQL)
4. Set up monitoring and logging
5. Configure backup procedures
