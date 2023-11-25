@echo off

set MAINFAILENAME=binary-waterfall
set ENVNAME=%MAINFAILENAME%

set ORIGDIR=%CD%
set DISTDIR=%ORIGDIR%\dist
set BUILDDIR=%ORIGDIR%\build

set PY=%ORIGDIR%\%MAINFAILENAME%.py
set SPEC=%ORIGDIR%\%MAINFAILENAME%.spec
set EXE=%DISTDIR%\%MAINFAILENAME%.exe

set VERSION_INFO=%ORIGDIR%\file_version_info.txt


echo Building portable EXE...
call conda run -n %ENVNAME% create-version-file version.yml --outfile %VERSION_INFO%
if errorlevel 1 goto ERROR
call conda run -n %ENVNAME% pyinstaller ^
    --clean ^
    --noconfirm ^
    --noconsole ^
	--add-data resources\;resources\ ^
    --add-data version.yml;. ^
    --add-data icon.png;. ^
    --onefile ^
    --icon=icon.ico ^
    --version-file=%VERSION_INFO% ^
    "%PY%"
if errorlevel 1 goto ERROR

echo Cleaning up before making release...
move "%EXE%" "%ORIGDIR%"
del /f /s /q "%DISTDIR%" 1>nul 2>&1
rmdir /s /q "%DISTDIR%" 1>nul 2>&1
del /f /s /q "%BUILDDIR%" 1>nul 2>&1
rmdir /s /q "%BUILDDIR%" 1>nul 2>&1
del /f /q "%SPEC%" 1>nul 2>&1
del /f /q "%VERSION_INFO%" 1>nul 2>&1

goto DONE


:ERROR
cd %ORIGDIR%
echo Portable EXE build failed!
exit /B 1

:DONE
cd %ORIGDIR%
echo Portable EXE build done!
exit /B 0