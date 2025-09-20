# IIS SSL Setup Script for Django Project Manager Dashboard
# Run as Administrator

Write-Host "🔐 Setting up SSL for IIS deployment..." -ForegroundColor Green

# Import WebAdministration module
Import-Module WebAdministration

# Create website if it doesn't exist
$siteName = "ProjectManagerDashboard"
$sitePath = "C:\inetpub\wwwroot\ProjectManagerDashboard"
$port = 80
$sslPort = 443

Write-Host "📁 Creating IIS website..." -ForegroundColor Yellow

# Remove existing site if it exists
if (Get-Website -Name $siteName -ErrorAction SilentlyContinue) {
    Remove-Website -Name $siteName
    Write-Host "Removed existing website" -ForegroundColor Red
}

# Create new website
New-Website -Name $siteName -Port $port -PhysicalPath $sitePath

Write-Host "🔒 Adding SSL binding..." -ForegroundColor Yellow

# Add HTTPS binding
New-WebBinding -Name $siteName -Protocol "https" -Port $sslPort

Write-Host "✅ SSL setup completed!" -ForegroundColor Green
Write-Host "Access your site at: https://projecthelal.rcs.ir" -ForegroundColor Cyan
