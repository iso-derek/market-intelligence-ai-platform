@echo off
setlocal
cd /d "%~dp0"

py -3.13 -c "import sys" >nul 2>&1
if not errorlevel 1 (
  py -3.13 launch.py %*
  exit /b %errorlevel%
)

py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
  py -3.12 launch.py %*
  exit /b %errorlevel%
)

python -c "import sys; assert sys.version_info[:2] in ((3, 12), (3, 13))" >nul 2>&1
if not errorlevel 1 (
  python launch.py %*
  exit /b %errorlevel%
)

echo Python 3.12 or 3.13 was not found. Install a supported version, then run Start.cmd again.
exit /b 1
