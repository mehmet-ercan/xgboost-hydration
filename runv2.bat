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
rem -- flask waitress joblib numpy flask_cors xgboost --
call :check_and_install flask
call :check_and_install waitress
call :check_and_install joblib
call :check_and_install numpy
call :check_and_install flask_cors
call :check_and_install xgboost
call :check_and_install pandas
call :check_and_install scikit-learn sklearn

echo.
echo Uygulama baslatiliyor, lutfen bekleyin
echo.

rem -- Uygulamayi normal modda baslat, hata varsa dur ve mesaj ver --
:: start /b python appv2.py
start "" /min cmd /c python appv2.py

call :loading_animation 5

if errorlevel 1 (
    goto :eof
)

rem -- Tarayiciyi ac --
start "" http://localhost:5000

echo.
echo Eger tarayıcı açılmazsa, aşağidaki linki kopyalayıp, tarayıcıda adres çubuğuna yapıstırın ve enter'a basın:
echo http://localhost:5000

goto :eof

:check_and_install
python -c "import %1" 2>nul >nul
if errorlevel 1 (
    echo %1 paketi yüklü değil, kuruluyor...
    pip install --no-index --find-links=pip_paketleri %1 >nul 2>&1
) else (
    echo %1 paketi zaten yüklü.
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