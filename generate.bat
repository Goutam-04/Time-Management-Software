@echo off
echo Step 1: Running table.py for ~15s...
start "" /b python src\python\table.py
set PID=%!%

:: Wait ~15 seconds
ping -n 16 127.0.0.1 >nul

:: Kill python process
taskkill /im python.exe /f >nul 2>&1

echo Step 2: Running labassign.js...
node src\js\labassign.js

echo Step 3: Running timetable_resolve.js...
node src\js\timetable_resolve.js

echo Step 4: Running json2pdf.js...
node src\js\json2pdf.js

echo All steps completed! The final files are in src\output and src\ (PDF)
pause
