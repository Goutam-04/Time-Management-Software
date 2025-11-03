```
time-management-software/
├── data/
│   ├── config.json                 # Main solver configuration
│   ├── data.json                   # Base timetable structure (input for 3rd sem solver)
│   ├── not-available.json          # Teacher unavailability rules
│   └── raw_inputs/                 # (Optional) Place for original TT files
│       ├── third-btech-tt.json
│       ├── fifth-btech-tt.json
│       ├── first-mtech-tt.json
│       ├── first-year-tt.json
│       ├── rooms.json
│       ├── sessional-assign.json
│       └── workload-distrib.json
├── outputs/                        # All generated files
│   ├── updated_timetable.json      # Final JSON output from the solver pipeline
│   ├── timetable.pdf               # Generated PDF
│   └── Timetable.docx              # Generated Word Document
├── src/                            # Python source code package
│   ├── __init__.py
│   ├── solver/                     # Core Python solver package
│   │   ├── __init__.py
│   │   ├── solver_3rd.py           # (Was solver.py)
│   │   ├── solver_5th.py           # (Was 5solver.py)
│   │   └── solver_7th.py           # (Was 7solver.py)
│   └── diagnostics/                # Python-based diagnostic tools
│       ├── __init__.py
│       ├── conflict_analyzer.py    # (Was dd.py)
│       ├── diagnose_conflicts.py   # (Was diagnose.py)
│       └── test_unavailability.py  # (Was test.py)
├── scripts/                        # All Node.js helper scripts
│   ├── data_generator.js           # (Was dataGeneration.js)
│   ├── overlap_fixer.js            # (Was overlapFix.js)
│   ├── export_to_pdf.js            # (Was json2pdf.js)
│   └── export_to_doc.js            # (Was json2doc.js)
├── web_viewer/                     # Standalone web UI for viewing results
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── updated_timetable.json      # (This should be copied from /outputs)
├── .gitignore
├── package.json                    # For all Node.js dependencies
├── requirements.txt                # For all Python dependencies (ortools)
├── generate.sh                     # Main execution script (Linux/macOS)
└── generate.bat                    # Main execution script (Windows)

```