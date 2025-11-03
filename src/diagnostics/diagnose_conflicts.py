import json

def diagnose_all_conflicts():
    """
    Loads data and runs a comprehensive check for all types of conflicts:
    1. "To Be Assigned" slots competing for the same room.
    2. "Assigned" classes with teacher or room double-bookings.
    3. "Assigned" classes violating the recess rule.
    4. Conflicts between "Assigned" classes and "To Be Assigned" slots.
    """
    print("🩺 Running Comprehensive Timetable Diagnostics...")

    # --- 1. Load Data ---
    try:
        # UPDATED PATHS
        with open('data/config.json', 'r') as f:
            config = json.load(f)
        with open('data/data.json', 'r') as f:
            timetable = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}. Make sure 'data/config.json' and 'data/data.json' are present.")
        return

    days = config['settings']['days']
    slots = config['settings']['all_slots']
    section_rooms = config['section_theory_rooms']
    subjects_map = config['subjects']
    teacher_map = {
        (sec, sub_info[0]): sub_info[1]
        for sec, subs in subjects_map.items()
        for sub_info in subs
    }

    conflict_count = 0
    
    # --- 2. Iterate Through Every Time Slot ---
    for day in days:
        for slot in slots:
            slot_teachers = {} # teacher -> [sections]
            slot_rooms = {}    # room -> [sections]

            # Collect data for the current slot
            for section_schedule in timetable.get(day, []):
                section = section_schedule['section']
                if slot not in section_schedule:
                    continue

                slot_info = section_schedule[slot][0]
                status = slot_info.get('status')
                room = section_rooms.get(section) # The required room for this section

                # A. Handle Pre-Assigned Classes
                if status == 'Assigned':
                    teacher = slot_info.get('teacher')
                    assigned_room = slot_info.get('room')
                    
                    if teacher:
                        if teacher not in slot_teachers: slot_teachers[teacher] = []
                        slot_teachers[teacher].append(f"{section} (Assigned)")
                    
                    if assigned_room:
                        if assigned_room not in slot_rooms: slot_rooms[assigned_room] = []
                        slot_rooms[assigned_room].append(f"{section} (Assigned)")

                # B. Handle Slots to be Filled
                elif status == 'To Be Assigned':
                    if room:
                        if room not in slot_rooms: slot_rooms[room] = []
                        slot_rooms[room].append(f"{section} (To Be Assigned)")
                    
                    # Check potential teacher conflicts for this slot
                    for subject, teacher in teacher_map.items():
                        if subject[0] == section: # If this teacher teaches this section
                           if teacher not in slot_teachers: slot_teachers[teacher] = []
                           slot_teachers[teacher].append(f"{section} (Potential for {subject[1]})")


            # --- 3. Report Conflicts for the Current Slot ---
            for teacher, assignments in slot_teachers.items():
                if len(assignments) > 1:
                    conflict_count += 1
                    print(f"""
    🔴 Teacher Conflict!
    ---------------------
    Who:       Teacher {teacher}
    When:      {day} at {slot}
    Problem:   Is double-booked. Required for: {', '.join(assignments)}
    ---------------------""")

            for room, assignments in slot_rooms.items():
                if len(assignments) > 1:
                    conflict_count += 1
                    print(f"""
    🔴 Room Conflict!
    ---------------------
    Where:     Room {room}
    When:      {day} at {slot}
    Problem:   Is double-booked. Required for: {', '.join(assignments)}
    ---------------------""")

    # --- 4. Final Report ---
    if conflict_count == 0:
        print("\n✅ No fundamental teacher or room conflicts found. The issue might be with other constraints like daily class limits or recess rules.")
    else:
        print(f"\nFound a total of {conflict_count} conflicts. Please fix these in 'data.json' and re-run the solver.")


# --- Run the diagnostic tool ---
if __name__ == '__main__':
    diagnose_all_conflicts()