@echo off
chcp 65001 >nul
setlocal

rem -- Python kurulu mu kontrol et --
python --version >nul 2>&1
if errorlevel 1 (
    echo Python bulunamadi! Lütfen Python'u indirip kurunuz:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
) else (
    echo Python versiyonu:
    python --version
)

echo.

rem -- XGBoost uyarılarını bastırmak için PYTHONWARNINGS ayarlanabilir --
set PYTHONWARNINGS=ignore

rem -- Paket kontrol ve yükleme fonksiyonu --
call :check_and_install flask flask
call :check_and_install waitress waitress
call :check_and_install joblib joblib
call :check_and_install numpy numpy
call :check_and_install flask_cors Flask-Cors
call :check_and_install xgboost xgboost
call :check_and_install pandas pandas
call :check_and_install sklearn scikit-learn

echo.
echo Uygulama baslatiliyor, lutfen bekleyin
echo.

rem -- Uygulamayi normal modda baslat, hata varsa dur ve mesaj ver --
start /b python appv2.py
:: start "" /min cmd /c python appv2.py

call :loading_animation 5

if errorlevel 1 (
    goto :eof
)

rem -- Tarayıcıyı aç --
start "" http://localhost:5000

echo.
echo Eger tarayici açilmazsa, aşağidaki linki kopyalayip, tarayicida adres çubuğuna yapistirin ve enter'a basin:
echo http://localhost:5000

goto :eof

:check_and_install
rem %1 = import adı, %2 = pip paketi adı
python -c "import %1" 2>nul >nul
if errorlevel 1 (
    echo %2 paketi yüklü değil, kuruluyor...
    pip install --no-index --find-links=pip_paketleri %2 >nul 2>&1
) else (
    echo %2 paketi zaten yüklü.
)
goto :eof

:loading_animation
set /a count=0
:loop
set /a count+=1
<nul set /p=.
timeout /t 1 /nobreak >nul
if %count% lss %1 goto loop
echo.
goto :eof