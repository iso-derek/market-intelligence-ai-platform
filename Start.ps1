$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($version in @("3.13", "3.12")) {
        & py "-$version" -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) {
            & py "-$version" launch.py @args
            exit $LASTEXITCODE
        }
    }
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -c "import sys; assert sys.version_info[:2] in ((3, 12), (3, 13))" 2>$null
    if ($LASTEXITCODE -eq 0) {
        & python launch.py @args
        exit $LASTEXITCODE
    }
}

Write-Error "Python 3.12 or 3.13 was not found. Install a supported version, then run Start.ps1 again."
