@echo off
set TRANSLATION_FILE=translations\pyfiles.ts

rem Check if the translation file exists, if not, create it
if not exist "%TRANSLATION_FILE%" (
    echo Creating an empty translation file...
    copy NUL "%TRANSLATION_FILE%" > nul
    if errorlevel 1 (
        echo Failed to create the translation file.
        exit /b 1
    )
    echo Empty translation file created successfully.
)

rem Loop through each .py file recursively and append to the translation file
for /R %%i in (*.py) do (
    echo Processing: %%i
    D:\anaconda3\pylupdate5.bat "%%i" -ts "%TRANSLATION_FILE%" >> "%TRANSLATION_FILE%"
    if errorlevel 1 (
        echo Error encountered while processing: %%i
    ) else (
        echo Successfully updated translation file.
    )
)
