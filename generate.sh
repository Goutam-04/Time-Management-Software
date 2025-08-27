#!/bin/bash

echo "Step 1: Running table.py for ~15s..."
python3 src/python/table.py &
pid=$!
sleep 15
kill -INT $pid 2>/dev/null
wait $pid 2>/dev/null

echo "Step 2: Running labassign.js..."
node src/js/labassign.js

echo "Step 3: Running timetable_resolve.js..."
node src/js/timetable_resolve.js

echo "Step 4: Running json2pdf.js..."
node src/js/json2pdf.js

echo "✅ All steps completed! The final files are in src/output and src/ (PDF)"
