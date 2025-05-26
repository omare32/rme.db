@echo off
title Ollama API Server

:: Kill any existing Ollama processes
taskkill /F /IM ollama.exe 2>nul
timeout /t 3 /nobreak >nul

:: Use a different port (11435 instead of 11434)
set PORT=11435

:: Set environment variables
set OLLAMA_HOST=0.0.0.0:%PORT%
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
