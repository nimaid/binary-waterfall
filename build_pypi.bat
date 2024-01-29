@echo off

set ENVNAME=binary-waterfall
set BUILDENVNAME=build

set ORIGDIR=%CD%
set DISTDIR=%ORIGDIR%\dist

call conda activate %BUILDENVNAME%

if "%~1" == "upload" goto UPLOAD

echo Cleaning up before making release...
del /f /s /q "%DISTDIR%" 1>nul 2>&1
rmdir /s /q "%DISTDIR%" 1>nul 2>&1

echo Making PyPI release...
python -m build
if errorlevel 1 goto ERROR

goto DONE


:UPLOAD
echo Uploading to PyPI
twine upload "%DISTDIR%"\*
if errorlevel 1 goto ERROR
goto DONE

:ERROR
cd %ORIGDIR%
call conda deactivate
echo Build failed!
exit /B 1

:DONE
cd %ORIGDIR%
call conda deactivate
echo Build done!
exit /B 0
