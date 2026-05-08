# ============================================
# JARVIS OS - Script de Instalacion Completa
# Ejecutar como Administrador en PowerShell
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  JARVIS OS - Instalacion Completa" -ForegroundColor Cyan
Write-Host "  Stark Industries Style" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos de administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host "Click derecho en PowerShell -> Ejecutar como administrador" -ForegroundColor Yellow
    pause
    exit 1
}

$ErrorActionPreference = "Stop"

# ============================================
# 1. INSTALAR CHOCOLATEY
# ============================================
Write-Host "[1/8] Instalando Chocolatey..." -ForegroundColor Yellow

if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "Chocolatey ya esta instalado" -ForegroundColor Green
} else {
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "Chocolatey instalado correctamente" -ForegroundColor Green
    } catch {
        Write-Host "Error instalando Chocolatey: $_" -ForegroundColor Red
        pause
        exit 1
    }
}

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
refreshenv -ErrorAction SilentlyContinue

# ============================================
# 2. INSTALAR PYTHON 3.11
# ============================================
Write-Host ""
Write-Host "[2/8] Instalando Python 3.11..." -ForegroundColor Yellow

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detectado: $pythonVersion" -ForegroundColor Green
} else {
    try {
        choco install python311 -y
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        refreshenv -ErrorAction SilentlyContinue
        Write-Host "Python 3.11 instalado correctamente" -ForegroundColor Green
    } catch {
        Write-Host "Error instalando Python: $_" -ForegroundColor Red
        pause
        exit 1
    }
}

# ============================================
# 3. INSTALAR GIT
# ============================================
Write-Host ""
Write-Host "[3/8] Instalando Git..." -ForegroundColor Yellow

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "Git ya esta instalado" -ForegroundColor Green
} else {
    try {
        choco install git -y
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        refreshenv -ErrorAction SilentlyContinue
        Write-Host "Git instalado correctamente" -ForegroundColor Green
    } catch {
        Write-Host "Error instalando Git: $_" -ForegroundColor Red
        pause
        exit 1
    }
}

# ============================================
# 4. INSTALAR MOSQUITTO MQTT
# ============================================
Write-Host ""
Write-Host "[4/8] Instalando Mosquitto MQTT..." -ForegroundColor Yellow

if (Get-Service mosquitto -ErrorAction SilentlyContinue) {
    Write-Host "Mosquitto ya esta instalado" -ForegroundColor Green
} else {
    try {
        choco install mosquitto -y
        
        Start-Service mosquitto
        Set-Service mosquitto -StartupType Automatic
        
        New-NetFirewallRule -DisplayName "Mosquitto MQTT" -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow -ErrorAction SilentlyContinue
        
        Write-Host "Mosquitto MQTT instalado y ejecutandose" -ForegroundColor Green
    } catch {
        Write-Host "Error instalando Mosquitto: $_" -ForegroundColor Red
        pause
        exit 1
    }
}

# ============================================
# 5. INSTALAR OLLAMA
# ============================================
Write-Host ""
Write-Host "[5/8] Instalando Ollama..." -ForegroundColor Yellow

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Ollama ya esta instalado" -ForegroundColor Green
} else {
    try {
        choco install ollama -y
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        refreshenv -ErrorAction SilentlyContinue
        Write-Host "Ollama instalado correctamente" -ForegroundColor Green
    } catch {
        Write-Host "Error instalando Ollama: $_" -ForegroundColor Red
        pause
        exit 1
    }
}

$ollamaRunning = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Write-Host "Iniciando Ollama en segundo plano..." -ForegroundColor Yellow
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# ============================================
# 6. DESCARGAR MODELO DE OLLAMA
# ============================================
Write-Host ""
Write-Host "[6/8] Descargando modelo llama3.2:3b (2GB)..." -ForegroundColor Yellow
Write-Host "Esto puede tardar unos minutos..." -ForegroundColor Yellow

try {
    ollama pull llama3.2:3b
    Write-Host "Modelo descargado correctamente" -ForegroundColor Green
} catch {
    Write-Host "Error descargando modelo: $_" -ForegroundColor Yellow
    Write-Host "Puedes descargarlo manualmente despues con: ollama pull llama3.2:3b" -ForegroundColor Yellow
}

# ============================================
# 7. CREAR ENTORNO VIRTUAL E INSTALAR DEPENDENCIAS
# ============================================
Write-Host ""
Write-Host "[7/8] Configurando entorno Python..." -ForegroundColor Yellow

$projectPath = "C:\JARVIS_OS"

if (-not (Test-Path $projectPath)) {
    New-Item -ItemType Directory -Path $projectPath -Force | Out-Null
}

Set-Location $projectPath

if (Test-Path "$projectPath\venv") {
    Write-Host "Entorno virtual ya existe" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "Entorno virtual creado" -ForegroundColor Green
}

Write-Host "Instalando dependencias Python..." -ForegroundColor Yellow

& "$projectPath\venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Null

$packages = @(
    "faster-whisper",
    "sounddevice",
    "numpy",
    "paho-mqtt",
    "pyyaml",
    "PySide6",
    "requests",
    "pygetwindow",
    "psutil",
    "openwakeword",
    "piper-tts"
)

foreach ($package in $packages) {
    Write-Host "  Instalando $package..." -ForegroundColor Gray
    & "$projectPath\venv\Scripts\pip.exe" install $package | Out-Null
}

Write-Host "Dependencias instaladas correctamente" -ForegroundColor Green

# ============================================
# 8. DESCARGAR VOZ ESPAÑOLA PIPER TTS
# ============================================
Write-Host ""
Write-Host "[8/8] Descargando voz espanola para Piper TTS..." -ForegroundColor Yellow

try {
    & "$projectPath\venv\Scripts\python.exe" -c @"
from piper.download import get_voice
import os
os.makedirs('$projectPath\models', exist_ok=True)
get_voice('es_ES-carlfm-medium', download_dir='$projectPath\models')
"@
    Write-Host "Voz espanola descargada correctamente" -ForegroundColor Green
} catch {
    Write-Host "Error descargando voz: $_" -ForegroundColor Yellow
}

# ============================================
# FINALIZAR
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Componentes instalados:" -ForegroundColor White
Write-Host "  [x] Chocolatey" -ForegroundColor Green
Write-Host "  [x] Python 3.11" -ForegroundColor Green
Write-Host "  [x] Git" -ForegroundColor Green
Write-Host "  [x] Mosquitto MQTT (puerto 1883)" -ForegroundColor Green
Write-Host "  [x] Ollama + llama3.2:3b" -ForegroundColor Green
Write-Host "  [x] Piper TTS + voz espanola" -ForegroundColor Green
Write-Host "  [x] Entorno virtual + dependencias" -ForegroundColor Green
Write-Host ""
Write-Host "Carpeta del proyecto: C:\JARVIS_OS" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para empezar:" -ForegroundColor Cyan
Write-Host "  cd C:\JARVIS_OS" -ForegroundColor White
Write-Host "  .\venv\Scripts\activate" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Servicios en ejecucion:" -ForegroundColor Cyan
Write-Host "  Mosquitto MQTT: localhost:1883" -ForegroundColor Gray
Write-Host "  Ollama: localhost:11434" -ForegroundColor Gray
Write-Host ""

pause