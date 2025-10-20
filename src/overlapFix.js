const fs = require('fs');

/**
 * Main function to find and report conflicts in pre-assigned classes.
 */
function findAssignedConflicts() {
    console.log("🔍 Checking for conflicts in PRE-ASSIGNED classes...");

    // --- 1. Load Data ---
    let timetable;
    try {
        timetable = JSON.parse(fs.readFileSync('data.json', 'utf8'));
    } catch (error) {
        console.error("❌ Error reading data.json. Make sure the file exists and is valid JSON.", error);
        return;
    }

    const days = Object.keys(timetable);
    const slotUsage = {}; // Structure: { "Day-Slot": { teachers: {}, rooms: {} } }
    const recessTracker = {}; // Structure: { "Day-Entity": [slots] }
    let conflictCount = 0;

    // --- 2. Collect All Pre-Assigned Classes ---
    for (const day of days) {
        for (const sectionSchedule of timetable[day]) {
            const sectionName = sectionSchedule.section;
            for (const slot in sectionSchedule) {
                if (slot === 'section') continue;

                const slotInfo = sectionSchedule[slot][0];
                if (slotInfo.status === 'Assigned') {
                    const usageKey = `${day}-${slot}`;
                    if (!slotUsage[usageKey]) {
                        slotUsage[usageKey] = { teachers: {}, rooms: {}, sections: {} };
                    }

                    const { teacher, room } = slotInfo;

                    // Track teacher usage
                    if (teacher) {
                        if (!slotUsage[usageKey].teachers[teacher]) slotUsage[usageKey].teachers[teacher] = [];
                        slotUsage[usageKey].teachers[teacher].push(sectionName);
                    }

                    // Track room usage
                    if (room) {
                        if (!slotUsage[usageKey].rooms[room]) slotUsage[usageKey].rooms[room] = [];
                        slotUsage[usageKey].rooms[room].push(sectionName);
                    }
                     // Track section usage (for recess rule)
                     if (!slotUsage[usageKey].sections[sectionName]) slotUsage[usageKey].sections[sectionName] = [];
                     slotUsage[usageKey].sections[sectionName].push(teacher);


                    // Track for Recess Rule
                    if (slot === '12-1' || slot === '2-3') {
                        // Track teacher
                        if (teacher) {
                            const recessKeyTeacher = `${day}-${teacher}`;
                            if (!recessTracker[recessKeyTeacher]) recessTracker[recessKeyTeacher] = new Set();
                            recessTracker[recessKeyTeacher].add(slot);
                        }
                        // Track section
                        const recessKeySection = `${day}-${sectionName}`;
                        if (!recessTracker[recessKeySection]) recessTracker[recessKeySection] = new Set();
                        recessTracker[recessKeySection].add(slot);
                    }
                }
            }
        }
    }

    // --- 3. Report Conflicts ---
    console.log("\n--- PRE-ASSIGNED CONFLICT REPORT ---");

    // Check for Teacher and Room double-booking
    for (const key in slotUsage) {
        const [day, slot] = key.split('-');
        const usage = slotUsage[key];

        // Teacher conflicts
        for (const teacher in usage.teachers) {
            if (usage.teachers[teacher].length > 1) {
                conflictCount++;
                console.log(`
    🔴 Teacher Conflict!
    ---------------------
    Who:       Teacher ${teacher}
    When:      ${day} at ${slot}
    Problem:   Assigned to multiple sections: ${usage.teachers[teacher].join(', ')}
    ---------------------`);
            }
        }

        // Room conflicts
        for (const room in usage.rooms) {
            if (usage.rooms[room].length > 1) {
                conflictCount++;
                console.log(`
    🔴 Room Conflict!
    ---------------------
    Where:     Room ${room}
    When:      ${day} at ${slot}
    Problem:   Occupied by multiple sections: ${usage.rooms[room].join(', ')}
    ---------------------`);
            }
        }
    }

    // Check for Recess Rule violations
    for (const key in recessTracker) {
        const slots = recessTracker[key];
        if (slots.has('12-1') && slots.has('2-3')) {
            const [day, entity] = key.split(/-(.+)/); // Split only on the first dash
            conflictCount++;
            console.log(`
    🔴 Recess Rule Violation!
    ---------------------
    Who/What:  ${entity}
    When:      ${day}
    Problem:   Scheduled during both 12-1 PM and 2-3 PM slots.
    ---------------------`);
        }
    }


    if (conflictCount === 0) {
        console.log("\n✅ No conflicts found among pre-assigned classes. The issue might be a more complex constraint interaction.");
    } else {
        console.log(`\nFound a total of ${conflictCount} pre-assigned conflicts.
        \nACTION: Please fix these directly in your 'data.json' file and run the Python solver again.`);
    }
}

// --- Run the function ---
findAssignedConflicts();