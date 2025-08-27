#!/bin/bash
# This script automates the timetable generation process

echo "Step 1: Running table.py to generate the master timetable..."
python table.py

echo "Step 2: Running labassign.js to assign labs..."
node labassign.js

echo "Step 3: Running timetable_resolve.js to fix conflicts..."
node timetable_resolve.js

echo "Step 4: Running json2pdf.js to convert JSON to PDF..."
node json2pdf.js

echo "✅ All steps completed! The final file is timetable_resolved.json"