@echo off
title Mohammed Hobi - PhotoPrint

echo ========================================
echo       Mohammed Hobi | PhotoPrint
echo       Building Windows Application
echo ========================================
echo.

:: استخدام أمر py لضمان التشغيل على ويندوز
py -m pip install -r requirements.txt

echo.
echo Creating application icon...
py make_icon.py

echo.
echo Building EXE...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "محمد هوبي PhotoPrint" --icon "photo_print.ico" photo_print.py

echo.
echo ========================================
echo       BUILD FINISHED
echo ========================================
echo.
echo The EXE file is inside the "dist" folder.
echo.
pause
