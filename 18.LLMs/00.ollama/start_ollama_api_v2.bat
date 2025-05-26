@echo off
title Ollama API Server
setlocal enabledelayedexpansion

:: Kill any existing Ollama processes
taskkill /F /IM ollama.exe 2>nul
timeout /t 3 /nobreak >nul

:: Set environment variables
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_CUDA=1
set OLLAMA_GPU_LAYERS=99
set OLLAMA_FLASH_ATTENTION=true
set OLLAMA_GPU_MEMORY=22

echo Setting up Ollama server...
echo Environment variables:
echo OLLAMA_HOST = %OLLAMA_HOST%
echo OLLAMA_CUDA = %OLLAMA_CUDA%
echo OLLAMA_GPU_LAYERS = %OLLAMA_GPU_LAYERS%
echo OLLAMA_FLASH_ATTENTION = %OLLAMA_FLASH_ATTENTION%
echo OLLAMA_GPU_MEMORY = %OLLAMA_GPU_MEMORY%

echo.
echo Starting Ollama server...
echo.

:: Run Ollama in the current console
start "Ollama Server" /B /WAIT ollama serve

:: If we get here, something went wrong
echo.
echo Server stopped! Check the output above for errors.
echo.
pause
