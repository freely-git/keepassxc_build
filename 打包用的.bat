@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYTHON_SCRIPT=keepass_converter.py"
set "ICON_FILE=icon.ico"

if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: Python script '%PYTHON_SCRIPT%' not found.
    pause
    exit /b 1
)

if not exist "%ICON_FILE%" (
    echo ERROR: Icon file '%ICON_FILE%' not found.
    pause
    exit /b 1
)

echo [1/4] 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
)
call "venv\Scripts\activate.bat"

echo [2/4] 安装依赖...
pip install --upgrade pip
pip install PySide6 pykeepass requests pyinstaller

if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages.
    pause
    exit /b 1
)

echo [3/4] 清理旧构建文件...
rmdir /s /q build
rmdir /s /q dist

echo [4/4] 正在打包...
pyinstaller --name "KeePass_CSV_Converter" ^
    --onefile ^
    --windowed ^
    --icon="%ICON_FILE%" ^
    --add-data "%ICON_FILE%;." ^
    --add-data "venv\Lib\site-packages\pykeepass\blank_database.kdbx;pykeepass" ^
    "%PYTHON_SCRIPT%"

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller failed.
    pause
    exit /b 1
)

echo.
echo ✅ 打包成功！可执行文件在 dist\KeePass_CSV_Converter.exe
echo.

call "venv\Scripts\deactivate.bat"
pause
