# Modern Windows installer builder for Metadata Cleaner
# Version: 2.0.0
# PowerShell script for building NSIS installer

param(
    [switch]$Help,
    [string]$Architecture = "auto",
    [switch]$Verbose
)

# Configuration
$ErrorActionPreference = "Stop"
$APP_NAME = "Metadata Cleaner"
$APP_VERSION = "1.0.1"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
$DIST_DIR = Join-Path $PROJECT_ROOT "dist"

# Helper functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info { param([string]$Message) Write-ColorOutput "[INFO] $Message" "Cyan" }
function Write-Success { param([string]$Message) Write-ColorOutput "[SUCCESS] $Message" "Green" }
function Write-Warning { param([string]$Message) Write-ColorOutput "[WARNING] $Message" "Yellow" }
function Write-Error { param([string]$Message) Write-ColorOutput "[ERROR] $Message" "Red" }

function Show-Help {
    Write-Output @"
Windows Installer Builder for Metadata Cleaner

USAGE:
    .\build.ps1 [OPTIONS]

OPTIONS:
    -Architecture <arch>    Target architecture (auto, x64, x86, arm64) [default: auto]
    -Verbose               Enable verbose output
    -Help                  Show this help message

EXAMPLES:
    .\build.ps1                     # Build for current architecture
    .\build.ps1 -Architecture x64   # Build for x64 specifically
    .\build.ps1 -Verbose           # Build with verbose output

REQUIREMENTS:
    - NSIS (Nullsoft Scriptable Install System)
    - Built application in dist/MetadataCleaner/
    - Windows PowerShell 5.0 or later

NOTES:
    - Requires administrator privileges for proper testing
    - NSIS must be installed and in PATH
    - Run 'python build.py' first to build the application
"@
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-SystemArchitecture {
    $arch = (Get-WmiObject Win32_OperatingSystem).OSArchitecture
    switch ($arch) {
        "64-bit" { return "x64" }
        "32-bit" { return "x86" }
        "ARM64" { return "arm64" }
        default { 
            Write-Warning "Unknown architecture: $arch, defaulting to x64"
            return "x64"
        }
    }
}

function Test-NSISInstallation {
    Write-Info "Checking for NSIS installation..."
    
    # Check for makensis in PATH
    if (Get-Command "makensis" -ErrorAction SilentlyContinue) {
        Write-Success "NSIS found in PATH"
        return $true
    }
    
    # Check common installation paths
    $commonPaths = @(
        "${env:ProgramFiles}\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "C:\Program Files\NSIS\makensis.exe",
        "C:\Program Files (x86)\NSIS\makensis.exe"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            Write-Success "NSIS found at: $path"
            $env:PATH += ";$(Split-Path $path)"
            return $true
        }
    }
    
    Write-Error "NSIS not found. Please install NSIS from https://nsis.sourceforge.io/"
    Write-Info "After installation, add NSIS to your PATH or restart PowerShell"
    return $false
}

function Test-BuildFiles {
    Write-Info "Validating build files..."
    
    $requiredFiles = @(
        (Join-Path $DIST_DIR "MetadataCleaner"),
        (Join-Path $PROJECT_ROOT "assets\icons\icon.ico"),
        (Join-Path $PROJECT_ROOT "docs\LICENSE_INSTALLER.txt")
    )
    
    $missing = @()
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missing += $file
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Error "Missing required files:"
        foreach ($file in $missing) {
            Write-Error "  - $file"
        }
        Write-Info "Run 'python build.py' first to build the application"
        return $false
    }
    
    Write-Success "All required files found"
    return $true
}

function Build-Installer {
    param([string]$TargetArch)
    
    Write-Info "Building Windows installer for $TargetArch architecture..."
    
    $nsisScript = Join-Path $SCRIPT_DIR "installer.nsi"
    $outputPath = Join-Path $DIST_DIR "MetadataCleaner-Windows-$TargetArch.exe"
    
    # Remove existing installer
    if (Test-Path $outputPath) {
        Remove-Item $outputPath -Force
        Write-Info "Removed existing installer"
    }
    
    # Prepare NSIS command
    $nsisArgs = @()
    
    # Add architecture definition if not auto-detected
    if ($TargetArch -eq "arm64") {
        $nsisArgs += "/DARM64"
    }
    
    # Add verbose flag if requested
    if ($Verbose) {
        $nsisArgs += "/V4"
    } else {
        $nsisArgs += "/V2"
    }
    
    # Add script path
    $nsisArgs += $nsisScript
    
    # Execute NSIS
    Write-Info "Running NSIS with arguments: $($nsisArgs -join ' ')"
    
    try {
        $process = Start-Process -FilePath "makensis" -ArgumentList $nsisArgs -NoNewWindow -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            if (Test-Path $outputPath) {
                $size = [math]::Round((Get-Item $outputPath).Length / 1MB, 2)
                Write-Success "Installer created successfully: $outputPath ($size MB)"
                return $true
            } else {
                Write-Error "NSIS completed but installer file not found"
                return $false
            }
        } else {
            Write-Error "NSIS compilation failed with exit code: $($process.ExitCode)"
            return $false
        }
    } catch {
        Write-Error "Failed to run NSIS: $($_.Exception.Message)"
        return $false
    }
}

function Test-Installer {
    param([string]$InstallerPath)
    
    Write-Info "Testing installer..."
    
    if (-not (Test-Path $InstallerPath)) {
        Write-Error "Installer not found: $InstallerPath"
        return $false
    }
    
    # Basic file validation
    try {
        $fileInfo = Get-Item $InstallerPath
        if ($fileInfo.Length -lt 1MB) {
            Write-Warning "Installer seems unusually small ($([math]::Round($fileInfo.Length / 1MB, 2)) MB)"
        }
        
        # Check if it's a valid executable
        $signature = [System.IO.File]::ReadAllBytes($InstallerPath)[0..1]
        if ($signature[0] -ne 0x4D -or $signature[1] -ne 0x5A) {
            Write-Error "Installer does not appear to be a valid executable"
            return $false
        }
        
        Write-Success "Installer validation passed"
        return $true
    } catch {
        Write-Error "Failed to validate installer: $($_.Exception.Message)"
        return $false
    }
}

function Show-Usage {
    Write-Info "Windows Installer Build Completed"
    Write-Info ""
    Write-Info "Distribution:"
    Write-Info "  1. Share the .exe file with Windows users"
    Write-Info "  2. Users run as administrator for system-wide installation"
    Write-Info "  3. Installer handles all setup automatically"
    Write-Info ""
    Write-Info "Manual Testing:"
    Write-Info "  - Run installer in a test environment"
    Write-Info "  - Verify all components install correctly"
    Write-Info "  - Test uninstallation process"
    Write-Info ""
    Write-Info "Code Signing (Optional):"
    Write-Info "  For trusted distribution, consider code signing with:"
    Write-Info "  - Microsoft Authenticode certificate"
    Write-Info "  - signtool.exe from Windows SDK"
}

# Main execution
function Main {
    Write-Info "Starting Windows installer build for $APP_NAME v$APP_VERSION"
    
    # Show help if requested
    if ($Help) {
        Show-Help
        return
    }
    
    # Check administrator privileges
    if (-not (Test-Administrator)) {
        Write-Warning "Not running as administrator. Some operations may fail."
        Write-Info "Consider running as administrator for complete testing."
    }
    
    # Set working directory
    Set-Location $PROJECT_ROOT
    
    # Determine target architecture
    $targetArch = $Architecture
    if ($targetArch -eq "auto") {
        $targetArch = Get-SystemArchitecture
        Write-Info "Auto-detected architecture: $targetArch"
    } else {
        Write-Info "Target architecture: $targetArch"
    }
    
    # Validate architecture
    if ($targetArch -notin @("x64", "x86", "arm64")) {
        Write-Error "Unsupported architecture: $targetArch"
        Write-Error "Supported: x64, x86, arm64"
        exit 1
    }
    
    # Check dependencies
    if (-not (Test-NSISInstallation)) {
        exit 1
    }
    
    # Validate build files
    if (-not (Test-BuildFiles)) {
        exit 1
    }
    
    # Build installer
    if (Build-Installer $targetArch) {
        $installerPath = Join-Path $DIST_DIR "MetadataCleaner-Windows-$targetArch.exe"
        
        # Test installer
        if (Test-Installer $installerPath) {
            Show-Usage
            Write-Success "Build process completed successfully!"
        } else {
            Write-Error "Installer validation failed"
            exit 1
        }
    } else {
        Write-Error "Installer build failed"
        exit 1
    }
}

# Script entry point
if ($MyInvocation.InvocationName -ne '.') {
    Main
}