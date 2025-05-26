@echo off
echo ===============================================================
echo Updating Alstom Project Assistant Chatbot Configuration
echo ===============================================================
echo.
echo This script will update the chatbot to use the Ollama API
echo running on the GPU machine (10.10.12.202).
echo.

set CHATBOT_FILE="15.vector_chatbot.rev.09(working).py"

echo Checking if chatbot file exists...
if not exist %CHATBOT_FILE% (
    echo ERROR: Chatbot file %CHATBOT_FILE% not found!
    echo Please run this script from the directory containing the chatbot file.
    goto :end
)

echo Creating backup of chatbot file...
copy %CHATBOT_FILE% "%CHATBOT_FILE%.bak" > nul

echo Updating Ollama API URL in chatbot file...
powershell -Command "(Get-Content %CHATBOT_FILE%) -replace '(OLLAMA_API_URL\s*=\s*)[^\r\n]+', '$1\"http://10.10.12.202:11434\"' | Set-Content %CHATBOT_FILE%"

echo.
echo ===============================================================
echo Configuration updated successfully!
echo.
echo The chatbot has been configured to use the Ollama API at:
echo http://10.10.12.202:11434
echo.
echo You can now run the chatbot with:
echo python %CHATBOT_FILE%
echo ===============================================================

:end
echo.
echo Press any key to exit...
pause > nul
