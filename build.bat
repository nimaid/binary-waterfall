@echo off

set MAINFAILENAME=binary-waterfall
set ENVNAME=%MAINFAILENAME%
set BUILDENVNAME=build
set MODULENAME=binary_waterfall

set ORIGDIR=%CD%
set SOURCEDIR=%ORIGDIR%\src\%MODULENAME%
set DISTDIR=%ORIGDIR%\dist
set BUILDDIR=%ORIGDIR%\build

set PY=%ORIGDIR%\%MAINFAILENAME%.py
set SPEC=%ORIGDIR%\%MAINFAILENAME%.spec
set EXE=%DISTDIR%\%MAINFAILENAME%.exe
set TARGETEXE=%ORIGDIR%\%MAINFAILENAME%.exe

set VERSION_YAML=%SOURCEDIR%\version.yml
set VERSION_INFO=%ORIGDIR%\file_version_info.txt

set RESOURCEDIR=%SOURCEDIR%\resources
set ICON_ICO=%RESOURCEDIR%\icon.ico
set SPLASH_IMG=%RESOURCEDIR%\splash.jpg

echo Cleaning up before making release...
del /f /q "%TARGETEXE%" 1>nul 2>&1
del /f /s /q "%DISTDIR%" 1>nul 2>&1
rmdir /s /q "%DISTDIR%" 1>nul 2>&1
del /f /s /q "%BUILDDIR%" 1>nul 2>&1
rmdir /s /q "%BUILDDIR%" 1>nul 2>&1
del /f /q "%SPEC%" 1>nul 2>&1
del /f /q "%VERSION_INFO%" 1>nul 2>&1

echo Building portable EXE...
del /f /s /q "%TARGETEXE%" 1>nul 2>&1
call conda run -n %ENVNAME% create-version-file %VERSION_YAML% --outfile %VERSION_INFO%
if errorlevel 1 goto ERROR
call conda run -n %ENVNAME% pyinstaller ^
    --clean ^
    --noconfirm ^
    --noconsole ^
	--add-data %SOURCEDIR%\*.py;.\src\%MODULENAME% ^
	--add-data %SOURCEDIR%\version.yml;.\src\%MODULENAME% ^
	--add-data %SOURCEDIR%\constants\*.py;.\src\%MODULENAME%\constants ^
	--add-data %SOURCEDIR%\helpers\*.py;.\src\%MODULENAME%\helpers ^
	--add-data %SOURCEDIR%\resources\*;.\src\%MODULENAME%\resources ^
    --onefile ^
    --icon=%ICON_ICO% ^
    --splash=%SPLASH_IMG% ^
    --version-file=%VERSION_INFO% ^
    "%PY%"
if errorlevel 1 goto ERROR

echo Cleaning up after making .exe release...
move "%EXE%" "%TARGETEXE%"
del /f /s /q "%DISTDIR%" 1>nul 2>&1
rmdir /s /q "%DISTDIR%" 1>nul 2>&1
del /f /s /q "%BUILDDIR%" 1>nul 2>&1
rmdir /s /q "%BUILDDIR%" 1>nul 2>&1
del /f /q "%SPEC%" 1>nul 2>&1
del /f /q "%VERSION_INFO%" 1>nul 2>&1

echo Making PyPI release...
call conda run -n %BUILDENVNAME% python -m build
if errorlevel 1 goto ERROR

goto DONE


:ERROR
cd %ORIGDIR%
echo Build failed!
exit /B 1

:DONE
cd %ORIGDIR%
echo Build done!
exit /B 0
