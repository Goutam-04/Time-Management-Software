#!/bin/bash

# ----------------------------------------
# Color Codes for Output
# ----------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  University Timetable Solver Pipeline${NC}"
echo -e "${BLUE}========================================${NC}\n"

# ----------------------------------------
# File & Directory Paths
# ----------------------------------------
CONFIG_FILE="data/config.json"
DATA_FILE="data/data.json"
UNAVAIL_FILE="data/not-available.json"

OUTPUT_DIR="outputs"
OUTPUT_JSON="outputs/updated_timetable.json"
OUTPUT_PDF="outputs/timetable.pdf"
OUTPUT_DOCX="outputs/Timetable.docx"

WEB_DIR="web"
WEB_JSON="web/updated_timetable.json"

# ----------------------------------------
# Phase 0: Pre-run Checks & Cleanup
# ----------------------------------------
echo -e "${CYAN}--- Phase 0: Pre-run Checks & Cleanup ---${NC}"

# Check for critical input files
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Error: $CONFIG_FILE not found. Cannot continue.${NC}"
    exit 1
fi
if [ ! -f "$DATA_FILE" ]; then
    echo -e "${RED}❌ Error: $DATA_FILE not found. Cannot continue.${NC}"
    exit 1
fi
if [ ! -f "$UNAVAIL_FILE" ]; then
    echo -e "${YELLOW}⚠️ Warning: $UNAVAIL_FILE not found. Teacher unavailability rules may not be applied.${NC}"
fi
echo -e "${GREEN}✅ Critical input files found.${NC}"

# Check for pre-assigned conflicts in data.json
echo -e "${YELLOW}🔍 Running pre-check for conflicts in $DATA_FILE...${NC}"
node scripts/overlap_fixer.js
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Pre-check failed. Please fix conflicts in $DATA_FILE before continuing.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Pre-check passed. No initial conflicts found.${NC}\n"

# Create/clean output directory
mkdir -p "$OUTPUT_DIR"
echo -e "${YELLOW}🗑️  Cleaning up old output files from $OUTPUT_DIR/...${NC}"
rm -f "$OUTPUT_JSON" "$OUTPUT_PDF" "$OUTPUT_DOCX"

# ----------------------------------------
# Phase 1: Python Solver Pipeline
# ----------------------------------------
echo -e "${CYAN}--- Phase 1: Running Python Solver Pipeline ---${NC}"

echo -e "${BLUE}Step 1.1: Running 3rd Sem Solver (src/solver/solver_3rd.py)...${NC}"
python3 src/solver/solver_3rd.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: 3rd Semester Solver failed.${NC}"
    exit 1
fi
if [ ! -f "$OUTPUT_JSON" ]; then
    echo -e "${RED}❌ Error: solver_3rd.py did not create $OUTPUT_JSON${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 3rd Semester solved successfully.${NC}\n"

echo -e "${BLUE}Step 1.2: Running 5th Sem Solver (src/solver/solver_5th.py)...${NC}"
python3 src/solver/solver_5th.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: 5th Semester Solver failed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 5th Semester solved successfully.${NC}\n"

echo -e "${BLUE}Step 1.3: Running 7th Sem Solver (src/solver/solver_7th.py)...${NC}"
python3 src/solver/solver_7th.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: 7th Semester Solver failed.${NC}"
    echo -e "${YELLOW}💡 Tip: Run 'python3 src/diagnostics/conflict_analyzer.py' to diagnose the issue.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 7th Semester solved successfully.${NC}\n"

# ----------------------------------------
# Phase 2: Post-run Diagnostics
# ----------------------------------------
echo -e "${CYAN}--- Phase 2: Post-run Diagnostics ---${NC}"
echo -e "${BLUE}Step 2.1: Testing final output against unavailability rules...${NC}"
python3 src/diagnostics/test_unavailability.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Unavailability test failed! The generated timetable has violations.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Unavailability test passed. No violations found.${NC}\n"

# ----------------------------------------
# Phase 3: Export & Web Prep
# ----------------------------------------
echo -e "${CYAN}--- Phase 3: Exporting Files & Preparing Web Viewer ---${NC}"

echo -e "${BLUE}Step 3.1: Generating PDF (scripts/export_to_pdf.js)...${NC}"
node scripts/export_to_pdf.js
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: PDF generation failed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ PDF generation complete ($OUTPUT_PDF).${NC}\n"

echo -e "${BLUE}Step 3.2: Generating DOCX (scripts/export_to_doc.js)...${NC}"
node scripts/export_to_doc.js
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: DOCX generation failed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ DOCX generation complete ($OUTPUT_DOCX).${NC}\n"

echo -e "${BLUE}Step 3.3: Copying final JSON to web viewer...${NC}"
cp "$OUTPUT_JSON" "$WEB_JSON"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to copy $OUTPUT_JSON to $WEB_DIR/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Final JSON copied to $WEB_DIR/${NC}\n"

# ----------------------------------------
# Phase 4: Final Summary
# ----------------------------------------
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 All steps completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "   • Final Timetable: ${YELLOW}$OUTPUT_JSON${NC}"
echo -e "   • Viewable PDF:    ${YELLOW}$OUTPUT_PDF${NC}"
echo -e "   • Viewable DOCX:   ${YELLOW}$OUTPUT_DOCX${NC}"
echo -e "\n${GREEN}To view the interactive timetable, open this file in your browser:${NC}"
echo -e "${CYAN}    $WEB_DIR/index.html${NC}\n"