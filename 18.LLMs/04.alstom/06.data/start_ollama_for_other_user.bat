@echo off
echo ===============================================================
echo Ollama API Starter for Alstom Project Assistant
echo ===============================================================
echo.
echo This script will configure and start the Ollama API service
echo to accept connections from other machines on the network.
echo.
echo Press any key to continue or CTRL+C to cancel...
pause > nul

echo.
echo 1. Stopping any running Ollama process...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak > nul

echo.
echo 2. Setting Ollama to listen on all interfaces...
setx OLLAMA_HOST "0.0.0.0:11434" /M
set OLLAMA_HOST=0.0.0.0:11434

echo.
echo 3. Creating firewall rule for Ollama API (port 11434)...
netsh advfirewall firewall show rule name="Ollama API" > nul 2>&1
if %errorlevel% neq 0 (
    netsh advfirewall firewall add rule name="Ollama API" dir=in action=allow protocol=TCP localport=11434
    echo    - Firewall rule created successfully
) else (
    echo    - Firewall rule already exists
)

echo.
echo 4. Starting Ollama service...
start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve

echo.
echo 5. Waiting for Ollama to initialize...
timeout /t 5 /nobreak > nul

echo.
echo 6. Checking if Ollama is running...
tasklist | findstr ollama

echo.
echo 7. Testing API accessibility...
curl -s http://localhost:11434/api/tags > nul 2>&1
if %errorlevel% equ 0 (
    echo    - Ollama API is accessible locally
) else (
    echo    - Could not connect to Ollama API locally
)

echo.
echo ===============================================================
echo Configuration complete!
echo.
echo The Ollama API should now be accessible at:
echo http://%COMPUTERNAME%:11434 or http://10.10.12.202:11434
echo.
echo Please keep this window open to keep the Ollama service running.
echo ===============================================================
echo.
echo Press any key to exit...
pause > nul
