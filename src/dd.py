#!/usr/bin/env python
"""
Detailed conflict analyzer for 7th semester timetable
This will show EXACTLY why the solver fails
"""

import json
from collections import defaultdict

def load_data():
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Try to load updated_timetable.json first (after 5th sem solver)
    try:
        with open('updated_timetable.json', 'r') as f:
            data = json.load(f)
            print("Analyzing updated_timetable.json (includes 3rd and 5th sem solutions)")
    except:
        with open('data.json', 'r') as f:
            data = json.load(f)
            print("Analyzing data.json (original)")
    
    return config, data

def main():
    config, data = load_data()
    
    sections_7th = ["CSE-7", "IT-7"]
    all_sections = config['sections']
    days = config['settings']['days']
    slots = config['settings']['all_slots']
    
    # Build mappings
    section_index_map = {d: {} for d in days}
    for day in days:
        for i, section_obj in enumerate(data[day]):
            section_index_map[day][section_obj['section']] = i
    
    print("\n" + "="*80)
    print("CONFLICT ANALYSIS FOR 7TH SEMESTER")
    print("="*80)
    
    # Build teacher and room schedules from ASSIGNED slots
    teacher_busy = defaultdict(lambda: defaultdict(list))  # teacher -> day -> [(slot, section)]
    room_busy = defaultdict(lambda: defaultdict(list))      # room -> day -> [(slot, section)]
    lab_room_busy = defaultdict(lambda: defaultdict(list))  # lab_room -> day -> [(slot, section)]
    
    for day in days:
        for section_obj in data[day]:
            section = section_obj['section']
            for slot in slots:
                slot_info = section_obj[slot][0]
                if slot_info['status'] == "Assigned":
                    teacher = slot_info.get('teacher', '')
                    room = slot_info.get('room', '')
                    
                    # Handle teachers
                    if teacher and "/" not in str(teacher):
                        if "TBD" not in str(teacher):
                            teacher_busy[teacher][day].append((slot, section))
                    elif teacher and "/" in str(teacher):
                        for t in teacher.split('/'):
                            t = t.strip()
                            if "TBD" not in t:
                                teacher_busy[t][day].append((slot, section))
                    
                    # Handle rooms
                    if room and "/" not in str(room):
                        room_busy[room][day].append((slot, section))
                    elif room and "/" in str(room):
                        for r in room.split('/'):
                            r = r.strip()
                            lab_room_busy[r][day].append((slot, section))
    
    # Check 1: Theory class conflicts
    print("\n1. CHECKING THEORY CLASS SCHEDULING:")
    print("-" * 80)
    
    for section in sections_7th:
        print(f"\n{section}:")
        core_subjects = config['core_subjects'][section]
        print(f"  Core subjects: {', '.join(core_subjects)}")
        
        # Get teachers for this section
        teacher_map = {s: t for s, t in config['subjects'][section]}
        
        # Check each day's TBA slots
        conflicts_found = False
        for day in days:
            idx = section_index_map[day][section]
            section_obj = data[day][idx]
            
            tba_slots = [slot for slot in slots if section_obj[slot][0]['status'] == "To Be Assigned"]
            
            if tba_slots:
                print(f"\n  {day} - TBA slots: {', '.join(tba_slots)}")
                
                # For each TBA slot, check if ANY of the section's teachers are busy
                for slot in tba_slots:
                    busy_teachers = []
                    for subj in core_subjects:
                        teacher = teacher_map.get(subj, '')
                        if teacher in teacher_busy and day in teacher_busy[teacher]:
                            for busy_slot, busy_sec in teacher_busy[teacher][day]:
                                if busy_slot == slot:
                                    busy_teachers.append(f"{teacher}({subj}) teaching {busy_sec}")
                                    conflicts_found = True
                    
                    if busy_teachers:
                        print(f"    ✗ {slot}: CONFLICT - {'; '.join(busy_teachers)}")
                    else:
                        print(f"    ✓ {slot}: Available")
        
        # Check room availability
        assigned_room = config['section_theory_rooms'][section]
        print(f"\n  Assigned room: {assigned_room}")
        room_conflicts = False
        for day in days:
            if day in room_busy[assigned_room]:
                idx = section_index_map[day][section]
                section_obj = data[day][idx]
                tba_slots = [slot for slot in slots if section_obj[slot][0]['status'] == "To Be Assigned"]
                
                for slot, other_sec in room_busy[assigned_room][day]:
                    if slot in tba_slots:
                        print(f"    ✗ {day} {slot}: Room occupied by {other_sec}")
                        room_conflicts = True
        
        if not room_conflicts:
            print(f"    ✓ Room available in all TBA slots")
    
    # Check 2: Lab scheduling conflicts
    print("\n\n2. CHECKING LAB SCHEDULING:")
    print("-" * 80)
    
    lab_slot_map = {
        "9-11": ("9-10", "10-11"),
        "11-1": ("11-12", "12-1"),
        "3-5": ("3-4", "4-5")
    }
    
    all_lab_rooms = config['lab_rooms']
    
    for section in sections_7th:
        print(f"\n{section}:")
        labs = config['labs'][section]
        print(f"  Labs: {', '.join(labs)}")
        print(f"  Need: {len(labs)} slots (1 per lab, both groups parallel)")
        
        teacher_map = {s: t for s, t in config['subjects'][section]}
        
        available_count = 0
        conflicts_by_day = defaultdict(list)
        
        for day in days:
            idx = section_index_map[day][section]
            section_obj = data[day][idx]
            
            for lab_slot_name, (slot1, slot2) in lab_slot_map.items():
                is_free = (slot1 in section_obj and slot2 in section_obj and
                          section_obj[slot1][0]['status'] == "Free" and
                          section_obj[slot2][0]['status'] == "Free")
                
                if is_free:
                    available_count += 1
                    
                    # Check if lab rooms are available
                    rooms_available = []
                    rooms_busy = []
                    
                    for room in all_lab_rooms:
                        room_free = True
                        for check_slot in [slot1, slot2]:
                            if check_slot in [s for s, _ in lab_room_busy[room][day]]:
                                room_free = False
                                break
                        if room_free:
                            rooms_available.append(room)
                        else:
                            rooms_busy.append(room)
                    
                    # Check if teachers are available
                    teachers_available = []
                    teachers_busy = []
                    
                    for lab in labs:
                        # Get teacher for this lab
                        theory_subj = lab.split(" ")[0]
                        teacher = teacher_map.get(theory_subj, teacher_map.get(lab, ''))
                        
                        teacher_free = True
                        if teacher and teacher in teacher_busy:
                            for check_slot in [slot1, slot2]:
                                if check_slot in [s for s, _ in teacher_busy[teacher][day]]:
                                    teachers_busy.append(f"{teacher}({lab})")
                                    teacher_free = False
                                    break
                        
                        if teacher_free:
                            teachers_available.append(f"{teacher}({lab})")
                    
                    # We need 2 rooms and 2 teachers (for parallel groups)
                    if len(rooms_available) >= 2 and len(teachers_available) >= len(labs):
                        conflicts_by_day[day].append(f"✓ {lab_slot_name}: OK ({len(rooms_available)} rooms free)")
                    else:
                        conflict_msg = f"✗ {lab_slot_name}: "
                        if len(rooms_available) < 2:
                            conflict_msg += f"Only {len(rooms_available)} lab rooms free (need 2). "
                        if len(teachers_available) < len(labs):
                            conflict_msg += f"Teachers busy: {', '.join(teachers_busy)}"
                        conflicts_by_day[day].append(conflict_msg)
        
        print(f"  Total available 2-hour slots: {available_count}")
        for day in days:
            if conflicts_by_day[day]:
                print(f"\n  {day}:")
                for msg in conflicts_by_day[day]:
                    print(f"    {msg}")
    
    # Check 3: Summary of potential issues
    print("\n\n3. POTENTIAL ISSUES SUMMARY:")
    print("-" * 80)
    
    issues = []
    
    for section in sections_7th:
        # Count constraints
        core_subjects = config['core_subjects'][section]
        labs = config['labs'][section]
        
        tba_total = 0
        for day in days:
            idx = section_index_map[day][section]
            section_obj = data[day][idx]
            tba_total += sum(1 for slot in slots if section_obj[slot][0]['status'] == "To Be Assigned")
        
        needed = len(core_subjects) * 3
        if tba_total != needed:
            issues.append(f"{section}: TBA slots ({tba_total}) ≠ required ({needed})")
        
        # Count free lab slots
        free_lab_slots = 0
        for day in days:
            idx = section_index_map[day][section]
            section_obj = data[day][idx]
            for lab_slot_name, (s1, s2) in lab_slot_map.items():
                if (s1 in section_obj and s2 in section_obj and
                    section_obj[s1][0]['status'] == "Free" and
                    section_obj[s2][0]['status'] == "Free"):
                    free_lab_slots += 1
        
        needed_labs = len(labs)
        if free_lab_slots < needed_labs:
            issues.append(f"{section}: Free lab slots ({free_lab_slots}) < required ({needed_labs})")
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  ✗ {issue}")
    else:
        print("No obvious slot count issues found.")
        print("\nThe infeasibility is likely due to:")
        print("  1. Teacher conflicts (teachers busy in TBA slots)")
        print("  2. Lab room conflicts (not enough rooms available simultaneously)")
        print("  3. Over-constrained daily uniqueness (subjects can't fit in available slots)")
    
    print("\n" + "="*80)
    print("Run this to see the full picture of what's causing infeasibility.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()