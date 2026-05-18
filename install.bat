@echo off
echo 📦 Installing AI Job Hunting System Dependencies...
cd /d "%~dp0"
pip install -r requirements.txt
echo ✅ Installation complete! Now run start.bat
pause
