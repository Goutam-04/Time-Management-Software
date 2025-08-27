@echo off
ECHO Step 1: Running table.py to generate the master timetable...
python table.py

ECHO Step 2: Running labassign.js to assign labs...
node labassign.js

ECHO Step 3: Running timetable_resolve.js to fix conflicts...
node timetable_resolve.js

ECHO Step 4: Running json2pdf.js to convert JSON to PDF...
node json2pdf.js

ECHO All steps completed! The final file is timetable_resolved.json