@echo off
title Ollama API Server

:: Kill any existing Ollama processes
taskkill /F /IM ollama.exe 2>nul

:: Find and kill any process using port 11434
for /f "tokens=5" %%a in ('netstat -aon ^| find "11434"') do (
    taskkill /F /PID %%a 2>nul
)

:: Wait a bit
timeout /t 3 /nobreak >nul

:: Double check port is free
for /f "tokens=5" %%a in ('netstat -aon ^| find "11434"') do (
    echo Port 11434 is still in use by PID: %%a
    taskkill /F /PID %%a 2>nul
    timeout /t 2 /nobreak >nul
)

:: Set environment variables
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_CUDA=1
set OLLAMA_GPU_LAYERS=99
set OLLAMA_FLASH_ATTENTION=true
set OLLAMA_GPU_MEMORY=22

echo Starting Ollama server...

:: Start Ollama and redirect error output to a file
ollama serve 2> ollama_error.txt

:: If we get here, something went wrong
echo Server stopped unexpectedly!
echo Checking error log:
type ollama_error.txt

echo.
echo Press any key to exit...
pause > nul
