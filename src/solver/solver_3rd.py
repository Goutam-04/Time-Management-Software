#!/usr/bin/env python
# solver_3rd.py
"""
Solves the university timetable problem for 3rd-semester sections
using Google OR-Tools CP-SAT solver.

Schedules both theory (in "To Be Assigned" slots) and
labs (in "Free" slots).

Reads from:
- data/config.json (rules, subjects, rooms, labs)
- data/data.json (current timetable)

Writes to:
- outputs/updated_timetable.json (solved timetable)
"""

import json
import sys
import copy
from ortools.sat.python import cp_model

def load_data(config_path, data_path):
    """Loads config and timetable data from JSON files."""
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        with open(data_path, 'r') as f:
            timetable_data = json.load(f)
        return config_data, timetable_data
    except FileNotFoundError as e:
        print(f"Error: File not found. {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON. {e}", file=sys.stderr)
        sys.exit(1)

def save_solution(solver, new_classes, lab_assignments, timetable_data, config_data, 
                  sections_to_solve, inv_core_subject_map, teacher_subject_map,
                  inv_lab_name_map, lab_teacher_map, inv_lab_room_id_to_name,
                  inv_lab_slot_id_to_name, lab_slot_map, section_index_map, 
                  NO_LAB_SUBJECT_IDX, NO_LAB_ROOM_ID, output_path):
    """
    Populates a copy of the timetable with the solved values and saves it.
    """
    print(f"Solution found. Saving to {output_path}...")
    
    # Create a deep copy to avoid modifying the original data
    timetable_copy = copy.deepcopy(timetable_data)

    # --- 1. Populate Theory Classes ---
    for (section, day, slot), var in new_classes.items():
        subject_index = solver.Value(var)
        subject_name = inv_core_subject_map[section][subject_index]
        teacher_name = teacher_subject_map[section][subject_name]
        room_name = config_data['section_theory_rooms'][section]
        
        list_index = section_index_map[day][section]
        slot_info = timetable_copy[day][list_index][slot][0]
        
        slot_info['status'] = "Assigned"
        slot_info['subject'] = subject_name
        slot_info['teacher'] = teacher_name
        slot_info['room'] = room_name

    # --- 2. Populate Lab Classes ---
    gA_subj, gA_room_vars, gB_subj, gB_room_vars = lab_assignments ### <-- CHANGED ### (renamed for clarity)
    
    for section in sections_to_solve:
        for day in config_data['settings']['days']:
            for lab_slot_idx, lab_slot_name in inv_lab_slot_id_to_name.items():
                
                # Check if Group A has a lab scheduled here
                gA_subj_idx = solver.Value(gA_subj[section, day, lab_slot_idx])
                
                if gA_subj_idx != NO_LAB_SUBJECT_IDX:
                    # --- Group A Lab ---
                    gA_lab_name = inv_lab_name_map[section][gA_subj_idx]
                    gA_teacher = lab_teacher_map[section][gA_lab_name]
                    gA_room_idx = solver.Value(gA_room_vars[section, day, lab_slot_idx]) ### <-- CHANGED ###
                    gA_room_name = inv_lab_room_id_to_name[gA_room_idx]                  ### <-- CHANGED ###

                    # --- Group B Lab (must be parallel) ---
                    gB_subj_idx = solver.Value(gB_subj[section, day, lab_slot_idx])
                    gB_lab_name = inv_lab_name_map[section][gB_subj_idx]
                    gB_teacher = lab_teacher_map[section][gB_lab_name]
                    gB_room_idx = solver.Value(gB_room_vars[section, day, lab_slot_idx]) ### <-- CHANGED ###
                    gB_room_name = inv_lab_room_id_to_name[gB_room_idx]                  ### <-- CHANGED ###

                    # Get the 1-hour slots this lab occupies
                    slot1, slot2 = lab_slot_map[lab_slot_name]
                    list_index = section_index_map[day][section]
                    
                    # Update first 1-hour slot
                    slot_info_1 = timetable_copy[day][list_index][slot1][0]
                    slot_info_1['status'] = "Assigned"
                    slot_info_1['subject'] = f"{gA_lab_name} (G-A) / {gB_lab_name} (G-B)"
                    slot_info_1['teacher'] = f"{gA_teacher} / {gB_teacher}"
                    slot_info_1['room'] = f"{gA_room_name} / {gB_room_name}" ### <-- CHANGED ###

                    # Update second 1-hour slot
                    slot_info_2 = timetable_copy[day][list_index][slot2][0]
                    slot_info_2['status'] = "Assigned"
                    slot_info_2['subject'] = f"{gA_lab_name} (G-A) / {gB_lab_name} (G-B)"
                    slot_info_2['teacher'] = f"{gA_teacher} / {gB_teacher}"
                    slot_info_2['room'] = f"{gA_room_name} / {gB_room_name}" ### <-- CHANGED ###

    # --- 3. Save to File ---
    try:
        with open(output_path, 'w') as f:
            json.dump(timetable_copy, f, indent=2)
        print(f"Successfully saved updated timetable to {output_path}")
    except IOError as e:
        print(f"Error: Could not write to output file. {e}", file=sys.stderr)
def main():
    """
    Main function to set up and solve the CP-SAT model.
    """
    # --- 1. Load Data ---
    # UPDATED PATHS
    config_path = 'data/config.json'
    data_path = 'data/data.json'
    output_path = 'outputs/updated_timetable.json'
    
    config_data, timetable_data = load_data(config_path, data_path)

    # --- 2. Define Problem Scope ---
    sections_to_solve = ["CSE-A-3", "CSE-B-3", "CSE-AIML-3"]
    
    all_sections = config_data['sections']
    days = config_data['settings']['days']
    slots = config_data['settings']['all_slots']
    lab_slot_names = config_data['settings']['lab_slot'] # e.g., "9-11"
    groups = config_data['settings']['groups'] # "A", "B"

    # --- 3. Pre-process Data and Build Mappings ---
    
    # --- Mappings for Theory (Same as before) ---
    core_subject_map = {}     # {section: {subject_name: index}}
    inv_core_subject_map = {} # {section: {index: subject_name}}
    teacher_subject_map = {}  # {section: {subject_name: teacher_name}}
    tba_slots_by_section = {s: [] for s in sections_to_solve}
    section_index_map = {d: {} for d in days} # {day: {section: list_index}}

    all_teachers = set()
    all_theory_rooms = set()
    all_lab_rooms = set(config_data['lab_rooms'])

    for day in days:
        for i, section_obj in enumerate(timetable_data[day]):
            section_index_map[day][section_obj['section']] = i

    for day in days:
        for section_obj in timetable_data[day]:
            for slot in slots:
                slot_info = section_obj[slot][0]
                if slot_info['status'] == "Assigned":
                    teacher = slot_info.get('teacher')
                    room = slot_info.get('room')
                    if teacher and "TBD" not in str(teacher):
                        all_teachers.add(teacher)
                    if room and room not in all_lab_rooms:
                        all_theory_rooms.add(room)

    for section in sections_to_solve:
        core_subjects = config_data['core_subjects'][section]
        core_subject_map[section] = {subject: i for i, subject in enumerate(core_subjects)}
        
        # --------------------- THIS IS THE FIX ---------------------
        # The line was:
        # inv_core_subject_map[section] = {i: subject for i, subject in enumerate(core_subject_map[section].items())}
        # It should be:
        inv_core_subject_map[section] = {i: subject for subject, i in core_subject_map[section].items()}
        # -----------------------------------------------------------
        
        teacher_subject_map[section] = {}
        for subject, teacher in config_data['subjects'][section]:
            teacher_subject_map[section][subject] = teacher # Map all subjects
            if subject in core_subject_map[section]:
                all_teachers.add(teacher)
        
        all_theory_rooms.add(config_data['section_theory_rooms'][section])
    
    for day in days:
        for section in sections_to_solve:
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                if section_obj[slot][0]['status'] == "To Be Assigned":
                    tba_slots_by_section[section].append((day, slot))

    # --- Mappings for Labs (New) ---
    lab_slot_map = {
        "9-11": ("9-10", "10-11"),
        "11-1": ("11-12", "12-1"),
        "3-5": ("3-4", "4-5")
    }
    theory_slot_to_lab_slot_map = {
        "9-10": "9-11", "10-11": "9-11",
        "11-12": "11-1", "12-1": "11-1",
        "3-4": "3-5", "4-5": "3-5"
    }
    lab_slot_name_to_id = {name: i for i, name in enumerate(lab_slot_names)}
    inv_lab_slot_id_to_name = {i: name for name, i in lab_slot_name_to_id.items()}
    
    lab_name_map = {}         # {section: {lab_name: index}}
    inv_lab_name_map = {}     # {section: {index: lab_name}}
    lab_teacher_map = {}      # {section: {lab_name: teacher_name}}
    lab_teacher_id_list_map = {} # {section: [teacher_id_0, ...]}
    available_lab_slots = {s: {d: {} for d in days} for s in sections_to_solve}

    for section in sections_to_solve:
        labs = config_data['labs'][section]
        lab_name_map[section] = {name: i for i, name in enumerate(labs)}
        inv_lab_name_map[section] = {i: name for name, i in lab_name_map[section].items()}
        lab_teacher_map[section] = {}
        for lab_name in labs:
            # Assumption: Lab name "DS Lab" maps to theory subject "DS"
            theory_subject = lab_name.split(" ")[0]
            if theory_subject in teacher_subject_map[section]:
                lab_teacher = teacher_subject_map[section][theory_subject]
                lab_teacher_map[section][lab_name] = lab_teacher
                all_teachers.add(lab_teacher)
            else:
                print(f"Warning: No teacher found for {lab_name} in section {section}", file=sys.stderr)
    
    # Find all available 2-hour "Free" slots for labs
    for section in sections_to_solve:
        for day in days:
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for lab_slot_name, (slot1, slot2) in lab_slot_map.items():
                if (slot1 in section_obj and slot2 in section_obj and
                    section_obj[slot1][0]['status'] == "Free" and
                    section_obj[slot2][0]['status'] == "Free"):
                    available_lab_slots[section][day][lab_slot_name_to_id[lab_slot_name]] = True
                else:
                    available_lab_slots[section][day][lab_slot_name_to_id[lab_slot_name]] = False

    # --- Create final integer mappings for all resources ---
    
    # Create unique dummy IDs for each potential lab assignment
    # This is to make the AddAllDifferent constraint work
    dummy_teacher_id_map = {}
    dummy_lab_room_id_map = {}
    
    dummy_teacher_counter = 0
    dummy_lab_room_counter = 0

    for section in sections_to_solve:
        for group in groups:
            all_teachers.add(f"DUMMY_TEACHER_{section}_{group}")
            dummy_teacher_id_map[section, group] = f"DUMMY_TEACHER_{section}_{group}"
            
            all_lab_rooms.add(f"DUMMY_LAB_ROOM_{section}_{group}")
            dummy_lab_room_id_map[section, group] = f"DUMMY_LAB_ROOM_{section}_{group}"

    teacher_name_to_id = {name: i for i, name in enumerate(sorted(list(all_teachers)))}
    inv_teacher_name_to_id = {i: name for name, i in teacher_name_to_id.items()} # <-- This was the other required line
    theory_room_name_to_id = {name: i for i, name in enumerate(sorted(list(all_theory_rooms)))}
    lab_room_name_to_id = {name: i for i, name in enumerate(sorted(list(all_lab_rooms)))}
    inv_lab_room_id_to_name = {i: name for name, i in lab_room_name_to_id.items()}

    # Map theory teacher names to their integer IDs
    section_teacher_id_list_map = {}
    for section in sections_to_solve:
        core_subjects = config_data['core_subjects'][section]
        teacher_ids = []
        for subject in core_subjects:
            teacher_name = teacher_subject_map[section][subject]
            teacher_ids.append(teacher_name_to_id[teacher_name])
        section_teacher_id_list_map[section] = teacher_ids

    # Map lab teacher names to their integer IDs
    for section in sections_to_solve:
        labs = config_data['labs'][section]
        teacher_ids = []
        for lab_name in labs:
            teacher_name = lab_teacher_map[section][lab_name]
            teacher_ids.append(teacher_name_to_id[teacher_name])
        lab_teacher_id_list_map[section] = teacher_ids

    # --- 4. Initialize CP-SAT Model ---
    model = cp_model.CpModel()

    # --- 4.5. Define Teacher Unavailability (NEW) ---
    print("Defining teacher unavailability constraints...")
    teacher_unavailability = {
        "SA": {"Monday": ["11-12", "12-1", "3-4"], "Wednesday": ["9-10"], "Thursday": ["11-12"]},
        "EO": {"Tuesday": ["10-11", "11-12", "12-1"], "Wednesday": ["12-1"], "Thursday": ["3-4"], "Friday": ["9-10", "10-11"]},
        "GF7": {"Monday": ["2-3"], "Tuesday": ["12-1"], "Wednesday": ["9-10"], "Thursday": ["3-4", "4-5"]},
        "SPS": {"Monday": ["9-10"], "Wednesday": ["11-12", "12-1", "4-5"], "Friday": ["10-11"]},
        "GF8": {"Monday": ["12-1"], "Tuesday": ["11-12", "12-1"], "Wednesday": ["11-12"], "Thursday": ["3-4"]},
        "SS": {"Tuesday": ["10-11"], "Wednesday": ["11-12"], "Thursday": ["11-12", "12-1"], "Friday": ["3-4"]},
        "GF9": {"Monday": ["3-4"], "Tuesday": ["11-12", "3-4", "4-5"], "Wednesday": ["3-4"]},
        "GF10": {"Monday": ["3-4", "4-5"], "Tuesday": ["9-10"], "Thursday": ["10-11"], "Friday": ["12-1"]},
        "AS": {"Monday": ["3-4", "4-5"]},
        "SP": {"Tuesday": ["3-4", "4-5"]},
        "KN": {"Thursday": ["3-4", "4-5"]},
    }

    # --- 5. Create Model Variables ---
    
    # --- Theory Variables (Same as before) ---
    new_classes = {}
    for section in sections_to_solve:
        num_core_subjects = len(core_subject_map[section])
        for (day, slot) in tba_slots_by_section[section]:
            new_classes[section, day, slot] = model.NewIntVar(
                0, num_core_subjects - 1, f"theory_{section}_{day}_{slot}"
            )

    # --- Lab Variables (New) ---
    NO_LAB_SUBJECT_IDX = len(config_data['labs']['CSE-A-3']) # All 3rd sem have 4 labs
    NO_LAB_ROOM_ID = lab_room_name_to_id[dummy_lab_room_id_map["CSE-A-3", "A"]] # Use one as a reference

    lab_group_A_subject = {} # [section][day][lab_slot_idx] -> subject_idx (0-3) or 4 (NoLab)
    lab_group_A_room = {}    # [section][day][lab_slot_idx] -> room_idx or NO_LAB_ROOM_ID
    lab_group_B_subject = {}
    lab_group_B_room = {}
    
    lab_assignments = (lab_group_A_subject, lab_group_A_room, lab_group_B_subject, lab_group_B_room)

    for section in sections_to_solve:
        # Get the unique dummy IDs for this section's groups
        dummy_room_A_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "A"]]
        dummy_room_B_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "B"]]
        
        for day in days:
            for lab_slot_idx in lab_slot_name_to_id.values():
                
                # Domains for this slot
                subject_domain = [NO_LAB_SUBJECT_IDX]
                room_A_domain = [dummy_room_A_id]
                room_B_domain = [dummy_room_B_id]
                
                # If the slot is available, add real labs/rooms to the domain
                if available_lab_slots[section][day][lab_slot_idx]:
                    subject_domain.extend(range(NO_LAB_SUBJECT_IDX))
                    room_A_domain.extend(range(len(all_lab_rooms) - len(sections_to_solve)*2)) # All real rooms
                    room_B_domain.extend(range(len(all_lab_rooms) - len(sections_to_solve)*2))
                
                # Create variables
                lab_group_A_subject[section, day, lab_slot_idx] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(subject_domain), f"lab_A_subj_{section}_{day}_{lab_slot_idx}")
                lab_group_B_subject[section, day, lab_slot_idx] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(subject_domain), f"lab_B_subj_{section}_{day}_{lab_slot_idx}")
                
                lab_group_A_room[section, day, lab_slot_idx] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(room_A_domain), f"lab_A_room_{section}_{day}_{lab_slot_idx}")
                lab_group_B_room[section, day, lab_slot_idx] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(room_B_domain), f"lab_B_room_{section}_{day}_{lab_slot_idx}")

    # --- 6. Add Constraints ---

    # --- Constraint 0: Teacher Unavailability (NEW) ---
    print("Adding teacher unavailability constraints...")
    
    # A. For Theory Classes
    for (section, day, slot), subject_var in new_classes.items():
        teacher_options = section_teacher_id_list_map[section]
        for subject_index, teacher_id in enumerate(teacher_options):
            teacher_name = inv_teacher_name_to_id.get(teacher_id)
            if teacher_name and teacher_name in teacher_unavailability:
                if day in teacher_unavailability[teacher_name] and slot in teacher_unavailability[teacher_name][day]:
                    # This teacher is unavailable. The subject var (which holds a subject_index) cannot be this subject_index.
                    print(f"  -> Blocking {teacher_name} (Theory) for {section} on {day} at {slot}")
                    model.Add(subject_var != subject_index)
    
    # B. For Lab Classes
    for section in sections_to_solve:
        lab_teacher_ids = lab_teacher_id_list_map[section]
        for day in days:
            for lab_slot_idx, lab_slot_name in inv_lab_slot_id_to_name.items():
                slot1, slot2 = lab_slot_map[lab_slot_name]
                
                gA_subj = lab_group_A_subject[section, day, lab_slot_idx]
                gB_subj = lab_group_B_subject[section, day, lab_slot_idx]
                
                for lab_index, teacher_id in enumerate(lab_teacher_ids):
                    teacher_name = inv_teacher_name_to_id.get(teacher_id)
                    if teacher_name and teacher_name in teacher_unavailability:
                        if day in teacher_unavailability[teacher_name]:
                            if (slot1 in teacher_unavailability[teacher_name][day] or 
                                slot2 in teacher_unavailability[teacher_name][day]):
                                # This teacher is unavailable for this 2-hour lab slot.
                                # Neither Group A nor Group B can have this lab index.
                                print(f"  -> Blocking Lab {inv_lab_name_map[section][lab_index]} ({teacher_name}) for {section} on {day} at {lab_slot_name}")
                                model.Add(gA_subj != lab_index)
                                model.Add(gB_subj != lab_index)

    # --- Constraint 1: Subject Frequency (Theory) ---
    print("Adding subject frequency constraints (Theory)...")
    for section in sections_to_solve:
        section_vars = [new_classes[s, d, t] for (s, d, t) in new_classes if s == section]
        
        num_required = len(core_subject_map[section]) * 3
        if len(section_vars) != num_required:
            print(f"Error: Section {section} has {len(section_vars)} 'To Be Assigned' slots,"
                  f" but needs {num_required} (4 subjects * 3 times).", file=sys.stderr)
            print("Please check data.json. Cannot solve.", file=sys.stderr)
            sys.exit(1)

        for j in range(len(core_subject_map[section])):
            bool_list = []
            for i in range(len(section_vars)):
                bool_list.append(
                    model.NewBoolVar(f"sec_{section}_subj_{j}_var_{i}")
                )
            for i in range(len(section_vars)):
                var = section_vars[i]
                b = bool_list[i]
                model.Add(var == j).OnlyEnforceIf(b)
                model.Add(var != j).OnlyEnforceIf(b.Not())
            model.Add(sum(bool_list) == 3)

    # --- Constraint 2: Daily Subject Uniqueness (Theory) ---
    print("Adding daily subject uniqueness constraints (Theory)...")
    # (Code from previous step)
    for section in sections_to_solve:
        for day in days:
            daily_vars = []
            for (s, d, slot) in new_classes:
                if s == section and d == day:
                    daily_vars.append(new_classes[s, d, slot])
            if not daily_vars:
                continue

            pre_assigned_subjects_on_day = set()
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                slot_info = section_obj[slot][0]
                if slot_info['status'] == "Assigned":
                    subject = slot_info.get('subject')
                    if subject and subject in core_subject_map[section]:
                        pre_assigned_subjects_on_day.add(subject)

            for subject_name, subject_index in core_subject_map[section].items():
                bool_list = []
                for i in range(len(daily_vars)):
                    bool_list.append(
                        model.NewBoolVar(f"day_{day}_sec_{section}_subj_{subject_index}_var_{i}")
                    )
                for i in range(len(daily_vars)):
                    var = daily_vars[i]
                    b = bool_list[i]
                    model.Add(var == subject_index).OnlyEnforceIf(b)
                    model.Add(var != subject_index).OnlyEnforceIf(b.Not())
                variable_subject_count = sum(bool_list)
                
                if subject_name in pre_assigned_subjects_on_day:
                    model.Add(variable_subject_count == 0)
                else:
                    model.Add(variable_subject_count <= 1)

    # --- Constraint 3: Lab Parallelism & Properties ---
    print("Adding lab parallelism constraints...")
    for section in sections_to_solve:
        for day in days:
            for lab_slot_idx in lab_slot_name_to_id.values():
                gA_subj = lab_group_A_subject[section, day, lab_slot_idx]
                gB_subj = lab_group_B_subject[section, day, lab_slot_idx]
                gA_room = lab_group_A_room[section, day, lab_slot_idx]
                gB_room = lab_group_B_room[section, day, lab_slot_idx]

                dummy_room_A_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "A"]]
                dummy_room_B_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "B"]]

                # Create boolean vars for "has lab"
                b_A_has_lab = model.NewBoolVar(f"b_A_has_lab_{section}_{day}_{lab_slot_idx}")
                b_B_has_lab = model.NewBoolVar(f"b_B_has_lab_{section}_{day}_{lab_slot_idx}")

                model.Add(gA_subj != NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b_A_has_lab)
                model.Add(gA_subj == NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b_A_has_lab.Not())
                
                model.Add(gB_subj != NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b_B_has_lab)
                model.Add(gB_subj == NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b_B_has_lab.Not())

                # 1. Groups A and B must have parallel labs
                model.Add(b_A_has_lab == b_B_has_lab)
                
                # 2. If they have labs, subjects and rooms must be different
                model.Add(gA_subj != gB_subj).OnlyEnforceIf(b_A_has_lab)
                model.Add(gA_room != gB_room).OnlyEnforceIf(b_A_has_lab)
                
                # 3. Link subject to room (if no subject, no room)
                model.Add(gA_room != dummy_room_A_id).OnlyEnforceIf(b_A_has_lab)
                model.Add(gA_room == dummy_room_A_id).OnlyEnforceIf(b_A_has_lab.Not())
                
                model.Add(gB_room != dummy_room_B_id).OnlyEnforceIf(b_B_has_lab)
                model.Add(gB_room == dummy_room_B_id).OnlyEnforceIf(b_B_has_lab.Not())


    # --- Constraint 4: Lab Session Frequency ---
    print("Adding lab frequency constraints...")
    for section in sections_to_solve:
        # Get all lab subject variables for the week for each group
        all_gA_subj_vars = [lab_group_A_subject[section, d, s] for d in days for s in lab_slot_name_to_id.values()]
        all_gB_subj_vars = [lab_group_B_subject[section, d, s] for d in days for s in lab_slot_name_to_id.values()]
        
        for lab_idx in range(NO_LAB_SUBJECT_IDX):
            # Check Group A
            bool_list_A = []
            for var in all_gA_subj_vars:
                b = model.NewBoolVar(f"b_freq_A_{section}_lab{lab_idx}")
                model.Add(var == lab_idx).OnlyEnforceIf(b)
                model.Add(var != lab_idx).OnlyEnforceIf(b.Not())
                bool_list_A.append(b)
            model.Add(sum(bool_list_A) == 1) # Each lab exactly once per week

            # Check Group B
            bool_list_B = []
            for var in all_gB_subj_vars:
                b = model.NewBoolVar(f"b_freq_B_{section}_lab{lab_idx}")
                model.Add(var == lab_idx).OnlyEnforceIf(b)
                model.Add(var != lab_idx).OnlyEnforceIf(b.Not())
                bool_list_B.append(b)
            model.Add(sum(bool_list_B) == 1) # Each lab exactly once per week

    # --- Constraint 5: Daily Lab Limit ---
    print("Adding daily lab limit constraints...")
    for section in sections_to_solve:
        for day in days:
            daily_gA_subj_vars = [lab_group_A_subject[section, day, s] for s in lab_slot_name_to_id.values()]
            daily_gB_subj_vars = [lab_group_B_subject[section, day, s] for s in lab_slot_name_to_id.values()]
            
            # Count labs for Group A
            bool_list_A = []
            for var in daily_gA_subj_vars:
                b = model.NewBoolVar(f"b_daily_A_{section}_{day}")
                model.Add(var != NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b)
                model.Add(var == NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b.Not())
                bool_list_A.append(b)
            model.Add(sum(bool_list_A) <= 2) # At most 2 lab sessions per day

            # Count labs for Group B
            bool_list_B = []
            for var in daily_gB_subj_vars:
                b = model.NewBoolVar(f"b_daily_B_{section}_{day}")
                model.Add(var != NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b)
                model.Add(var == NO_LAB_SUBJECT_IDX).OnlyEnforceIf(b.Not())
                bool_list_B.append(b)
            model.Add(sum(bool_list_B) <= 2) # At most 2 lab sessions per day

    # --- Constraint 6: Resource Uniqueness (Combined Theory + Lab) ---
    print("Adding combined resource uniqueness constraints...")
    for day in days:
        for slot in slots: # Iterate over 1-hour slots
            teacher_vars_at_slot = []
            theory_room_vars_at_slot = []
            lab_room_vars_at_slot = []
            
            # 1. Add Pre-assigned theory classes
            for section in all_sections:
                list_index = section_index_map[day][section]
                slot_info = timetable_data[day][list_index][slot][0]
                status = slot_info['status']
                
                if status == "Assigned":
                    teacher = slot_info.get('teacher')
                    room = slot_info.get('room')
                    
                    if teacher and teacher in teacher_name_to_id:
                        teacher_vars_at_slot.append(model.NewConstant(teacher_name_to_id[teacher]))
                    
                    if room and room in theory_room_name_to_id:
                        theory_room_vars_at_slot.append(model.NewConstant(theory_room_name_to_id[room]))

            # 2. Add Variable theory classes
            for (section, d, t), subject_var in new_classes.items():
                if d == day and t == slot:
                    # Add room
                    room_name = config_data['section_theory_rooms'][section]
                    theory_room_vars_at_slot.append(model.NewConstant(theory_room_name_to_id[room_name]))
                    
                    # Add teacher
                    teacher_options = section_teacher_id_list_map[section]
                    teacher_var = model.NewIntVarFromDomain(
                        cp_model.Domain.FromValues(teacher_options), 
                        f"teacher_{section}_{day}_{slot}"
                    )
                    model.AddElement(subject_var, teacher_options, teacher_var)
                    teacher_vars_at_slot.append(teacher_var)
            
            # 3. Add Variable lab classes that cover this slot
            covering_lab_slot_name = theory_slot_to_lab_slot_map.get(slot)
            if covering_lab_slot_name:
                lab_slot_idx = lab_slot_name_to_id[covering_lab_slot_name]
                
                for section in sections_to_solve:
                    # --- Group A Teacher & Room ---
                    gA_subj = lab_group_A_subject[section, day, lab_slot_idx]
                    gA_room = lab_group_A_room[section, day, lab_slot_idx]
                    gA_teacher = model.NewIntVar(0, len(teacher_name_to_id)-1, f"lab_A_teach_{section}_{day}_{slot}")
                    
                    # Teacher list includes real teachers + unique dummy
                    teacher_list_A = lab_teacher_id_list_map[section] + [teacher_name_to_id[dummy_teacher_id_map[section, "A"]]]
                    model.AddElement(gA_subj, teacher_list_A, gA_teacher)
                    
                    teacher_vars_at_slot.append(gA_teacher)
                    lab_room_vars_at_slot.append(gA_room)

                    # --- Group B Teacher & Room ---
                    gB_subj = lab_group_B_subject[section, day, lab_slot_idx]
                    gB_room = lab_group_B_room[section, day, lab_slot_idx]
                    gB_teacher = model.NewIntVar(0, len(teacher_name_to_id)-1, f"lab_B_teach_{section}_{day}_{slot}")
                    
                    teacher_list_B = lab_teacher_id_list_map[section] + [teacher_name_to_id[dummy_teacher_id_map[section, "B"]]]
                    model.AddElement(gB_subj, teacher_list_B, gB_teacher)
                    
                    teacher_vars_at_slot.append(gB_teacher)
                    lab_room_vars_at_slot.append(gB_room)

            # Add the "all different" constraint for this specific 1-hour slot
            if teacher_vars_at_slot:
                model.AddAllDifferent(teacher_vars_at_slot)
            if theory_room_vars_at_slot:
                model.AddAllDifferent(theory_room_vars_at_slot)
            if lab_room_vars_at_slot:
                model.AddAllDifferent(lab_room_vars_at_slot)

    # --- 7. Solve the Model ---
    print("\nStarting solver...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config_data['settings']['solver_timeout_seconds']
    status = solver.Solve(model)

    # --- 8. Process Solution ---
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        save_solution(
            solver, new_classes, lab_assignments, timetable_data, config_data,
            sections_to_solve, inv_core_subject_map, teacher_subject_map,
            inv_lab_name_map, lab_teacher_map, inv_lab_room_id_to_name,
            inv_lab_slot_id_to_name, lab_slot_map, section_index_map,
            NO_LAB_SUBJECT_IDX, NO_LAB_ROOM_ID, output_path
        )
    elif status == cp_model.INFEASIBLE:
        print("No solution found: The problem is infeasible.")
        print("Check constraints, especially room/teacher clashes or lack of 'Free' slots for labs.")
    elif status == cp_model.MODEL_INVALID:
        print("No solution found: The model is invalid.")
    else:
        print(f"No solution found. Solver status: {status}")

if __name__ == "__main__":
    main()