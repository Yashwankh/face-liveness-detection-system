@echo off
echo ========================================
echo   Aadhaar Face Verification System
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements_web.txt
echo.
echo Starting Flask server...
echo Open your browser and go to: http://localhost:5000
echo.
python app.py
pause
