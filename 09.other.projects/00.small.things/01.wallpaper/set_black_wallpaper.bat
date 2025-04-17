@echo off
echo Setting solid black wallpaper...

:: Set wallpaper registry key
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "C:\Wallpapers\black.bmp" /f

:: Apply wallpaper setting immediately
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters

echo Done! Your wallpaper should now be black.
pause
