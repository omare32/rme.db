@echo off
echo ===============================================================
echo Manual steps to start Ollama API on GPU machine (10.10.12.202)
echo ===============================================================
echo.
echo 1. Open PowerShell and connect to the GPU machine using:
echo    ssh -l "ROWAD\Omar Essam2" 10.10.12.202
echo.
echo 2. Enter your password when prompted: PMO@1234
echo.
echo 3. Run these commands one by one:
echo.
echo    # Stop any running Ollama process
echo    Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
echo.
echo    # Set Ollama to listen on all interfaces
echo    $env:OLLAMA_HOST='0.0.0.0:11434'; [Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
echo.
echo    # Start Ollama service
echo    $env:OLLAMA_HOST='0.0.0.0:11434'; Start-Process -FilePath ollama -ArgumentList 'serve' -WindowStyle Hidden
echo.
echo    # Create firewall rule for port 11434
echo    Get-NetFirewallRule -Name ollama-api -ErrorAction SilentlyContinue ^|^| New-NetFirewallRule -Name ollama-api -DisplayName 'Ollama API' -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow
echo.
echo    # Verify Ollama is running
echo    Get-Process -Name ollama -ErrorAction SilentlyContinue
echo.
echo 4. After running these commands, the Ollama API should be accessible at:
echo    http://10.10.12.202:11434
echo.
echo 5. You can now update your chatbot to use this API URL.
echo.
echo Press any key to exit...
pause > nul
