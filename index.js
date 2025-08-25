// scheduler.js
// Node.js heuristic backtracking scheduler that mirrors your Python constraints
// Output: University_Master_Timetable.xlsx (one sheet per day, sections x slots)

const XLSX = require("xlsx");

// ---------- 1. INPUT DATA (mirrors your Python) ----------
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOTS = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];
const LAB_SLOT_STARTS = ["9-10", "11-12", "3-4"]; // 2-hour lab blocks start at these
const GROUPS = ["A", "B"];

const SECTIONS = [
  "CSE-3-1", "CSE-3-2", "AIML-3",
  "CSE-5", "IT-5",
  "CSE-7", "IT-7"
];

const SECTION_THEORY_ROOM = {
  "CSE-3-1": "B-209", "CSE-3-2": "B-209", "AIML-3": "A-32",
  "CSE-5": "B-205", "IT-5": "B-205", "CSE-7": "D-303", "IT-7": "D-303"
};

const LAB_ROOMS = ["CS105", "CS106", "CS107", "CS115", "CS204", "CS205", "CS208", "CS220"];

const SUBJECTS = {
  "CSE-3-1": [["DLD","AM"], ["DS","SK"], ["DBE","SP"], ["OOP","AVL"]],
  "CSE-3-2": [["DLD","SWP"], ["DS","GS"], ["DBE","KN"], ["OOP","SS"]],
  "AIML-3":  [["DLD","PKS"], ["DS","SKS"], ["DBE","GF4"], ["OOP","SKB"]],
  "CSE-5":   [["TOC","GF2"], ["OS","HSB"], ["AI/ML","PKD"], ["CNS","SPanda"]],
  "IT-5":    [["TOC","KKS"], ["OS","SBD"], ["AI/ML","GF3"], ["DMDW","BN"]],
  "CSE-7":   [["AI","GF5"], ["IWP","GF6"], ["IP","KN"]],
  "IT-7":    [["AI","MRS"], ["CS","AD"], ["SM","SKN"]]
};

const LABS = {
  "CSE-3-1": ["DLD Lab", "DS Lab", "DBE Lab", "OOP Lab"],
  "CSE-3-2": ["DLD Lab", "DS Lab", "DBE Lab", "OOP Lab"],
  "AIML-3":  ["DLD Lab", "DS Lab", "DBE Lab", "OOP Lab"],
  "CSE-5":   ["TOC Lab", "OS Lab", "AI/ML Lab"],
  "IT-5":    ["TOC Lab", "OS Lab", "AI/ML Lab"],
  "CSE-7":   ["Web Programming Lab"],
  "IT-7":    ["Artificial Intelligence Lab"]
};

// map lab -> subject per your rule "same-subject teacher also takes lab"
const labToSubjectMap = (labName) => {
  const explicit = {
    "Web Programming Lab": "IWP",
    "Artificial Intelligence Lab": "AI",
  };
  return explicit[labName] || labName.replace(" Lab", "");
};

const allTeachers = (() => {
  const set = new Set();
  Object.values(SUBJECTS).forEach(arr => arr.forEach(([sub, t]) => set.add(t)));
  return [...set].sort();
})();

const ALL_ROOMS = Array.from(new Set([...Object.values(SECTION_THEORY_ROOM), ...LAB_ROOMS])).sort();

// ---------- 2. SCHEDULE MODEL (in-memory) ----------
const indexSlot = (slot) => SLOTS.indexOf(slot);
const isLabStart = (slot) => LAB_SLOT_STARTS.includes(slot);

// schedule state
// timetable[day][slot] = array of entries
// entry = { type: 'theory'|'lab', section, subject, teacher, room, group? ('A'|'B'), spans?:2 }
const timetable = DAYS.map(() => SLOTS.map(() => []));

// fast lookup maps for constraints
const roomBusy = {};      // key: `${day}-${slot}-${room}` => true
const teacherBusy = {};   // key: `${day}-${slot}-${teacher}` => true
const sectionBusy = {};   // key: `${day}-${slot}-${section}-${groupOrAll}` => true

// theory per day counter to enforce <=4 per day
const theoryCountPerSectionDay = {}; // key: `${section}-${day}` => int

// counts for requirements
// theoryPlaced[section][subject] = count (must be exactly 3)
const theoryPlaced = {};
// labPlaced[section][labName][group] = boolean (must be exactly once)
const labPlaced = {};

for (const sec of SECTIONS) {
  theoryPlaced[sec] = {};
  for (const [sub] of (SUBJECTS[sec] || [])) theoryPlaced[sec][sub] = 0;
}
for (const sec of SECTIONS) {
  labPlaced[sec] = {};
  (LABS[sec] || []).forEach(l => {
    labPlaced[sec][l] = { A: false, B: false };
  });
}

// helper to get teacher for a lab in a section
function teacherForLab(section, labName) {
  const subject = labToSubjectMap(labName);
  const pair = (SUBJECTS[section] || []).find(([s]) => s === subject);
  return pair ? pair[1] : null;
}

// ---------- 3. CONSTRAINT CHECKERS ----------
function canPlaceTheory(section, subject, teacher, dayIdx, slotIdx) {
  const day = DAYS[dayIdx];
  const slot = SLOTS[slotIdx];
  const room = SECTION_THEORY_ROOM[section];
  if (!room) return false;

  // already 4 theory that day?
  const keyDay = `${section}-${day}`;
  const count = theoryCountPerSectionDay[keyDay] || 0;
  if (count >= 4) return false;

  // room busy?
  if (roomBusy[`${dayIdx}-${slotIdx}-${room}`]) return false;

  // section busy? (whole section)
  if (sectionBusy[`${dayIdx}-${slotIdx}-${section}-ALL`]) return false;

  // teacher busy?
  if (teacherBusy[`${dayIdx}-${slotIdx}-${teacher}`]) return false;

  // recess rule: if slot is 2-3 and teacher had 12-1, block
  const idx121 = indexSlot("12-1");
  const idx23 = indexSlot("2-3");
  if (slotIdx === idx23 && teacherBusy[`${dayIdx}-${idx121}-${teacher}`]) return false;

  // also if placing at 12-1, ensure not already at 2-3
  if (slotIdx === idx121 && teacherBusy[`${dayIdx}-${idx23}-${teacher}`]) return false;

  return true;
}

function placeTheory(section, subject, teacher, dayIdx, slotIdx) {
  const room = SECTION_THEORY_ROOM[section];
  timetable[dayIdx][slotIdx].push({ type: "theory", section, subject, teacher, room });

  roomBusy[`${dayIdx}-${slotIdx}-${room}`] = true;
  teacherBusy[`${dayIdx}-${slotIdx}-${teacher}`] = true;
  sectionBusy[`${dayIdx}-${slotIdx}-${section}-ALL`] = true;

  const keyDay = `${section}-${DAYS[dayIdx]}`;
  theoryCountPerSectionDay[keyDay] = (theoryCountPerSectionDay[keyDay] || 0) + 1;
  theoryPlaced[section][subject] += 1;
}

function removeTheory(section, subject, teacher, dayIdx, slotIdx) {
  const room = SECTION_THEORY_ROOM[section];
  timetable[dayIdx][slotIdx] = timetable[dayIdx][slotIdx].filter(
    e => !(e.type === "theory" && e.section === section && e.subject === subject && e.teacher === teacher && e.room === room)
  );

  delete roomBusy[`${dayIdx}-${slotIdx}-${room}`];
  delete teacherBusy[`${dayIdx}-${slotIdx}-${teacher}`];
  delete sectionBusy[`${dayIdx}-${slotIdx}-${section}-ALL`];

  const keyDay = `${section}-${DAYS[dayIdx]}`;
  theoryCountPerSectionDay[keyDay] = (theoryCountPerSectionDay[keyDay] || 1) - 1;
  theoryPlaced[section][subject] -= 1;
}

function canPlaceLab(section, labName, group, teacher, dayIdx, slotIdx, room) {
  // lab spans 2 slots: slotIdx and slotIdx+1
  if (slotIdx >= SLOTS.length - 1) return false;
  const startSlot = SLOTS[slotIdx];
  const nextSlotIdx = slotIdx + 1;
  if (!isLabStart(startSlot)) return false;

  // room free across both hours?
  if (roomBusy[`${dayIdx}-${slotIdx}-${room}`] || roomBusy[`${dayIdx}-${nextSlotIdx}-${room}`]) return false;

  // section group free both hours?
  if (sectionBusy[`${dayIdx}-${slotIdx}-${section}-${group}`] || sectionBusy[`${dayIdx}-${nextSlotIdx}-${section}-${group}`]) return false;

  // teacher free both hours?
  if (teacherBusy[`${dayIdx}-${slotIdx}-${teacher}`] || teacherBusy[`${dayIdx}-${nextSlotIdx}-${teacher}`]) return false;

  // recess rule: if any hour is 12-1 then teacher must not have 2-3 same day; and vice versa
  const idx121 = indexSlot("12-1");
  const idx23 = indexSlot("2-3");
  if ((slotIdx === idx121 || nextSlotIdx === idx121) && (teacherBusy[`${dayIdx}-${idx23}-${teacher}`])) return false;
  if ((slotIdx === idx23 || nextSlotIdx === idx23) && (teacherBusy[`${dayIdx}-${idx121}-${teacher}`])) return false;

  // parallel labs A & B same time must be different subjects:
  // if opposite group has a lab starting here with same labName, block
  const oppGroup = group === "A" ? "B" : "A";
  const entriesNow = timetable[dayIdx][slotIdx];
  const sameTimeOpp = entriesNow.find(
    e => e.type === "lab" && e.section === section && e.group === oppGroup
  );
  if (sameTimeOpp) {
    const thisSubj = labToSubjectMap(labName);
    const oppSubj = labToSubjectMap(sameTimeOpp.subject);
    if (thisSubj === oppSubj) return false;
  }

  return true;
}

function placeLab(section, labName, group, teacher, dayIdx, slotIdx, room) {
  const nextSlotIdx = slotIdx + 1;
  const entry = { type: "lab", section, subject: labName, teacher, room, group, spans: 2 };

  timetable[dayIdx][slotIdx].push(entry);
  timetable[dayIdx][nextSlotIdx].push(entry); // mirror span display (we’ll dedupe in export)

  roomBusy[`${dayIdx}-${slotIdx}-${room}`] = true;
  roomBusy[`${dayIdx}-${nextSlotIdx}-${room}`] = true;

  sectionBusy[`${dayIdx}-${slotIdx}-${section}-${group}`] = true;
  sectionBusy[`${dayIdx}-${nextSlotIdx}-${section}-${group}`] = true;

  teacherBusy[`${dayIdx}-${slotIdx}-${teacher}`] = true;
  teacherBusy[`${dayIdx}-${nextSlotIdx}-${teacher}`] = true;

  labPlaced[section][labName][group] = true;
}

function removeLab(section, labName, group, teacher, dayIdx, slotIdx, room) {
  const nextSlotIdx = slotIdx + 1;

  const filterOut = (arr) =>
    arr.filter(e => !(e.type === "lab" && e.section === section && e.subject === labName && e.teacher === teacher && e.room === room && e.group === group));

  timetable[dayIdx][slotIdx] = filterOut(timetable[dayIdx][slotIdx]);
  timetable[dayIdx][nextSlotIdx] = filterOut(timetable[dayIdx][nextSlotIdx]);

  delete roomBusy[`${dayIdx}-${slotIdx}-${room}`];
  delete roomBusy[`${dayIdx}-${nextSlotIdx}-${room}`];

  delete sectionBusy[`${dayIdx}-${slotIdx}-${section}-${group}`];
  delete sectionBusy[`${dayIdx}-${nextSlotIdx}-${section}-${group}`];

  delete teacherBusy[`${dayIdx}-${slotIdx}-${teacher}`];
  delete teacherBusy[`${dayIdx}-${nextSlotIdx}-${teacher}`];

  labPlaced[section][labName][group] = false;
}

// ---------- 4. BUILD DECISION LIST (order matters) ----------
// Place all labs first (harder), then theory occurrences (3 per subject)
function buildDecisions() {
  const decisions = [];

  // labs first
  for (const section of SECTIONS) {
    const labs = LABS[section] || [];
    for (const lab of labs) {
      for (const grp of GROUPS) {
        const teacher = teacherForLab(section, lab);
        if (!teacher) continue; // skip if mapping missing
        decisions.push({
          kind: "lab",
          section, labName: lab, group: grp, teacher
        });
      }
    }
  }

  // then theory: 3 per subject
  for (const section of SECTIONS) {
    const subs = SUBJECTS[section] || [];
    for (const [subj, teacher] of subs) {
      for (let i = 0; i < 3; i++) {
        decisions.push({
          kind: "theory",
          section, subject: subj, teacher
        });
      }
    }
  }

  // heuristic: shuffle a bit but keep labs before theory
  shuffle(decisions);
  decisions.sort((a, b) => (a.kind === "lab" && b.kind !== "lab" ? -1 : a.kind !== "lab" && b.kind === "lab" ? 1 : 0));
  return decisions;
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

// ---------- 5. BACKTRACKING SOLVER ----------
function solve() {
  const decisions = buildDecisions();
  return backtrack(0, decisions);
}

function backtrack(idx, decisions) {
  if (idx >= decisions.length) return true;

  const d = decisions[idx];

  if (d.kind === "lab") {
    // try all day/slot/lab-room
    const dayOrder = orderDaysForSection(d.section);
    for (const dayIdx of dayOrder) {
      for (let slotIdx = 0; slotIdx < SLOTS.length - 1; slotIdx++) {
        if (!isLabStart(SLOTS[slotIdx])) continue;
        // try lab rooms in random order
        const roomsOrder = [...LAB_ROOMS];
        shuffle(roomsOrder);
        for (const room of roomsOrder) {
          if (!canPlaceLab(d.section, d.labName, d.group, d.teacher, dayIdx, slotIdx, room)) continue;
          placeLab(d.section, d.labName, d.group, d.teacher, dayIdx, slotIdx, room);
          if (backtrack(idx + 1, decisions)) return true;
          removeLab(d.section, d.labName, d.group, d.teacher, dayIdx, slotIdx, room);
        }
      }
    }
    return false;
  } else {
    // theory
    const dayOrder = orderDaysForSection(d.section);
    for (const dayIdx of dayOrder) {
      // try all slots
      const slotOrder = orderSlotsForTheory();
      for (const slotIdx of slotOrder) {
        if (!canPlaceTheory(d.section, d.subject, d.teacher, dayIdx, slotIdx)) continue;
        placeTheory(d.section, d.subject, d.teacher, dayIdx, slotIdx);
        if (backtrack(idx + 1, decisions)) return true;
        removeTheory(d.section, d.subject, d.teacher, dayIdx, slotIdx);
      }
    }
    return false;
  }
}

// simple heuristics to get nicer layouts
function orderDaysForSection(/*section*/) {
  // spread across the week: Tue, Thu, Mon, Wed, Fri (just a heuristic)
  return [1, 3, 0, 2, 4];
}
function orderSlotsForTheory() {
  // prefer continuous blocks: 9-10,10-11,11-12 then 3-4,4-5 then 12-1, then 2-3
  return [0,1,2,5,6,3,4];
}

// ---------- 6. RUN ----------
const ok = solve();
if (!ok) {
  console.error("❌ No feasible solution found with current constraints/inputs.");
  process.exit(1);
}
console.log("✅ Solution found. Writing Excel…");

// ---------- 7. EXPORT TO EXCEL (one sheet per day) ----------
const wb = XLSX.utils.book_new();

for (let dayIdx = 0; dayIdx < DAYS.length; dayIdx++) {
  const day = DAYS[dayIdx];

  // build a matrix: rows = sections, cols = slots
  const header = ["Section", ...SLOTS];
  const rows = [];

  for (const section of SECTIONS) {
    const row = new Array(SLOTS.length + 1).fill("");
    row[0] = section;

    for (let slotIdx = 0; slotIdx < SLOTS.length; slotIdx++) {
      const cellEntries = timetable[dayIdx][slotIdx]
        .filter(e => e.section === section);

      if (cellEntries.length === 0) {
        row[slotIdx + 1] = "";
        continue;
      }

      // de-duplicate lab span echo (we pushed entry in both hours)
      const uniq = [];
      const seen = new Set();
      for (const e of cellEntries) {
        const key = `${e.type}-${e.section}-${e.subject}-${e.teacher}-${e.room}-${e.group || "ALL"}`;
        if (!seen.has(key)) {
          uniq.push(e);
          seen.add(key);
        }
      }

      const text = uniq.map(e => {
        const grp = e.type === "lab" ? ` (${e.group})` : "";
        return `${e.subject}${grp}\n(${e.teacher})\n${e.room}`;
      }).join("\n---\n");

      row[slotIdx + 1] = text;
    }

    rows.push(row);
  }

  const wsData = [header, ...rows];
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // widen columns a bit
  const colWidths = [{ wch: 16 }, ...SLOTS.map(() => ({ wch: 28 }))];
  ws["!cols"] = colWidths;

  // increase row height (XLSX doesn’t directly store row heights; most viewers size automatically)
  XLSX.utils.book_append_sheet(wb, ws, day);
}

XLSX.writeFile(wb, "University_Master_Timetable.xlsx");
console.log("✅ Saved: University_Master_Timetable.xlsx");

