const fs = require("fs");
const PdfPrinter = require("pdfmake");

// Built-in fonts
const fonts = {
  Helvetica: {
    normal: "Helvetica",
    bold: "Helvetica-Bold",
    italics: "Helvetica-Oblique",
    bolditalics: "Helvetica-BoldOblique",
  },
};
const printer = new PdfPrinter(fonts);

const timetable = JSON.parse(fs.readFileSync("./updated_timetable.json", "utf8"));
const timeSlots = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];

// Helper: handle undefined gracefully
function safe(v) {
  return v === undefined || v === null ? "" : String(v);
}

/**
 * Check if entry is actually empty/unassigned
 */
function isEmpty(entry) {
  if (!entry) return true;
  const status = safe(entry.status).toLowerCase();
  // Consider Free, To Be Assigned, or missing as empty
  return status === "free" || status === "to be assigned" || status === "" || !entry.subject;
}

/**
 * Detect if this entry represents a lab.
 */
function isLabEntry(entry) {
  const subj = safe(entry.subject).toLowerCase();
  return subj.includes("lab");
}

/**
 * Parse a combined lab entry like:
 * "subject": "DS Lab (G-A) / DBE Lab (G-B)"
 * "teacher": "SKS / GF4"
 * "room": "CS105 / CS107"
 * into two separate lab objects.
 */
function parseLabEntry(entry) {
  const subjects = safe(entry.subject).split(" / ");
  const teachers = safe(entry.teacher).split(" / ");
  const rooms = safe(entry.room).split(" / ");

  const labs = subjects.map((subj, i) => ({
    subject: safe(subj.trim()),
    teacher: safe(teachers[i] || "").trim(),
    room: safe(rooms[i] || "").trim(),
    isLab: true,
  }));
  return labs;
}

/**
 * Check if two entries are identical (for 2-hour labs)
 */
function areEntriesEqual(entries1, entries2) {
  if (!entries1 || !entries2) return false;
  return JSON.stringify(entries1) === JSON.stringify(entries2);
}

/**
 * Creates a content cell for one slot
 */
function createCellContent(entries) {
  // Return completely blank cell if empty
  if (!entries || entries.length === 0) {
    return { text: "", margin: [2, 4, 2, 4] };
  }

  const e = entries[0];
  
  // Return completely blank cell if status is Free or To Be Assigned
  if (isEmpty(e)) {
    return { text: "", margin: [2, 4, 2, 4] };
  }

  if (isLabEntry(e)) {
    const labs = parseLabEntry(e);

    // If two parallel labs, show them in horizontal split
    if (labs.length > 1) {
      return {
        table: {
          widths: ["*"],
          body: labs.map((lab) => [
            {
              stack: [
                { text: `${safe(lab.subject)}`, bold: true, fontSize: 8 },
                { text: `${safe(lab.teacher)}`, italics: true, fontSize: 7 },
                { text: `${safe(lab.room)}`, fontSize: 7 },
              ],
              fillColor: "#fff8b3", // light yellow
              alignment: "center",
              margin: [2, 3, 2, 3],
              border: [false, false, false, false],
            },
          ]),
        },
        layout: {
          hLineWidth: (i, node) =>
            i > 0 && i < node.table.body.length ? 0.5 : 0,
          vLineWidth: () => 0,
          hLineColor: () => "#aaa",
        },
      };
    }

    // Single lab
    const lab = labs[0];
    return {
      stack: [
        { text: `${safe(lab.subject)}`, bold: true, fontSize: 8 },
        { text: `${safe(lab.teacher)}`, italics: true, fontSize: 7 },
        { text: `${safe(lab.room)}`, fontSize: 7 },
      ],
      fillColor: "#fff8b3",
      alignment: "center",
      margin: [2, 3, 2, 3],
    };
  }

  // Non-lab class
  return {
    stack: [
      { text: `${safe(e.subject)}`, bold: true, fontSize: 8 },
      { text: `${safe(e.teacher)}`, fontSize: 7 },
      { text: `${safe(e.room)}`, fontSize: 7 },
    ],
    alignment: "center",
    margin: [2, 3, 2, 3],
  };
}

/**
 * Build table for each day
 */
function buildDayTable(day, data) {
  const headerRow = [
    { text: "Section", style: "tableHeader" },
    ...timeSlots.map((s) => ({ text: s, style: "tableHeader" })),
  ];
  const body = [headerRow];

  data.forEach((section) => {
    const row = [{ text: safe(section.section), style: "sectionCell" }];

    for (let i = 0; i < timeSlots.length; i++) {
      const slot = timeSlots[i];
      const nextSlot = timeSlots[i + 1];

      const entries = section[slot] || [];
      const nextEntries = section[nextSlot] || [];

      const e = entries[0];

      // Handle 2-hour lab merge (only if not empty)
      if (
        e &&
        !isEmpty(e) &&
        isLabEntry(e) &&
        areEntriesEqual(entries, nextEntries)
      ) {
        const cell = createCellContent(entries);
        cell.colSpan = 2;
        row.push(cell);
        row.push({}); // placeholder for merged cell
        i++;
        continue;
      }

      row.push(createCellContent(entries));
    }

    body.push(row);
  });

  return {
    table: {
      headerRows: 1,
      widths: [60, ...timeSlots.map(() => "*")],
      body,
    },
    layout: {
      hLineWidth: () => 0.5,
      vLineWidth: (i, node) => 0.5,
      hLineColor: () => "#444",
      vLineColor: () => "#444",
      paddingTop: () => 4,
      paddingBottom: () => 4,
      paddingLeft: () => 3,
      paddingRight: () => 3,
    },
  };
}

/**
 * Generate the full PDF document
 */
function makeDocument() {
  const content = [];
  
  Object.keys(timetable).forEach((day, idx) => {
    // Start each day on a new page (except the first)
    if (idx > 0) {
      content.push({ text: "", pageBreak: "before" });
    }
    
    // Day header
    content.push({
      text: safe(day),
      style: "dayHeader",
      margin: [0, 10, 0, 15],
    });
    
    // Day table
    content.push(buildDayTable(day, timetable[day]));
  });

  return {
    content,
    styles: {
      dayHeader: {
        fontSize: 16,
        bold: true,
        alignment: "center",
        color: "#333",
      },
      tableHeader: { 
        bold: true, 
        fillColor: "#d0d0d0", 
        alignment: "center",
        fontSize: 9,
      },
      sectionCell: { 
        bold: true, 
        alignment: "center",
        fontSize: 8,
      },
    },
    defaultStyle: {
      font: "Helvetica",
      fontSize: 8,
    },
    pageOrientation: "landscape",
    pageSize: "A4",
    pageMargins: [30, 40, 30, 40],
  };
}

const pdfDoc = printer.createPdfKitDocument(makeDocument());
pdfDoc.pipe(fs.createWriteStream("./timetable.pdf"));
pdfDoc.end();

console.log("✅ Timetable PDF generated with:");
console.log("   • Blank cells for Free/Unassigned slots");
console.log("   • Each day on a single page");
console.log("   • Merged 2-hour yellow lab blocks");