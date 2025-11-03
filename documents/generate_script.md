
We designed the `generate.sh` script to be a complete, "one-click" solution for running the entire project. It's not just a list of commands; it's a smart pipeline that checks for errors, runs diagnostics, and manages the flow of data.

Here is a breakdown of exactly what it does, phase by phase.

### Phase 0: Pre-run Checks & Cleanup

This phase makes sure the script can run successfully before it even starts the complex parts.

1.  **Color Codes & Paths:** It first defines variables for terminal colors (like `RED`, `GREEN`) to make the output easy to read. It also defines variables for all important file paths (like `CONFIG_FILE`, `OUTPUT_JSON`) so they can be easily changed in one place.

2.  **Check for Critical Files:** It checks if `data/config.json` and `data/data.json` exist. If either is missing, the script stops immediately with an error (`exit 1`) because the solvers cannot run.

3.  **Run Pre-Diagnostics:** This is a key step. It runs your `scripts/overlap_fixer.js` script to check your *input file* (`data/data.json`) for any pre-assigned conflicts (like a teacher scheduled in two rooms at the same time). If it finds a conflict, the script stops, telling you to fix your data first.

4.  **Create & Clean `outputs/`:** It creates the `outputs/` directory if it doesn't exist (`mkdir -p`). It then deletes any old files (`.json`, `.pdf`, `.docx`) from previous runs to prevent confusion.

### Phase 1: Python Solver Pipeline

This is the core logic of the project. It runs your Python solvers **in a specific sequence**, where the output of one becomes the input for the next.

1.  **Step 1.1 (3rd Sem):** Runs `src/solver/solver_3rd.py`.

    -   **Input:** `data/data.json` (the base skeleton)

    -   **Output:** Creates the first version of `outputs/updated_timetable.json` (now containing the 3rd sem schedule).

    -   **Error Check:** If this script fails or doesn't create the output file, the entire pipeline stops.

2.  **Step 1.2 (5th Sem):** Runs `src/solver/solver_5th.py`.

    -   **Input:** `outputs/updated_timetable.json` (the file just created with the 3rd sem data).

    -   **Output:** *Overwrites* `outputs/updated_timetable.json` with a new version that now includes both 3rd and 5th sem schedules.

    -   **Error Check:** Stops the pipeline if this solver fails.

3.  **Step 1.3 (7th Sem):** Runs `src/solver/solver_7th.py`.

    -   **Input:** `outputs/updated_timetable.json` (with 3rd + 5th sem data).

    -   **Output:** *Overwrites* `outputs/updated_timetable.json` one last time with the complete, fully solved timetable (3rd + 5th + 7th sem).

    -   **Error Check:** Stops if it fails, and provides a tip to run the `conflict_analyzer.py` script.

### Phase 2: Post-run Diagnostics

After the solvers are done, this phase *validates* the final result.

1.  **Step 2.1 (Test Unavailability):** Runs `src/diagnostics/test_unavailability.py`.

    -   This script reads the final `outputs/updated_timetable.json` and checks it against your `data/not-available.json` file.

    -   If it finds even one violation (e.g., a teacher is scheduled on a day they marked as unavailable), the script stops. This ensures you don't generate a PDF for a faulty timetable.

### Phase 3: Export & Web Prep

Once the final JSON is created and validated, this phase generates all the user-friendly files.

1.  **Step 3.1 (Generate PDF):** Runs `scripts/export_to_pdf.js` to create `outputs/timetable.pdf`.

2.  **Step 3.2 (Generate DOCX):** Runs `scripts/export_to_doc.js` to create `outputs/Timetable.docx`.

3.  **Step 3.3 (Copy to Web):** This is the crucial step for your web viewer. It copies the final, validated `outputs/updated_timetable.json` directly into the `web/` folder, so that `web/index.html` and `web/script.js` can access it.

### Phase 4: Final Summary

Finally, the script prints a success message and lists the exact locations of all the important files it created, telling you to open `web/index.html` in your browser.