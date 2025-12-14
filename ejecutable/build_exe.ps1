# PowerShell script to build a standalone executable using PyInstaller
# Usage (from project root):
#   .\build_exe.ps1 -Script main_simple.py -OneFile
# By default it will build 'main_simple.py'.

param(
    [string]$Script = "main_simple.py",
    [switch]$OneFile,
    [switch]$NoConsole
)

# Resolve Python executable to use (prefer venv\Scripts\python.exe if exists)
$venvPython = Join-Path -Path $PSScriptRoot -ChildPath 'venv\Scripts\python.exe'
if (Test-Path $venvPython) { $py = $venvPython } else { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Error "No se encontró python en PATH ni venv. Asegúrate de tener Python instalado."; exit 1 }

Write-Host "Usando Python: $py"

# Ensure PyInstaller is installed
& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install pyinstaller --upgrade

# Build args
$buildArgs = @()
if ($OneFile) { $buildArgs += '--onefile' }
if ($NoConsole) { $buildArgs += '--noconsole' }

# Collect data folders to include (if present)
$dataFolders = @('config','models','utils','writers','scraper')
foreach ($d in $dataFolders) {
    $full = Join-Path -Path $PSScriptRoot -ChildPath $d
    if (Test-Path $full) {
        # On Windows use ';' to separate source and destination
        $buildArgs += @("--add-data", "${full};$d")
    }
}

# Optionally include README and requirements
foreach ($f in @('README.md','requirements.txt')) {
    $full = Join-Path -Path $PSScriptRoot -ChildPath $f
    if (Test-Path $full) { $buildArgs += @("--add-data", "${full};.") }
}

# Extra PyInstaller options (hidden imports can be added if errors occur)
# Extra PyInstaller options (hidden imports can be added if errors occur)
$buildArgs += @('--clean', '--name', 'declaracion_importacion')

# Target script path
$scriptPath = Join-Path -Path $PSScriptRoot -ChildPath $Script
if (-not (Test-Path $scriptPath)) { Write-Error "Script no encontrado: $scriptPath"; exit 1 }

# Run PyInstaller
$argList = @('-m', 'PyInstaller') + $buildArgs + @($scriptPath)
Write-Host "Ejecutando: $($py) $($argList -join ' ')"
& $py @argList

Write-Host "Build finalizado. Revisa la carpeta 'dist' para el ejecutable o la carpeta generada."