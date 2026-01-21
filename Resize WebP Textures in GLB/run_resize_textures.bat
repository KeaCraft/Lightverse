@echo off
setlocal EnableExtensions

REM ==========================
REM CONFIG: set your Blender path
REM ==========================
set "BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
set "SCRIPT=%~dp0resize_lv_textures_and_export.py"

echo ==========================================
echo LV GLB Texture Resizer (Blender Background)
echo ==========================================
echo.

if not exist "%BLENDER_EXE%" (
  echo ERROR: Blender executable not found:
  echo %BLENDER_EXE%
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPT%" (
  echo ERROR: Script not found:
  echo %SCRIPT%
  echo.
  pause
  exit /b 1
)

set /p INPUT_DIR=Enter INPUT folder (contains .glb files): 
if "%INPUT_DIR%"=="" (
  echo ERROR: No input folder provided.
  pause
  exit /b 1
)

set /p OUTPUT_DIR=Enter OUTPUT folder (processed .glb will be saved here): 
if "%OUTPUT_DIR%"=="" (
  echo ERROR: No output folder provided.
  pause
  exit /b 1
)

set /p MAX_SIZE=Enter MAX texture size (default 512): 
if "%MAX_SIZE%"=="" set "MAX_SIZE=512"

echo.
echo Running...
echo Input : %INPUT_DIR%
echo Output: %OUTPUT_DIR%
echo Max   : %MAX_SIZE%px
echo.

"%BLENDER_EXE%" -b -P "%SCRIPT%" -- --input "%INPUT_DIR%" --output "%OUTPUT_DIR%" --max_size "%MAX_SIZE%"

echo.
echo ==========================================
echo Finished. Press any key to close.
echo ==========================================
pause >nul
endlocal
