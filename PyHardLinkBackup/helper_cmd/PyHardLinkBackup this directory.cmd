@echo off
title %~0

set SCRIPT_PATH="%APPDATA%\PyHardLinkBackup\Scripts\"
cd /d %SCRIPT_PATH%
if not "%errorlevel%"=="0" (
    echo.
    echo ERROR: venv/Script path not found here:
    echo.
    echo %SCRIPT_PATH%
    echo.
    pause
    exit
)

set PHLB_EXE=phlb.exe
if NOT exist %PHLB_EXE% (
    echo.
    echo ERROR: Can't find %PHLB_EXE% in Scripts
    echo.
    echo Not found in: %SCRIPT_PATH%
    echo.
    pause
    exit 1
)

echo on

%PHLB_EXE% backup "%~dp0"

@echo off
echo.
pause