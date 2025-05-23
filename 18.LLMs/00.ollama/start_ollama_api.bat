@echo off
title Ollama API Server

:: Kill any existing Ollama processes
taskkill /F /IM ollama.exe 2>nul

:: Kill any process using port 11434
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :11434') do (
    taskkill /F /PID %%a 2>nul
)

:: Wait to ensure processes are fully terminated
timeout /t 3 /nobreak >nul

:: Set environment variables
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_CUDA=1
set OLLAMA_GPU_LAYERS=99
set OLLAMA_FLASH_ATTENTION=true
set OLLAMA_GPU_MEMORY=22

:: Start Ollama
ollama serve

pause
