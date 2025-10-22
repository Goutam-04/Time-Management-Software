#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  University Timetable Solver Pipeline${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if required files exist
if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ Error: config.json not found${NC}"
    exit 1
fi

if [ ! -f "data.json" ]; then
    echo -e "${RED}❌ Error: data.json not found${NC}"
    exit 1
fi

# Remove any existing updated_timetable.json to start fresh
if [ -f "updated_timetable.json" ]; then
    echo -e "${YELLOW}🗑️  Removing existing updated_timetable.json...${NC}"
    rm updated_timetable.json
fi

# Step 1: Run 3rd Semester Solver
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📚 Step 1: Running 3rd Semester Solver (solver.py)...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 solver.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: 3rd Semester Solver failed${NC}"
    exit 1
fi

if [ ! -f "updated_timetable.json" ]; then
    echo -e "${RED}❌ Error: solver.py did not create updated_timetable.json${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 3rd Semester solved successfully${NC}"

# Step 2: Run 5th Semester Solver
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📚 Step 2: Running 5th Semester Solver (5solver.py)...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 5solver.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: 5th Semester Solver failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 5th Semester solved successfully${NC}"

# Step 3: Run 7th Semester Solver
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📚 Step 3: Running 7th Semester Solver (7solver.py)...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
python3 7solver.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: 7th Semester Solver failed${NC}"
    echo -e "${YELLOW}💡 Tip: Run 'python3 conflict_analyzer.py' to diagnose the issue${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 7th Semester solved successfully${NC}"

# Step 6: Run json2pdf.js (if exists)
if [ -f "json2pdf.js" ]; then
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📄 Step 6: Running json2pdf.js...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    node json2pdf.js
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: json2pdf.js failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ PDF generation completed${NC}"

    # 🧭 Open the generated PDF in the browser
    PDF_FILE=""
    if [ -f "timetable.pdf" ]; then
        PDF_FILE="timetable.pdf"
    elif [ -f "src/timetable.pdf" ]; then
        PDF_FILE="src/timetable.pdf"
    fi

    if [ -n "$PDF_FILE" ]; then
        echo -e "${YELLOW}🌐 Opening $PDF_FILE in your browser...${NC}"
        # Cross-platform open
        if command -v xdg-open >/dev/null; then
            xdg-open "$PDF_FILE" >/dev/null 2>&1 &
        elif command -v open >/dev/null; then
            open "$PDF_FILE" >/dev/null 2>&1 &
        elif command -v start >/dev/null; then
            start "$PDF_FILE" >/dev/null 2>&1 &
        else
            echo -e "${RED}⚠️ Could not detect a method to open the PDF automatically.${NC}"
        fi
    fi
fi

# Step 7: Run json2doc.js (if exists)
if [ -f "json2doc.js" ]; then
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📄 Step 7: Running json2doc.js...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    node json2doc.js
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: json2doc.js failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docx generation completed${NC}"
fi

# Final summary
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 All steps completed successfully!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${GREEN}✅ Generated files:${NC}"
echo -e "   • updated_timetable.json (complete solution)"

if [ -d "src/output" ]; then
    echo -e "   • Output files in: ${YELLOW}src/output/${NC}"
fi

if [ -f "timetable.pdf" ] || [ -f "src/timetable.pdf" ]; then
    echo -e "   • PDF timetable generated"
fi

if [ -f "Timetable.docx" ] || [ -f "src/Timetable.docx" ]; then
    echo -e "   • Docx timetable generated"
fi

echo -e "\n${YELLOW}💡 Tip: If the 7th semester solver fails, run:${NC}"
echo -e "   ${BLUE}python3 conflict_analyzer.py${NC}"
echo -e "\n"
