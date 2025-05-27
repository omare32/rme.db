@echo off
echo Starting Ollama API on GPU machine (10.10.12.202)...
echo.

REM Create a temporary PowerShell script to run the SSH commands
echo $password = ConvertTo-SecureString "PMO@1234" -AsPlainText -Force > "%TEMP%\start_ollama.ps1"
echo $credentials = New-Object System.Management.Automation.PSCredential ("ROWAD\Omar Essam2", $password) >> "%TEMP%\start_ollama.ps1"
echo $session = New-SSHSession -ComputerName 10.10.12.202 -Credential $credentials -AcceptKey >> "%TEMP%\start_ollama.ps1"

echo echo "Stopping any running Ollama process..." >> "%TEMP%\start_ollama.ps1"
echo Invoke-SSHCommand -SessionId $session.SessionId -Command "powershell -Command 'Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue'" >> "%TEMP%\start_ollama.ps1"

echo echo "Setting Ollama to listen on all interfaces..." >> "%TEMP%\start_ollama.ps1"
echo Invoke-SSHCommand -SessionId $session.SessionId -Command "powershell -Command '$env:OLLAMA_HOST=\"0.0.0.0:11434\"; [Environment]::SetEnvironmentVariable(\"OLLAMA_HOST\", \"0.0.0.0:11434\", \"User\")'" >> "%TEMP%\start_ollama.ps1"

echo echo "Starting Ollama service..." >> "%TEMP%\start_ollama.ps1"
echo Invoke-SSHCommand -SessionId $session.SessionId -Command "powershell -Command '$env:OLLAMA_HOST=\"0.0.0.0:11434\"; Start-Process -FilePath ollama -ArgumentList \"serve\" -WindowStyle Hidden'" >> "%TEMP%\start_ollama.ps1"

echo echo "Creating firewall rule for port 11434..." >> "%TEMP%\start_ollama.ps1"
echo Invoke-SSHCommand -SessionId $session.SessionId -Command "powershell -Command 'Get-NetFirewallRule -Name ollama-api -ErrorAction SilentlyContinue || New-NetFirewallRule -Name ollama-api -DisplayName \"Ollama API\" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow'" >> "%TEMP%\start_ollama.ps1"

echo echo "Verifying Ollama is running..." >> "%TEMP%\start_ollama.ps1"
echo $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "powershell -Command 'Get-Process -Name ollama -ErrorAction SilentlyContinue | Select-Object Id, Name'" >> "%TEMP%\start_ollama.ps1"
echo echo $result.Output >> "%TEMP%\start_ollama.ps1"

echo Remove-SSHSession -SessionId $session.SessionId >> "%TEMP%\start_ollama.ps1"
echo echo "SSH connection closed" >> "%TEMP%\start_ollama.ps1"
echo echo "Ollama API should now be accessible at http://10.10.12.202:11434" >> "%TEMP%\start_ollama.ps1"

REM Run the PowerShell script with admin privileges
powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%TEMP%\start_ollama.ps1\"' -Verb RunAs"

echo.
echo If you don't see any output, you may need to install the PowerShell SSH module.
echo To install it, run this command in an admin PowerShell window:
echo Install-Module -Name Posh-SSH -Force
echo.
echo Alternatively, here are the commands to run manually when you SSH into the GPU machine:
echo.
echo 1. Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
echo 2. $env:OLLAMA_HOST='0.0.0.0:11434'; [Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
echo 3. $env:OLLAMA_HOST='0.0.0.0:11434'; Start-Process -FilePath ollama -ArgumentList 'serve' -WindowStyle Hidden
echo 4. Get-NetFirewallRule -Name ollama-api -ErrorAction SilentlyContinue || New-NetFirewallRule -Name ollama-api -DisplayName 'Ollama API' -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow
echo 5. Get-Process -Name ollama -ErrorAction SilentlyContinue
echo.
echo Press any key to exit...
pause > nul
