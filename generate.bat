@echo off
cls

:: ----------------------------------------
:: Title & Color Setup
:: ----------------------------------------
color 07
echo ========================================
echo   University Timetable Solver Pipeline
echo ========================================
echo.

:: ----------------------------------------
:: File & Directory Paths
:: ----------------------------------------
SET "CONFIG_FILE=data\config.json"
SET "DATA_FILE=data\data.json"
SET "UNAVAIL_FILE=data\not-available.json"

SET "OUTPUT_DIR=outputs"
SET "OUTPUT_JSON=outputs\updated_timetable.json"
SET "OUTPUT_PDF=outputs\timetable.pdf"
SET "OUTPUT_DOCX=outputs\Timetable.docx"

SET "WEB_DIR=web"
SET "WEB_JSON=web\updated_timetable.json"

:: ----------------------------------------
:: Phase 0: Pre-run Checks & Cleanup
:: ----------------------------------------
echo --- Phase 0: Pre-run Checks & Cleanup ---

:: Check for critical input files
IF NOT EXIST "%CONFIG_FILE%" (
    echo [ERROR] %CONFIG_FILE% not found. Cannot continue.
    goto :eof
)
IF NOT EXIST "%DATA_FILE%" (
    echo [ERROR] %DATA_FILE% not found. Cannot continue.
    goto :eof
)
IF NOT EXIST "%UNAVAIL_FILE%" (
    echo [WARNING] %UNAVAIL_FILE% not found. Teacher unavailability rules may not be applied.
)
echo [SUCCESS] Critical input files found.

:: Check for pre-assigned conflicts in data.json
echo [INFO] Running pre-check for conflicts in %DATA_FILE%...
node scripts\overlap_fixer.js
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pre-check failed. Please fix conflicts in %DATA_FILE% before continuing.
    goto :eof
)
echo [SUCCESS] Pre-check passed. No initial conflicts found.
echo.

:: Create/clean output directory
IF NOT EXIST "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
echo [INFO] Cleaning up old output files from %OUTPUT_DIR%...
IF EXIST "%OUTPUT_JSON%" del "%OUTPUT_JSON%"
IF EXIST "%OUTPUT_PDF%" del "%OUTPUT_PDF%"
IF EXIST "%OUTPUT_DOCX%" del "%OUTPUT_DOCX%"

:: ----------------------------------------
:: Phase 1: Python Solver Pipeline
:: ----------------------------------------
echo.
echo --- Phase 1: Running Python Solver Pipeline ---

echo Step 1.1: Running 3rd Sem Solver (src\solver\solver_3rd.py)...
python src\solver\solver_3rd.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 3rd Semester Solver failed.
    goto :eof
)
IF NOT EXIST "%OUTPUT_JSON%" (
    echo [ERROR] solver_3rd.py did not create %OUTPUT_JSON%
    goto :eof
)
echo [SUCCESS] 3rd Semester solved successfully.
echo.

echo Step 1.2: Running 5th Sem Solver (src\solver\solver_5th.py)...
python src\solver\solver_5th.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 5th Semester Solver failed.
    goto :eof
)
echo [SUCCESS] 5th Semester solved successfully.
echo.

echo Step 1.3: Running 7th Sem Solver (src\solver\solver_7th.py)...
python src\solver\solver_7th.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 7th Semester Solver failed.
    echo [TIP] Run 'python src\diagnostics\conflict_analyzer.py' to diagnose the issue.
    goto :eof
)
echo [SUCCESS] 7th Semester solved successfully.
echo.

:: ----------------------------------------
:: Phase 2: Post-run Diagnostics
:: ----------------------------------------
echo --- Phase 2: Post-run Diagnostics ---
echo Step 2.1: Testing final output against unavailability rules...
python src\diagnostics\test_unavailability.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Unavailability test failed! The generated timetable has violations.
    goto :eof
)
echo [SUCCESS] Unavailability test passed. No violations found.
echo.

:: ----------------------------------------
:: Phase 3: Export & Web Prep
:: ----------------------------------------
echo --- Phase 3: Exporting Files & Preparing Web Viewer ---

echo Step 3.1: Generating PDF (scripts\export_to_pdf.js)...
node scripts\export_to_pdf.js
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PDF generation failed.
    goto :eof
)
echo [SUCCESS] PDF generation complete (%OUTPUT_PDF%).
echo.

echo Step 3.2: Generating DOCX (scripts\export_to_doc.js)...
node scripts\export_to_doc.js
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] DOCX generation failed.
    goto :eof
)
echo [SUCCESS] DOCX generation complete (%OUTPUT_DOCX%).
echo.

echo Step 3.3: Copying final JSON to web viewer...
copy /Y "%OUTPUT_JSON%" "%WEB_JSON%" > nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy %OUTPUT_JSON% to %WEB_DIR%\
    goto :eof
)
echo [SUCCESS] Final JSON copied to %WEB_DIR%\
echo.

:: ----------------------------------------
:: Phase 4: Final Summary
:: ----------------------------------------
echo ========================================
echo  All steps completed successfully!
echo ========================================
echo    . Final Timetable: %OUTPUT_JSON%
echo    . Viewable PDF:    %OUTPUT_PDF%
echo    . Viewable DOCX:   %OUTPUT_DOCX%
echo.
echo To view the interactive timetable, open this file in your browser:
echo     %WEB_DIR%\index.html
echo.
pause