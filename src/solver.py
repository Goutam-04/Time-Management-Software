#!/usr/bin/env python
# solver.py
"""
Solves the university timetable problem for 3rd-semester sections
using Google OR-Tools CP-SAT solver.

Reads from:
- config.json (rules, subjects, rooms)
- data.json (current timetable)

Writes to:
- updated_timetable.json (solved timetable)
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

def save_solution(solver, new_classes, timetable_data, config_data, 
                  sections_to_solve, inv_core_subject_map, 
                  teacher_subject_map, section_index_map, output_path):
    """
    Populates a copy of the timetable with the solved values and saves it.
    """
    print(f"Solution found. Saving to {output_path}...")
    
    # Create a deep copy to avoid modifying the original data
    timetable_copy = copy.deepcopy(timetable_data)

    # Iterate over the variables we created and update the timetable copy
    for (section, day, slot), var in new_classes.items():
        # Get the solved value for this variable
        subject_index = solver.Value(var)
        
        # Map index back to subject name
        subject_name = inv_core_subject_map[section][subject_index]
        
        # Find the corresponding teacher and room
        teacher_name = teacher_subject_map[section][subject_name]
        room_name = config_data['section_theory_rooms'][section]
        
        # Find the correct object in the timetable data to update
        list_index = section_index_map[day][section]
        slot_info = timetable_copy[day][list_index][slot][0]
        
        # Update the slot information
        slot_info['status'] = "Assigned"
        slot_info['subject'] = subject_name
        slot_info['teacher'] = teacher_name
        slot_info['room'] = room_name

    # Write the updated data to the output file
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
    config_path = 'config.json'
    data_path = 'data.json'
    output_path = 'updated_timetable.json'
    
    config_data, timetable_data = load_data(config_path, data_path)

    # --- 2. Define Problem Scope ---
    
    # As requested, only solve for 3rd-semester sections
    sections_to_solve = ["CSE-A-3", "CSE-B-3", "CSE-AIML-3"]
    
    all_sections = config_data['sections']
    days = config_data['settings']['days']
    slots = config_data['settings']['all_slots']

    # --- 3. Pre-process Data and Build Mappings ---
    
    core_subject_map = {}     # {section: {subject_name: index}}
    inv_core_subject_map = {} # {section: {index: subject_name}}
    teacher_subject_map = {}  # {section: {subject_name: teacher_name}}
    tba_slots_by_section = {s: [] for s in sections_to_solve}
    section_index_map = {d: {} for d in days} # {day: {section: list_index}}

    all_teachers = set()
    all_rooms = set()

    # Populate section index map for quick lookups
    for day in days:
        for i, section_obj in enumerate(timetable_data[day]):
            section_index_map[day][section_obj['section']] = i

    # Populate teacher/room sets from pre-assigned classes
    for day in days:
        for section_obj in timetable_data[day]:
            for slot in slots:
                slot_info = section_obj[slot][0]
                if slot_info['status'] == "Assigned":
                    teacher = slot_info.get('teacher')
                    room = slot_info.get('room')
                    if teacher and "TBD" not in str(teacher):
                        all_teachers.add(teacher)
                    if room:
                        all_rooms.add(room)

    # Populate mappings for the sections we need to solve
    for section in sections_to_solve:
        core_subjects = config_data['core_subjects'][section]
        core_subject_map[section] = {subject: i for i, subject in enumerate(core_subjects)}
        inv_core_subject_map[section] = {i: subject for i, subject in enumerate(core_subjects)}
        
        teacher_subject_map[section] = {}
        for subject, teacher in config_data['subjects'][section]:
            if subject in core_subject_map[section]:
                teacher_subject_map[section][subject] = teacher
                all_teachers.add(teacher) # Add core subject teachers
        
        all_rooms.add(config_data['section_theory_rooms'][section]) # Add home rooms
    
    # Find all "To Be Assigned" slots
    for day in days:
        for section in sections_to_solve:
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                if section_obj[slot][0]['status'] == "To Be Assigned":
                    tba_slots_by_section[section].append((day, slot))

    # Create final integer mappings for all resources
    teacher_name_to_id = {name: i for i, name in enumerate(sorted(list(all_teachers)))}
    room_name_to_id = {name: i for i, name in enumerate(sorted(list(all_rooms)))}

    # Map section's core teacher names to their integer IDs
    # This is for the AddElement constraint
    section_teacher_id_list_map = {}
    for section in sections_to_solve:
        core_subjects = config_data['core_subjects'][section]
        teacher_ids = []
        for subject in core_subjects:
            teacher_name = teacher_subject_map[section][subject]
            teacher_ids.append(teacher_name_to_id[teacher_name])
        section_teacher_id_list_map[section] = teacher_ids

    # --- 4. Initialize CP-SAT Model ---
    model = cp_model.CpModel()

    # --- 5. Create Model Variables ---
    
    # new_classes[(section, day, slot)] = subject_index_variable
    new_classes = {}
    
    for section in sections_to_solve:
        num_core_subjects = len(core_subject_map[section])
        for (day, slot) in tba_slots_by_section[section]:
            new_classes[section, day, slot] = model.NewIntVar(
                0, num_core_subjects - 1, f"class_{section}_{day}_{slot}"
            )

    # --- 6. Add Constraints ---

    # Constraint 1: Subject Frequency
    # Each core subject must be scheduled 3 times per week.
    print("Adding subject frequency constraints...")
    for section in sections_to_solve:
        section_vars = [new_classes[s, d, t] for (s, d, t) in new_classes if s == section]
        
        # Check for feasibility
        num_required = len(core_subject_map[section]) * 3
        if len(section_vars) != num_required:
            print(f"Error: Section {section} has {len(section_vars)} 'To Be Assigned' slots,"
                  f" but needs {num_required} (4 subjects * 3 times).", file=sys.stderr)
            print("Please check data.json. Cannot solve.", file=sys.stderr)
            sys.exit(1)

        for j in range(len(core_subject_map[section])):
            # This is the robust, "reified" way to implement a count
            # for older OR-Tools versions that lack model.AddCount().
            
            # 1. Create a list of new boolean variables
            bool_list = []
            for i in range(len(section_vars)):
                bool_list.append(
                    model.NewBoolVar(f"sec_{section}_subj_{j}_var_{i}")
                )
            
            # 2. Link each boolean var to the condition
            # b is true if and only if section_var == j
            for i in range(len(section_vars)):
                var = section_vars[i]
                b = bool_list[i]
                # Enforce: b == (var == j)
                model.Add(var == j).OnlyEnforceIf(b)
                model.Add(var != j).OnlyEnforceIf(b.Not())
                
            # 3. Sum the boolean variables and constrain to 3
            # Python's built-in sum() works here because bool_list 
            # contains variables, which can be summed into a LinearExpr.
            model.Add(sum(bool_list) == 3)

    # Constraint 2: Resource Uniqueness (Teachers and Rooms)
    # No teacher or room can be in two places at once.
    print("Adding resource uniqueness constraints...")
    for day in days:
        for slot in slots:
            teacher_vars_at_slot = []
            room_vars_at_slot = []
            
            for section in all_sections:
                list_index = section_index_map[day][section]
                slot_info = timetable_data[day][list_index][slot][0]
                status = slot_info['status']
                
                if status == "Assigned":
                    # This is a pre-assigned, fixed class
                    teacher = slot_info.get('teacher')
                    room = slot_info.get('room')
                    
                    if teacher and teacher in teacher_name_to_id:
                        teacher_id = teacher_name_to_id[teacher]
                        teacher_vars_at_slot.append(model.NewConstant(teacher_id))
                    
                    if room and room in room_name_to_id:
                        room_id = room_name_to_id[room]
                        room_vars_at_slot.append(model.NewConstant(room_id))

                elif status == "To Be Assigned" and section in sections_to_solve:
                    # This is a variable class we are solving
                    
                    # 1. Add Room
                    room_name = config_data['section_theory_rooms'][section]
                    room_id = room_name_to_id[room_name]
                    room_vars_at_slot.append(model.NewConstant(room_id))
                    
                    # 2. Add Teacher (as a variable linked to the subject)
                    subject_var = new_classes[section, day, slot]
                    teacher_options = section_teacher_id_list_map[section]
                    
                    teacher_var = model.NewIntVarFromDomain(
                        cp_model.Domain.FromValues(teacher_options), 
                        f"teacher_{section}_{day}_{slot}"
                    )
                    
                    # Link subject variable to teacher variable:
                    # teacher_var = teacher_options[subject_var]
                    model.AddElement(subject_var, teacher_options, teacher_var)
                    teacher_vars_at_slot.append(teacher_var)

            # Add the "all different" constraint for this specific time slot
            if teacher_vars_at_slot:
                model.AddAllDifferent(teacher_vars_at_slot)
            if room_vars_at_slot:
                model.AddAllDifferent(room_vars_at_slot)
    # Constraint 3: Daily Subject Uniqueness
    # A section cannot have the same core subject more than once on the same day.
    print("Adding daily subject uniqueness constraints...")
    for section in sections_to_solve:
        num_core_subjects = len(core_subject_map[section])
        
        for day in days:
            # 1. Get all variable slots for this section and day
            daily_vars = []
            for (s, d, slot) in new_classes:
                if s == section and d == day:
                    daily_vars.append(new_classes[s, d, slot])

            # If there are no variable slots on this day, skip
            if not daily_vars:
                continue

            # 2. Check pre-assigned slots for this section and day
            pre_assigned_subjects_on_day = set()
            list_index = section_index_map[day][section]
            section_obj = timetable_data[day][list_index]
            for slot in slots:
                slot_info = section_obj[slot][0]
                if slot_info['status'] == "Assigned":
                    subject = slot_info.get('subject')
                    # Check if it's one of the core subjects we care about
                    if subject and subject in core_subject_map[section]:
                        pre_assigned_subjects_on_day.add(subject)

            # 3. Add constraints for each subject
            for subject_name, subject_index in core_subject_map[section].items():
                
                # We need to count how many times this subject appears
                # in the *variable* slots for this day
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
                
                # This is the total count for this subject from *variable* slots
                variable_subject_count = sum(bool_list)
                
                # Now, apply the logic
                if subject_name in pre_assigned_subjects_on_day:
                    # If pre-assigned, it CANNOT appear in any variable slots
                    model.Add(variable_subject_count == 0)
                else:
                    # If not pre-assigned, it can appear AT MOST once
                    model.Add(variable_subject_count <= 1)
    # --- 7. Solve the Model ---
    print("\nStarting solver...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config_data['settings']['solver_timeout_seconds']
    status = solver.Solve(model)

    # --- 8. Process Solution ---
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        save_solution(
            solver, new_classes, timetable_data, config_data,
            sections_to_solve, inv_core_subject_map,
            teacher_subject_map, section_index_map, output_path
        )
    elif status == cp_model.INFEASIBLE:
        print("No solution found: The problem is infeasible.")
        print("Check constraints, especially room/teacher clashes.")
    elif status == cp_model.MODEL_INVALID:
        print("No solution found: The model is invalid.")
    else:
        print(f"No solution found. Solver status: {status}")

if __name__ == "__main__":
    main()