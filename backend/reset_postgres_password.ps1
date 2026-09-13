# PostgreSQL Password Reset Script
# Run this script as Administrator

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "PostgreSQL Password Reset for AccessSlot" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# PostgreSQL paths
$psqlPath = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
$pgHbaPath = "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"

# Verify PostgreSQL is installed
if (-not (Test-Path $psqlPath)) {
    Write-Host "ERROR: PostgreSQL not found at expected location" -ForegroundColor Red
    exit 1
}

# Step 1: Backup pg_hba.conf
Write-Host "Step 1: Backing up pg_hba.conf..." -ForegroundColor Yellow
try {
    $backupPath = "$pgHbaPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $pgHbaPath $backupPath -ErrorAction Stop
    Write-Host "OK Backup created: $backupPath" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to backup pg_hba.conf: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Modify pg_hba.conf to trust authentication
Write-Host "`nStep 2: Configuring temporary trust authentication..." -ForegroundColor Yellow
try {
    $content = Get-Content $pgHbaPath -Raw
    $content = $content -replace 'host\s+all\s+all\s+127\.0\.0\.1/32\s+scram-sha-256', 'host    all             all             127.0.0.1/32            trust'
    $content = $content -replace 'host\s+all\s+all\s+::1/128\s+scram-sha-256', 'host    all             all             ::1/128                 trust'
    Set-Content $pgHbaPath -Value $content -ErrorAction Stop
    Write-Host "OK pg_hba.conf configured for trust authentication" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to modify pg_hba.conf: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Restart PostgreSQL service
Write-Host "`nStep 3: Restarting PostgreSQL service..." -ForegroundColor Yellow
try {
    Restart-Service postgresql-x64-18 -ErrorAction Stop
    Write-Host "OK PostgreSQL service restarted" -ForegroundColor Green
    Start-Sleep -Seconds 3
} catch {
    Write-Host "ERROR: Failed to restart service: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Generate a secure random password
Write-Host "`nStep 4: Generating new secure password..." -ForegroundColor Yellow
$newPassword = -join ((48..57) + (65..90) + (97..122) + 33,64,35,36,37,94,38,42 | Get-Random -Count 16 | ForEach-Object {[char]$_})
Write-Host "OK New password generated (16 characters)" -ForegroundColor Green

# Step 5: Reset PostgreSQL password
Write-Host "`nStep 5: Resetting PostgreSQL password..." -ForegroundColor Yellow
try {
    $sqlCommand = "ALTER USER postgres WITH PASSWORD '$newPassword';"
    $env:PGPASSWORD = ""
    $result = & $psqlPath -U postgres -h 127.0.0.1 -d postgres -c $sqlCommand 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK Password reset successful" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Password reset failed" -ForegroundColor Red
        Write-Host $result
        exit 1
    }
} catch {
    Write-Host "ERROR: Exception during password reset: $_" -ForegroundColor Red
    exit 1
}

# Step 6: Restore pg_hba.conf to scram-sha-256
Write-Host "`nStep 6: Restoring secure authentication..." -ForegroundColor Yellow
try {
    $content = Get-Content $pgHbaPath -Raw
    $content = $content -replace 'host\s+all\s+all\s+127\.0\.0\.1/32\s+trust', 'host    all             all             127.0.0.1/32            scram-sha-256'
    $content = $content -replace 'host\s+all\s+all\s+::1/128\s+trust', 'host    all             all             ::1/128                 scram-sha-256'
    Set-Content $pgHbaPath -Value $content -ErrorAction Stop
    Write-Host "OK Authentication method restored to scram-sha-256" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to restore pg_hba.conf: $_" -ForegroundColor Red
    exit 1
}

# Step 7: Restart PostgreSQL service again
Write-Host "`nStep 7: Restarting PostgreSQL with secure authentication..." -ForegroundColor Yellow
try {
    Restart-Service postgresql-x64-18 -ErrorAction Stop
    Write-Host "OK PostgreSQL service restarted" -ForegroundColor Green
    Start-Sleep -Seconds 3
} catch {
    Write-Host "ERROR: Failed to restart service: $_" -ForegroundColor Red
    exit 1
}

# Step 8: Test new password
Write-Host "`nStep 8: Testing new password..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = $newPassword
    $testResult = & $psqlPath -U postgres -h 127.0.0.1 -d postgres -c "SELECT version();" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK Password test successful" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Password test failed" -ForegroundColor Red
        Write-Host $testResult
        exit 1
    }
} catch {
    Write-Host "ERROR: Exception during password test: $_" -ForegroundColor Red
    exit 1
}

# Step 9: Create database if not exists
Write-Host "`nStep 9: Checking/creating accessslot_db database..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = $newPassword
    $checkDb = & $psqlPath -U postgres -h 127.0.0.1 -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='accessslot_db';" 2>&1
    
    if ($checkDb -match '1') {
        Write-Host "OK Database accessslot_db already exists" -ForegroundColor Green
    } else {
        $createDb = & $psqlPath -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE accessslot_db;" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK Database accessslot_db created" -ForegroundColor Green
        } else {
            Write-Host "ERROR: Failed to create database" -ForegroundColor Red
            Write-Host $createDb
            exit 1
        }
    }
} catch {
    Write-Host "ERROR: Exception during database creation: $_" -ForegroundColor Red
    exit 1
}

# Step 10: Update .env file
Write-Host "`nStep 10: Updating backend/.env file..." -ForegroundColor Yellow
try {
    $envPath = Join-Path $PSScriptRoot ".env"
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
        $envContent = $envContent -replace 'DB_PASSWORD=.*', "DB_PASSWORD=$newPassword"
        Set-Content $envPath -Value $envContent -NoNewline -ErrorAction Stop
        Write-Host "OK .env file updated with new password" -ForegroundColor Green
    } else {
        Write-Host "WARNING: .env file not found at: $envPath" -ForegroundColor Yellow
        Write-Host "Please manually update DB_PASSWORD in your .env file" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Error updating .env: $_" -ForegroundColor Yellow
    Write-Host "Please manually update DB_PASSWORD in your .env file" -ForegroundColor Yellow
}

Write-Host "`n$('=' * 60)" -ForegroundColor Cyan
Write-Host "SUCCESS: PASSWORD RESET COMPLETE" -ForegroundColor Green
Write-Host ('=' * 60) -ForegroundColor Cyan
Write-Host "`nThe new password has been set and saved to backend/.env" -ForegroundColor White
Write-Host "PostgreSQL is ready for use with Django." -ForegroundColor White
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Run migrations: python manage.py migrate" -ForegroundColor White
Write-Host "2. Run tests: pytest -v" -ForegroundColor White
Write-Host ""
