const timeSlots = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"];
const container = document.getElementById("timetableContainer");
const daySelector = document.getElementById("daySelector");

// Load JSON and initialize
async function initTimetable() {
  try {
    const res = await fetch("updated_timetable.json");
    const data = await res.json();

    // Populate dropdown
    Object.keys(data).forEach(day => {
      const opt = document.createElement("option");
      opt.value = day;
      opt.textContent = day;
      daySelector.appendChild(opt);
    });

    daySelector.addEventListener("change", e => {
      const selectedDay = e.target.value;
      if (selectedDay) renderDayTable(selectedDay, data[selectedDay]);
      else container.innerHTML = "";
    });
  } catch (err) {
    container.innerHTML = `<p style="color:red;">Error loading timetable: ${err.message}</p>`;
  }
}

// Render timetable for one day
function renderDayTable(day, sections) {
  let html = `<h2>${day}</h2>`;
  html += `<table>
    <tr>
      <th>Section</th>
      ${timeSlots.map(slot => `<th>${slot}</th>`).join("")}
    </tr>`;

  sections.forEach(section => {
    html += `<tr><td class="section-name">${section.section}</td>`;
    for (let i = 0; i < timeSlots.length; i++) {
      const slot = timeSlots[i];
      const nextSlot = timeSlots[i + 1];
      const entries = section[slot] || [];
      const nextEntries = section[nextSlot] || [];

      // Detect 2-hour continuous labs
      if (isLab(entries) && JSON.stringify(entries) === JSON.stringify(nextEntries)) {
        html += `<td colspan="2" class="lab">${renderCell(entries)}</td>`;
        i++;
      } else {
        html += `<td>${renderCell(entries)}</td>`;
      }
    }
    html += "</tr>";
  });

  html += "</table>";
  container.innerHTML = html;
}

// Render cell contents intelligently
function renderCell(entries) {
  if (!entries || entries.length === 0 || entries[0].status === "Free") {
    return `<div class="free">Free</div>`;
  }

  return entries
    .map(e => {
      let content = `<div ${isLab([e]) ? 'class="lab"' : ""}>`;
      content += `<div><strong>${e.subject}</strong></div>`;
      if (e.teacher) content += `<div>${e.teacher}</div>`;
      if (e.room) content += `<div>Room: ${e.room}</div>`;
      content += "</div>";
      return content;
    })
    .join('<hr class="group-cell">');
}

function isLab(entries) {
  if (!entries || entries.length === 0) return false;
  const subject = entries[0].subject?.toLowerCase() || "";
  return subject.includes("lab");
}

initTimetable();
