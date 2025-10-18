const fs = require("fs");
const PdfPrinter = require("pdfmake");

// Use built-in fonts
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

/**
 * Helper: if a value is undefined, null, or not a string/number, return ""
 */
function safe(v) {
  return v === undefined || v === null ? "" : String(v);
}

/**
 * Check if two class entries are identical (for merging labs)
 */
function areEntriesEqual(entries1, entries2) {
  if (!entries1 || !entries2 || entries1.length !== entries2.length) return false;
  return JSON.stringify(entries1) === JSON.stringify(entries2);
}

/**
 * Build table for one day
 */
function buildDayTable(day, data) {
  const headerRow = [{ text: "Section", style: "tableHeader" }, ...timeSlots.map(s => ({ text: s, style: "tableHeader" }))];
  const body = [headerRow];

  data.forEach((section) => {
    const row = [{ text: safe(section.section), style: "sectionCell" }];

    for (let i = 0; i < timeSlots.length; i++) {
      const slot = timeSlots[i];
      const nextSlot = timeSlots[i + 1];

      const entries = section[slot] || [];
      const nextEntries = section[nextSlot] || [];

      // Merge 2-hour labs
      if (entries.length > 0 && entries[0].isLab && areEntriesEqual(entries, nextEntries)) {
        const cellContent = createCellContent(entries);
        cellContent.colSpan = 2;
        row.push(cellContent);
        row.push({});
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
      widths: [70, ...timeSlots.map(() => "*")],
      body,
    },
    layout: {
      hLineWidth: () => 0.5,
      vLineWidth: () => 0.5,
      hLineColor: () => "#444",
      vLineColor: () => "#444",
      paddingTop: () => 6,
      paddingBottom: () => 6,
    },
  };
}

/**
 * Creates a single cell's content safely
 */
function createCellContent(entries) {
  if (!entries || entries.length === 0) return "";

  if (entries.length === 1) {
    const e = entries[0];
    return {
      stack: [
        { text: `${safe(e.subject)} (${safe(e.teacher)})`, bold: true },
        { text: `Room: ${safe(e.room)}` },
        e.isLab ? { text: `Group: ${safe(e.group)}`, italics: true } : {},
      ],
      fillColor: e.isLab ? "#fff176" : null,
      alignment: "center",
      margin: [2, 4, 2, 4],
    };
  }

  // For multiple parallel labs (nested small table)
  return {
    table: {
      widths: ["*"],
      body: entries.map((e) => [
        {
          stack: [
            { text: `${safe(e.subject)} (${safe(e.teacher)})`, bold: true },
            { text: `Room: ${safe(e.room)}` },
            e.isLab ? { text: `Group: ${safe(e.group)}`, italics: true } : {},
          ],
          fillColor: e.isLab ? "#fff176" : null,
          alignment: "center",
          margin: [2, 4, 2, 4],
          border: [false, false, false, false],
        },
      ]),
    },
    layout: {
      hLineWidth: (i, node) => (i > 0 && i < node.table.body.length ? 0.5 : 0),
      vLineWidth: () => 0,
      hLineColor: () => "#aaa",
      paddingTop: (i) => (i === 0 ? 0 : 4),
      paddingBottom: (i, node) => (i === node.table.body.length - 1 ? 0 : 4),
    },
  };
}

/**
 * Generate the full PDF document
 */
function makeDocument() {
  const content = [];
  Object.keys(timetable).forEach((day, idx) => {
    if (idx > 0) content.push({ text: "", pageBreak: "before" });
    content.push({ text: safe(day), style: "dayHeader", margin: [0, 0, 0, 10] });
    content.push(buildDayTable(day, timetable[day]));
  });

  return {
    content,
    styles: {
      dayHeader: { fontSize: 18, bold: true, alignment: "center", margin: [0, 0, 0, 12] },
      tableHeader: { bold: true, fillColor: "#e0e0e0", alignment: "center" },
      sectionCell: { bold: true, alignment: "center" },
    },
    defaultStyle: {
      font: "Helvetica",
      fontSize: 9,
    },
    pageOrientation: "landscape",
  };
}

const pdfDoc = printer.createPdfKitDocument(makeDocument());
pdfDoc.pipe(fs.createWriteStream("./GG.pdf"));
pdfDoc.end();

console.log("✅ Timetable PDF generated with merged labs and no undefined fields!");
