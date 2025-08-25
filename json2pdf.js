const fs = require("fs");
const PdfPrinter = require("pdfmake");

// Use built-in fonts (no Roboto issues)
const fonts = {
  Helvetica: {
    normal: "Helvetica",
    bold: "Helvetica-Bold",
    italics: "Helvetica-Oblique",
    bolditalics: "Helvetica-BoldOblique",
  },
};
const printer = new PdfPrinter(fonts);

const timetable = JSON.parse(fs.readFileSync("University_Master_Timetable.json", "utf8"));
const timeSlots = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];

// Build table for one day
function buildDayTable(day, data) {
  const headerRow = [{ text: "Section", style: "tableHeader" }, ...timeSlots.map(s => ({ text: s, style: "tableHeader" }))];
  const body = [headerRow];

  data.forEach((section) => {
    const row = [{ text: section.section, style: "sectionCell" }];
    timeSlots.forEach((slot) => {
      const entries = section[slot] || [];
      if (entries.length === 0) {
        row.push("");
      } else if (entries.length === 1) {
        const e = entries[0];
        row.push({
          stack: [
            { text: `${e.subject} (${e.teacher})`, bold: true },
            { text: `Room: ${e.room}` },
            e.isLab ? { text: `Group: ${e.group}`, italics: true } : {}
          ],
          fillColor: e.isLab ? "#fff176" : null, // yellow for labs
          alignment: "center",
          margin: [2, 4, 2, 4],
        });
      } else {
        // Multiple entries (parallel labs etc.)
        row.push({
          table: {
            widths: ["*"],
            body: entries.map((e) => [
              {
                stack: [
                  { text: `${e.subject} (${e.teacher})`, bold: true },
                  { text: `Room: ${e.room}` },
                  e.isLab ? { text: `Group: ${e.group}`, italics: true } : {}
                ],
                fillColor: e.isLab ? "#fff176" : null,
                alignment: "center",
                margin: [2, 4, 2, 4],
              }
            ]),
          },
          layout: {
            hLineWidth: () => 0.5,
            vLineWidth: () => 0.5,
            hLineColor: () => "#aaa",
            vLineColor: () => "#aaa",
          },
        });
      }
    });
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

function makeDocument() {
  const content = [];
  Object.keys(timetable).forEach((day, idx) => {
    if (idx > 0) content.push({ text: "", pageBreak: "before" });

    content.push({ text: day, style: "dayHeader", margin: [0, 0, 0, 10] });
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
pdfDoc.pipe(fs.createWriteStream("Timetable.pdf"));
pdfDoc.end();

console.log("✅ Timetable PDF generated with lab colors, groups, and grid lines!");
