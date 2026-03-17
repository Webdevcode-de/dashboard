@echo off
REM --- Clean old builds ---
rmdir /s /q build
rmdir /s /q dist

REM --- Build screen.exe ---
pyinstaller --onefile --windowed --name screen --icon logo.ico --add-data "config.json;." main.py

REM --- Build configurator.exe ---
pyinstaller --onefile --windowed --name configurator --icon logo.ico --add-data "config.json;." configurator.py

REM --- Build uninstall.exe ---
pyinstaller --onefile --noconsole --name uninstall --icon logo.ico uninstall.py

REM --- Ensure dist folder exists for installer ---
if not exist dist mkdir dist

REM --- Build installer.exe ---
pyinstaller --onefile --windowed --name installer --icon logo.ico --add-data "dist;dist" installer.py

echo.
echo All EXEs built successfully!
pause
