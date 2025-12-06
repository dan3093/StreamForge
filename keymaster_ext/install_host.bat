@echo off
echo Installing StreamForge Keymaster Native Host...

:: Register the native messaging host in the registry
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.streamforge.keymaster" /ve /t REG_SZ /d "%~dp0com.streamforge.keymaster.json" /f

if %errorlevel% == 0 (
    echo.
    echo SUCCESS! Native host registered.
    echo.
    echo NEXT STEPS:
    echo 1. Load the extension in Chrome (chrome://extensions)
    echo 2. Copy the Extension ID
    echo 3. Edit com.streamforge.keymaster.json
    echo 4. Replace EXTENSION_ID_HERE with your actual ID
    echo 5. Reload the extension
    echo.
) else (
    echo ERROR: Failed to register native host.
)

pause
