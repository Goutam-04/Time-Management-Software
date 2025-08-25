// install required packages first:
// npm install xlsx fs

const xlsx = require("xlsx");
const fs = require("fs");

// Load your timetable Excel file
const workbook = xlsx.readFile("timetable.xlsx"); // put your file name here

let timetableJSON = {};

// Loop through all sheets (each sheet is a weekday)
workbook.SheetNames.forEach((sheetName) => {
  const sheet = workbook.Sheets[sheetName];

  // Convert sheet to JSON (each row becomes an object)
  const sheetData = xlsx.utils.sheet_to_json(sheet, { defval: "" });

  // Save inside timetable JSON
  timetableJSON[sheetName] = sheetData;
});

// Save output as JSON file
fs.writeFileSync("timetable.json", JSON.stringify(timetableJSON, null, 2));

console.log("✅ Timetable converted to JSON successfully! Check timetable.json file.");
