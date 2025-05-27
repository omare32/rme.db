@echo off
echo Git Commands Helper
echo ==================
echo.

IF "%~1"=="" (
    echo Usage: git_commands [command] [options]
    echo.
    echo Available commands:
    echo   status       - Show git status
    echo   add [files]  - Add files to staging (default: all)
    echo   commit [msg] - Commit changes with message (default: "Update")
    echo   push         - Push changes to remote repository
    echo   all [msg]    - Perform add, commit, and push in sequence
    echo.
    echo Examples:
    echo   git_commands status
    echo   git_commands add file1.txt file2.txt
    echo   git_commands commit "Fixed bug in login"
    echo   git_commands all "Weekly update"
    exit /b
)

SET command=%~1

IF "%command%"=="status" (
    echo Checking git status...
    git status
    exit /b
)

IF "%command%"=="add" (
    IF "%~2"=="" (
        echo Adding all files to staging...
        git add .
    ) ELSE (
        echo Adding specified files to staging...
        git add %~2 %~3 %~4 %~5 %~6 %~7 %~8 %~9
    )
    exit /b
)

IF "%command%"=="commit" (
    SET message=%~2
    IF "%message%"=="" SET message="Update"
    echo Committing with message: %message%
    git commit -m %message%
    exit /b
)

IF "%command%"=="push" (
    echo Pushing to remote repository...
    git push
    exit /b
)

IF "%command%"=="all" (
    SET message=%~2
    IF "%message%"=="" SET message="Update"
    echo Performing complete git workflow...
    echo.
    echo 1. Adding all files to staging...
    git add .
    echo.
    echo 2. Committing with message: %message%
    git commit -m %message%
    echo.
    echo 3. Pushing to remote repository...
    git push
    exit /b
)

echo Unknown command: %command%
echo Run git_commands without arguments to see usage information.