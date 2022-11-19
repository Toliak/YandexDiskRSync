$ErrorActionPreference = "Stop"

Write-Verbose "Script Root: $PSScriptRoot"

& "$PSScriptRoot\venv\Scripts\Activate.ps1"
$OldPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = "$PSScriptRoot"

python "$PSScriptRoot\yandex_disk_rsync" $args

$env:PYTHONPATH = $OldPythonPath
deactivate
