#!/usr/bin/env python
# solver_7th_sem.py
"""
Solves the university timetable problem for 7th-semester sections
using Google OR-Tools CP-SAT solver.

Reads from:
- data/config.json (rules, subjects, rooms, labs)
- data/data.json (current timetable, which is read by the script)
- outputs/updated_timetable.json (if it exists, to chain solvers)

Writes to:
- outputs/updated_timetable.json (solved timetable)
"""

import json
import sys
import copy
from ortools.sat.python import cp_model

def load_data(config_path, data_path, output_path):
    """Loads config and timetable data from JSON files."""
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        try:
            with open(output_path, 'r') as f:
                timetable_data = json.load(f)
                print("Reading from existing updated_timetable.json...")
        except FileNotFoundError:
            with open(data_path, 'r') as f:
                timetable_data = json.load(f)
                print("Reading from original data.json...")

        return config_data, timetable_data
    except FileNotFoundError as e:
        print(f"Error: A required file was not found. {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON. {e}", file=sys.stderr)
        sys.exit(1)

def save_solution(solver, new_classes, lab_assignments, timetable_data, config_data, 
                  sections_to_solve, inv_core_subject_map, teacher_subject_map,
                  inv_lab_name_map, lab_teacher_map, inv_lab_room_id_to_name,
                  inv_lab_slot_id_to_name, lab_slot_map, section_index_map, 
                  output_path):
    """
    Populates a copy of the timetable with the solved values and saves it.
    """
    print(f"Solution found for 7th Semester. Saving to {output_path}...")
    
    timetable_copy = copy.deepcopy(timetable_data)

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

    gA_subj, gA_room_vars, gB_subj, gB_room_vars = lab_assignments
    
    for section in sections_to_solve:
        NO_LAB_SUBJECT_IDX_sec = len(config_data['labs'][section])
        
        for day in config_data['settings']['days']:
            for lab_slot_idx, lab_slot_name in inv_lab_slot_id_to_name.items():
                gA_subj_idx = solver.Value(gA_subj[section, day, lab_slot_idx])
                
                if gA_subj_idx != NO_LAB_SUBJECT_IDX_sec:
                    gA_lab_name = inv_lab_name_map[section][gA_subj_idx]
                    gA_teacher = lab_teacher_map[section][gA_lab_name]
                    gA_room_idx = solver.Value(gA_room_vars[section, day, lab_slot_idx])
                    gA_room_name = inv_lab_room_id_to_name[gA_room_idx]

                    gB_subj_idx = solver.Value(gB_subj[section, day, lab_slot_idx])
                    gB_lab_name = inv_lab_name_map[section][gB_subj_idx]
                    gB_teacher = lab_teacher_map[section][gB_lab_name]
                    gB_room_idx = solver.Value(gB_room_vars[section, day, lab_slot_idx])
                    gB_room_name = inv_lab_room_id_to_name[gB_room_idx]

                    slot1, slot2 = lab_slot_map[lab_slot_name]
                    list_index = section_index_map[day][section]
                    
                    slot_info_1 = timetable_copy[day][list_index][slot1][0]
                    slot_info_1['status'] = "Assigned"
                    slot_info_1['subject'] = f"{gA_lab_name} (G-A) / {gB_lab_name} (G-B)"
                    slot_info_1['teacher'] = f"{gA_teacher} / {gB_teacher}"
                    slot_info_1['room'] = f"{gA_room_name} / {gB_room_name}"

                    slot_info_2 = timetable_copy[day][list_index][slot2][0]
                    slot_info_2['status'] = "Assigned"
                    slot_info_2['subject'] = f"{gA_lab_name} (G-A) / {gB_lab_name} (G-B)"
                    slot_info_2['teacher'] = f"{gA_teacher} / {gB_teacher}"
                    slot_info_2['room'] = f"{gA_room_name} / {gB_room_name}"

    try:
        with open(output_path, 'w') as f:
            json.dump(timetable_copy, f, indent=2)
        print(f"Successfully saved updated timetable to {output_path}")
    except IOError as e:
        print(f"Error: Could not write to output file. {e}", file=sys.stderr)

def main():
    # UPDATED PATHS
    config_path = 'data/config.json'
    data_path = 'data/data.json'
    output_path = 'outputs/updated_timetable.json'
    
    config_data, timetable_data = load_data(config_path, data_path, output_path)

    sections_to_solve = ["CSE-7", "IT-7"]
    
    all_sections_in_config = config_data['sections']
    days = config_data['settings']['days']
    slots = config_data['settings']['all_slots']
    lab_slot_names = config_data['settings']['lab_slot']
    groups = config_data['settings']['groups']

    core_subject_map, inv_core_subject_map, teacher_subject_map = {}, {}, {}
    tba_slots_by_section = {s: [] for s in sections_to_solve}
    section_index_map = {d: {} for d in days}
    all_teachers, all_theory_rooms = set(), set()
    all_lab_rooms = set(config_data['lab_rooms'])

    for day in days:
        for i, section_obj in enumerate(timetable_data[day]):
            section_index_map[day][section_obj['section']] = i

    for day in days:
        for section_obj in timetable_data[day]:
            for slot in slots:
                if slot not in section_obj: continue # Skip if slot missing
                slot_info = section_obj[slot][0]
                if slot_info['status'] == "Assigned":
                    teacher, room = slot_info.get('teacher'), slot_info.get('room')
                    if teacher and "/" not in str(teacher) and "TBD" not in str(teacher):
                        all_teachers.add(teacher)
                    elif teacher and "/" in str(teacher):
                        t1, t2 = [t.strip() for t in teacher.split('/')]
                        if t1 and "TBD" not in t1: all_teachers.add(t1)
                        if t2 and "TBD" not in t2: all_teachers.add(t2)
                    if room and "/" not in str(room) and room not in all_lab_rooms:
                        all_theory_rooms.add(room)

    for section in all_sections_in_config:
        teacher_subject_map[section] = {s: t for s, t in config_data['subjects'][section]}
        all_theory_rooms.add(config_data['section_theory_rooms'][section])

    for section in sections_to_solve:
        core_subjects = config_data['core_subjects'][section]
        core_subject_map[section] = {s: i for i, s in enumerate(core_subjects)}
        inv_core_subject_map[section] = {i: s for s, i in core_subject_map[section].items()}
        for subject in core_subjects:
            if subject in teacher_subject_map[section]:
                all_teachers.add(teacher_subject_map[section][subject])

    for day in days:
        for section in sections_to_solve:
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                if slot in section_obj and section_obj[slot][0]['status'] == "To Be Assigned":
                    tba_slots_by_section[section].append((day, slot))

    lab_slot_map = {"9-11": ("9-10", "10-11"), "11-1": ("11-12", "12-1"), "3-5": ("3-4", "4-5")}
    theory_slot_to_lab_slot_map = {s: ls for ls, s_tuple in lab_slot_map.items() for s in s_tuple}
    lab_slot_name_to_id = {name: i for i, name in enumerate(lab_slot_names)}
    inv_lab_slot_id_to_name = {i: name for name, i in lab_slot_name_to_id.items()}
    
    lab_name_map, inv_lab_name_map, lab_teacher_map, lab_teacher_id_list_map = {}, {}, {}, {}
    section_teacher_id_list_map = {}
    available_lab_slots = {s: {d: {} for d in days} for s in sections_to_solve}
    section_lab_count = {}

    for section in all_sections_in_config:
        labs = config_data['labs'].get(section, [])
        lab_teacher_map[section] = {}
        for lab_name in labs:
            teacher_name = None
            if lab_name in teacher_subject_map[section]:
                teacher_name = teacher_subject_map[section][lab_name]
            else:
                theory_subject = lab_name.split(" ")[0]
                if theory_subject in teacher_subject_map[section]:
                    teacher_name = teacher_subject_map[section][theory_subject]
            if teacher_name:
                lab_teacher_map[section][lab_name] = teacher_name
                all_teachers.add(teacher_name)
            else:
                print(f"Warning: No teacher could be mapped for lab '{lab_name}' in section {section}", file=sys.stderr)

    for section in sections_to_solve:
        labs = config_data['labs'][section]
        section_lab_count[section] = len(labs)
        lab_name_map[section] = {name: i for i, name in enumerate(labs)}
        inv_lab_name_map[section] = {i: name for name, i in lab_name_map[section].items()}
        for day in days:
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for lab_slot_name, (s1, s2) in lab_slot_map.items():
                available_lab_slots[section][day][lab_slot_name_to_id[lab_slot_name]] = (
                    s1 in section_obj and s2 in section_obj and
                    section_obj[s1][0]['status'] == "Free" and section_obj[s2][0]['status'] == "Free"
                )

    dummy_teacher_id_map, dummy_lab_room_id_map = {}, {}
    for section in all_sections_in_config:
        for group in groups:
            dummy_teacher_id_map[section, group] = f"DUMMY_TEACHER_{section}_{group}"
            all_teachers.add(dummy_teacher_id_map[section, group])
            dummy_lab_room_id_map[section, group] = f"DUMMY_LAB_ROOM_{section}_{group}"
            all_lab_rooms.add(dummy_lab_room_id_map[section, group])

    teacher_name_to_id = {name: i for i, name in enumerate(sorted(list(all_teachers)))}
    inv_teacher_name_to_id = {i: name for name, i in teacher_name_to_id.items()} # <-- (NEW) 1. ADDED THIS
    theory_room_name_to_id = {name: i for i, name in enumerate(sorted(list(all_theory_rooms)))}
    lab_room_name_to_id = {name: i for i, name in enumerate(sorted(list(all_lab_rooms)))}
    inv_lab_room_id_to_name = {i: name for name, i in lab_room_name_to_id.items()}
    real_lab_room_ids = [i for i, name in inv_lab_room_id_to_name.items() if not name.startswith("DUMMY")]

    for section in sections_to_solve:
        core_subjects = config_data['core_subjects'][section]
        section_teacher_id_list_map[section] = [teacher_name_to_id.get(teacher_subject_map[section].get(s, ''), -1) for s in core_subjects]

    for section in all_sections_in_config:
        labs = config_data['labs'].get(section, []) # Use .get for safety
        lab_teacher_id_list_map[section] = [teacher_name_to_id.get(lab_teacher_map[section].get(ln, ''), -1) for ln in labs]

    # Debug: Print available lab slots
    print("\n=== DEBUG: Available Lab Slots ===")
    for section in sections_to_solve:
        print(f"\n{section}:")
        for day in days:
            available_slots = [inv_lab_slot_id_to_name[slot_id] for slot_id, available in available_lab_slots[section][day].items() if available]
            if available_slots:
                print(f"  {day}: {', '.join(available_slots)}")

    model = cp_model.CpModel()
    
    # --- (NEW) 2. Define Teacher Unavailability ---
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
    
    new_classes = {}
    for section in sections_to_solve:
        num_core_subjects = len(core_subject_map[section])
        for (day, slot) in tba_slots_by_section[section]:
            new_classes[section, day, slot] = model.NewIntVar(0, num_core_subjects - 1, f"theory_{section}_{day}_{slot}")

    lab_group_A_subject, lab_group_A_room, lab_group_B_subject, lab_group_B_room = {}, {}, {}, {}
    lab_assignments = (lab_group_A_subject, lab_group_A_room, lab_group_B_subject, lab_group_B_room)

    for section in sections_to_solve:
        dummy_room_A_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "A"]]
        dummy_room_B_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "B"]]
        NO_LAB_SUBJECT_IDX_sec = section_lab_count[section]
        
        for day in days:
            for lab_slot_idx in lab_slot_name_to_id.values():
                subject_domain = [NO_LAB_SUBJECT_IDX_sec]
                room_A_domain, room_B_domain = [dummy_room_A_id], [dummy_room_B_id]
                if available_lab_slots[section][day][lab_slot_idx]:
                    subject_domain.extend(range(NO_LAB_SUBJECT_IDX_sec))
                    room_A_domain.extend(real_lab_room_ids)
                    room_B_domain.extend(real_lab_room_ids)
                lab_group_A_subject[section, day, lab_slot_idx] = model.NewIntVarFromDomain(cp_model.Domain.FromValues(subject_domain), f"lab_A_{section}_{day}_{lab_slot_idx}")
                lab_group_B_subject[section, day, lab_slot_idx] = model.NewIntVarFromDomain(cp_model.Domain.FromValues(subject_domain), f"lab_B_{section}_{day}_{lab_slot_idx}")
                lab_group_A_room[section, day, lab_slot_idx] = model.NewIntVarFromDomain(cp_model.Domain.FromValues(room_A_domain), f"lab_A_r_{section}_{day}_{lab_slot_idx}")
                lab_group_B_room[section, day, lab_slot_idx] = model.NewIntVarFromDomain(cp_model.Domain.FromValues(room_B_domain), f"lab_B_r_{section}_{day}_{lab_slot_idx}")

    # --- (NEW) 3. Constraint 0: Teacher Unavailability ---
    print("Adding teacher unavailability constraints...")
    
    # A. For Theory Classes
    for (section, day, slot), subject_var in new_classes.items():
        if section not in section_teacher_id_list_map: continue
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
        if section not in lab_teacher_id_list_map: continue
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

    print("\nAdding subject frequency constraints (Theory)...")
    for section in sections_to_solve:
        section_vars = [new_classes[s, d, t] for (s, d, t) in new_classes if s == section]
        
        pre_assigned_counts = {subj: 0 for subj in core_subject_map[section]}
        for day in days:
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                if slot not in section_obj: continue
                if section_obj[slot][0]['status'] == "Assigned":
                    subject = section_obj[slot][0].get('subject')
                    if subject in pre_assigned_counts:
                        pre_assigned_counts[subject] += 1
        
        total_needed = sum(max(0, 3 - count) for count in pre_assigned_counts.values())

        if len(section_vars) != total_needed:
            print(f"FATAL ERROR: Section {section} has {len(section_vars)} 'To Be Assigned' slots,"
                  f" but needs {total_needed} to satisfy the '3-per-week' rule after accounting for pre-assigned classes.", file=sys.stderr)
            print(f"Pre-assigned counts: {pre_assigned_counts}", file=sys.stderr)
            print("Please correct data.json and try again.", file=sys.stderr)
            sys.exit(1)

        for subject_name, subject_index in core_subject_map[section].items():
            needed_count = max(0, 3 - pre_assigned_counts[subject_name])
            if needed_count > 0:
                bool_list = [model.NewBoolVar(f"sec_{section}_subj_{subject_index}_var_{i}") for i in range(len(section_vars))]
                for i, var in enumerate(section_vars):
                    model.Add(var == subject_index).OnlyEnforceIf(bool_list[i])
                    model.Add(var != subject_index).OnlyEnforceIf(bool_list[i].Not())
                model.Add(sum(bool_list) == needed_count)
            else:
                # Ensure no more classes are scheduled if 3 are already assigned
                for var in section_vars:
                    model.Add(var != subject_index)


    print("Adding daily subject uniqueness constraints (Theory)...")
    for section in sections_to_solve:
        for day in days:
            daily_vars = [new_classes[s, d, slot] for (s, d, slot) in new_classes if s == section and d == day]
            pre_assigned_subjects_on_day = set()
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                if slot not in section_obj: continue
                if section_obj[slot][0]['status'] == "Assigned":
                    subject = section_obj[slot][0].get('subject')
                    if subject in core_subject_map[section]:
                        pre_assigned_subjects_on_day.add(subject)
            for subject_name, subject_index in core_subject_map[section].items():
                bool_list = [model.NewBoolVar(f"day_{day}_sec_{section}_subj_{subject_index}_var_{i}") for i in range(len(daily_vars))]
                for i, var in enumerate(daily_vars):
                    model.Add(var == subject_index).OnlyEnforceIf(bool_list[i])
                    model.Add(var != subject_index).OnlyEnforceIf(bool_list[i].Not())
                variable_subject_count = sum(bool_list) if bool_list else 0
                model.Add(variable_subject_count == 0) if subject_name in pre_assigned_subjects_on_day else model.Add(variable_subject_count <= 1)

    print("Adding lab parallelism and frequency constraints...")
    for section in sections_to_solve:
        NO_LAB_SUBJECT_IDX_sec = section_lab_count[section]
        if NO_LAB_SUBJECT_IDX_sec == 0: continue
        dummy_room_A_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "A"]]
        dummy_room_B_id = lab_room_name_to_id[dummy_lab_room_id_map[section, "B"]]
        all_gA_subj_vars = [lab_group_A_subject[section, d, s] for d in days for s in lab_slot_name_to_id.values()]
        all_gB_subj_vars = [lab_group_B_subject[section, d, s] for d in days for s in lab_slot_name_to_id.values()]
        for lab_idx in range(NO_LAB_SUBJECT_IDX_sec):
            bool_list_A = [model.NewBoolVar(f"b_freq_A_{section}_lab{lab_idx}_var{i}") for i, _ in enumerate(all_gA_subj_vars)]
            for i, var in enumerate(all_gA_subj_vars):
                model.Add(var == lab_idx).OnlyEnforceIf(bool_list_A[i])
                model.Add(var != lab_idx).OnlyEnforceIf(bool_list_A[i].Not())
            model.Add(sum(bool_list_A) == 1)
            bool_list_B = [model.NewBoolVar(f"b_freq_B_{section}_lab{lab_idx}_var{i}") for i, _ in enumerate(all_gB_subj_vars)]
            for i, var in enumerate(all_gB_subj_vars):
                model.Add(var == lab_idx).OnlyEnforceIf(bool_list_B[i])
                model.Add(var != lab_idx).OnlyEnforceIf(bool_list_B[i].Not())
            model.Add(sum(bool_list_B) == 1)
        for day in days:
            daily_gA_subj_vars = [lab_group_A_subject[section, day, s] for s in lab_slot_name_to_id.values()]
            bool_list_A_daily = [model.NewBoolVar(f"b_daily_A_{section}_{day}_var{i}") for i, _ in enumerate(daily_gA_subj_vars)]
            for i, var in enumerate(daily_gA_subj_vars):
                model.Add(var != NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(bool_list_A_daily[i])
                model.Add(var == NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(bool_list_A_daily[i].Not())
            model.Add(sum(bool_list_A_daily) <= 2)
            daily_gB_subj_vars = [lab_group_B_subject[section, day, s] for s in lab_slot_name_to_id.values()]
            bool_list_B_daily = [model.NewBoolVar(f"b_daily_B_{section}_{day}_var{i}") for i, _ in enumerate(daily_gB_subj_vars)]
            for i, var in enumerate(daily_gB_subj_vars):
                model.Add(var != NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(bool_list_B_daily[i])
                model.Add(var == NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(bool_list_B_daily[i].Not())
            model.Add(sum(bool_list_B_daily) <= 2)
            for lab_slot_idx in lab_slot_name_to_id.values():
                gA_subj, gB_subj = lab_group_A_subject[section, day, lab_slot_idx], lab_group_B_subject[section, day, lab_slot_idx]
                gA_room, gB_room = lab_group_A_room[section, day, lab_slot_idx], lab_group_B_room[section, day, lab_slot_idx]
                b_A, b_B = model.NewBoolVar(f"b_A_{section}_{day}_{lab_slot_idx}"), model.NewBoolVar(f"b_B_{section}_{day}_{lab_slot_idx}")
                model.Add(gA_subj != NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(b_A)
                model.Add(gA_subj == NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(b_A.Not())
                model.Add(gB_subj != NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(b_B)
                model.Add(gB_subj == NO_LAB_SUBJECT_IDX_sec).OnlyEnforceIf(b_B.Not())
                model.Add(b_A == b_B)
                model.Add(gA_subj != gB_subj).OnlyEnforceIf(b_A)
                model.Add(gA_room != gB_room).OnlyEnforceIf(b_A)
                model.Add(gA_room != dummy_room_A_id).OnlyEnforceIf(b_A)
                model.Add(gA_room == dummy_room_A_id).OnlyEnforceIf(b_A.Not())
                model.Add(gB_room != dummy_room_B_id).OnlyEnforceIf(b_B)
                model.Add(gB_room == dummy_room_B_id).OnlyEnforceIf(b_B.Not())

    print("Adding combined resource uniqueness constraints...")
    for day in days:
        for slot in slots:
            teacher_vars, theory_room_vars, lab_room_vars = [], [], []
            for section in all_sections_in_config:
                list_index = section_index_map[day][section]
                if slot not in timetable_data[day][list_index]: continue
                slot_info = timetable_data[day][list_index][slot][0]
                if slot_info['status'] == "Assigned":
                    t, r = slot_info.get('teacher'), slot_info.get('room')
                    if t and "/" not in str(t) and t in teacher_name_to_id: teacher_vars.append(model.NewConstant(teacher_name_to_id[t]))
                    elif t and "/" in str(t):
                         t1, t2 = [x.strip() for x in t.split('/')]
                         if t1 in teacher_name_to_id: teacher_vars.append(model.NewConstant(teacher_name_to_id[t1]))
                         if t2 in teacher_name_to_id: teacher_vars.append(model.NewConstant(teacher_name_to_id[t2]))
                    if r and "/" not in str(r) and r in theory_room_name_to_id: theory_room_vars.append(model.NewConstant(theory_room_name_to_id[r]))
                    elif r and "/" in str(r):
                         r1, r2 = [x.strip() for x in r.split('/')]
                         if r1 in lab_room_name_to_id: lab_room_vars.append(model.NewConstant(lab_room_name_to_id[r1]))
                         if r2 in lab_room_name_to_id: lab_room_vars.append(model.NewConstant(lab_room_name_to_id[r2]))
            for (section, d, t), var in new_classes.items():
                if d == day and t == slot:
                    theory_room_vars.append(model.NewConstant(theory_room_name_to_id[config_data['section_theory_rooms'][section]]))
                    teacher_opts = section_teacher_id_list_map[section]
                    teacher_var = model.NewIntVarFromDomain(cp_model.Domain.FromValues([o for o in teacher_opts if o!=-1]), f"t_{section}_{day}_{slot}")
                    model.AddElement(var, teacher_opts, teacher_var)
                    teacher_vars.append(teacher_var)
            lab_slot_name = theory_slot_to_lab_slot_map.get(slot)
            if lab_slot_name:
                lab_slot_idx = lab_slot_name_to_id[lab_slot_name]
                for section in sections_to_solve:
                    if section_lab_count[section] == 0: continue
                    dummy_A_id, dummy_B_id = teacher_name_to_id[dummy_teacher_id_map[section,"A"]], teacher_name_to_id[dummy_teacher_id_map[section,"B"]]
                    
                    gA_s, gA_r = lab_group_A_subject[section,day,lab_slot_idx], lab_group_A_room[section,day,lab_slot_idx]
                    gA_t = model.NewIntVar(0, len(teacher_name_to_id)-1, f"l_A_t_{section}_{day}_{slot}")
                    teacher_list_A = lab_teacher_id_list_map[section] + [dummy_A_id]
                    model.AddElement(gA_s, teacher_list_A, gA_t)
                    teacher_vars.append(gA_t)
                    lab_room_vars.append(gA_r)

                    gB_s, gB_r = lab_group_B_subject[section,day,lab_slot_idx], lab_group_B_room[section,day,lab_slot_idx]
                    gB_t = model.NewIntVar(0, len(teacher_name_to_id)-1, f"l_B_t_{section}_{day}_{slot}")
                    teacher_list_B = lab_teacher_id_list_map[section] + [dummy_B_id]
                    model.AddElement(gB_s, teacher_list_B, gB_t)
                    teacher_vars.append(gB_t)
                    lab_room_vars.append(gB_r)
            
            if teacher_vars: model.AddAllDifferent(teacher_vars)
            if theory_room_vars: model.AddAllDifferent(theory_room_vars)
            if lab_room_vars: model.AddAllDifferent(lab_room_vars)

    print("\nStarting solver for 7th Semester...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config_data['settings']['solver_timeout_seconds']
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        save_solution(solver, new_classes, lab_assignments, timetable_data, config_data,
                      sections_to_solve, inv_core_subject_map, teacher_subject_map,
                      inv_lab_name_map, lab_teacher_map, inv_lab_room_id_to_name,
                      inv_lab_slot_id_to_name, lab_slot_map, section_index_map, output_path)
    elif status == cp_model.INFEASIBLE:
        print("No solution found: The problem is infeasible.")
        print("Check constraints, especially room/teacher clashes or lack of 'Free' slots for labs.")
        print("ALSO: Check that 'To Be Assigned' slots in data.json match the dynamically calculated requirement.")
    else:
        print(f"No solution found. Solver status: {status}")

if __name__ == "__main__":
    main()