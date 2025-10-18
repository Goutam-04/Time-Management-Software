const fs = require("fs");
const { Document, Packer, Paragraph, Table, TableRow, TableCell, WidthType, TextRun, ShadingType, AlignmentType } = require("docx");

// Load timetable data
const timetable = JSON.parse(fs.readFileSync("./updated_timetable.json", "utf8"));
const timeSlots = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];

function safe(v) {
  return v === undefined || v === null ? "" : String(v);
}

function isLabEntry(entry) {
  const subj = safe(entry.subject).toLowerCase();
  return subj.includes("lab");
}

function parseLabEntry(entry) {
  const subjects = safe(entry.subject).split(" / ");
  const teachers = safe(entry.teacher).split(" / ");
  const rooms = safe(entry.room).split(" / ");
  return subjects.map((s, i) => ({
    subject: safe(s.trim()),
    teacher: safe(teachers[i] || ""),
    room: safe(rooms[i] || ""),
    isLab: true,
  }));
}

function areEntriesEqual(entries1, entries2) {
  if (!entries1 || !entries2) return false;
  return JSON.stringify(entries1) === JSON.stringify(entries2);
}

function createCellContent(entries) {
  if (!entries || entries.length === 0) return [new Paragraph("")];

  const e = entries[0];
  const isLab = isLabEntry(e);

  if (isLab) {
    const labs = parseLabEntry(e);
    const paras = [];

    for (const lab of labs) {
      paras.push(
        new Paragraph({
          children: [
            new TextRun({ text: lab.subject, bold: true }),
            new TextRun({ text: ` (${lab.teacher})`, italics: true }),
          ],
          alignment: AlignmentType.CENTER,
        }),
        new Paragraph({
          text: `Room: ${lab.room}`,
          alignment: AlignmentType.CENTER,
        })
      );
    }

    return [
      new Table({
        width: { size: 100, type: WidthType.PERCENTAGE },
        rows: labs.map(
          (lab) =>
            new TableRow({
              children: [
                new TableCell({
                  shading: { fill: "FFF8B3", type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({
                      alignment: AlignmentType.CENTER,
                      children: [
                        new TextRun({ text: lab.subject, bold: true }),
                        new TextRun({ text: ` (${lab.teacher})`, italics: true }),
                      ],
                    }),
                    new Paragraph({
                      text: `Room: ${lab.room}`,
                      alignment: AlignmentType.CENTER,
                    }),
                  ],
                }),
              ],
            })
        ),
      }),
    ];
  }

  // Non-lab class
  return [
    new Paragraph({
      children: [new TextRun({ text: `${safe(e.subject)}`, bold: true })],
      alignment: AlignmentType.CENTER,
    }),
    new Paragraph({
      text: `${safe(e.teacher)}`,
      alignment: AlignmentType.CENTER,
    }),
    new Paragraph({
      text: `Room: ${safe(e.room)}`,
      alignment: AlignmentType.CENTER,
    }),
  ];
}

function buildDayTable(day, data) {
  const headerRow = new TableRow({
    children: [
      new TableCell({ children: [new Paragraph({ text: "Section", bold: true })] }),
      ...timeSlots.map(
        (slot) => new TableCell({ children: [new Paragraph({ text: slot, bold: true, alignment: AlignmentType.CENTER })] })
      ),
    ],
  });

  const bodyRows = data.map((section) => {
    const cells = [
      new TableCell({
        children: [new Paragraph({ text: safe(section.section), bold: true, alignment: AlignmentType.CENTER })],
      }),
    ];

    for (let i = 0; i < timeSlots.length; i++) {
      const slot = timeSlots[i];
      const nextSlot = timeSlots[i + 1];
      const entries = section[slot] || [];
      const nextEntries = section[nextSlot] || [];

      const e = entries[0];

      if (e && isLabEntry(e) && areEntriesEqual(entries, nextEntries)) {
        cells.push(
          new TableCell({
            columnSpan: 2,
            shading: { fill: "FFF8B3", type: ShadingType.CLEAR },
            children: createCellContent(entries),
          })
        );
        i++;
        continue;
      }

      cells.push(
        new TableCell({
          children: createCellContent(entries),
        })
      );
    }

    return new TableRow({ children: cells });
  });

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [headerRow, ...bodyRows],
  });
}

async function generateDoc() {
  const doc = new Document({ sections: [] });

  Object.keys(timetable).forEach((day) => {
    doc.addSection({
      children: [
        new Paragraph({
          text: day,
          heading: "Heading1",
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
        }),
        buildDayTable(day, timetable[day]),
        new Paragraph({ text: "", pageBreakBefore: true }),
      ],
    });
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync("Timetable.docx", buffer);
  console.log("✅ Timetable.docx generated successfully!");
}

generateDoc();
