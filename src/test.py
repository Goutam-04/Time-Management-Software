import json
import sys

def check_unavailability():
    """
    Checks the generated updated_timetable.json against a hard-coded
    list of teacher unavailability constraints.
    """
    
    # 1. Define the Unavailability Rules (copy/pasted from your list)
    teacher_unavailability = {
        # TEACHER SA
        "SA": {"Monday": ["11-12", "12-1", "3-4"], "Wednesday": ["9-10"], "Thursday": ["11-12"]},
        # TEACHER EO
        "EO": {"Tuesday": ["10-11", "11-12", "12-1"], "Wednesday": ["12-1"], "Thursday": ["3-4"], "Friday": ["9-10", "10-11"]},
        # TEACHER GF7
        "GF7": {"Monday": ["2-3"], "Tuesday": ["12-1"], "Wednesday": ["9-10"], "Thursday": ["3-4", "4-5"]},
        # TEACHER SPS
        "SPS": {"Monday": ["9-10"], "Wednesday": ["11-12", "12-1", "4-5"], "Friday": ["10-11"]},
        # TEACHER GF8
        "GF8": {"Monday": ["12-1"], "Tuesday": ["11-12", "12-1"], "Wednesday": ["11-12"], "Thursday": ["3-4"]},
        # TEACHER SS
        "SS": {"Tuesday": ["10-11"], "Wednesday": ["11-12"], "Thursday": ["11-12", "12-1"], "Friday": ["3-4"]},
        # TEACHER GF9
        "GF9": {"Monday": ["3-4"], "Tuesday": ["11-12", "3-4", "4-5"], "Wednesday": ["3-4"]},
        # TEACHER GF10
        "GF10": {"Monday": ["3-4", "4-5"], "Tuesday": ["9-10"], "Thursday": ["10-11"], "Friday": ["12-1"]},
        # TEACHER AS
        "AS": {"Monday": ["3-4", "4-5"]},
        # TEACHER SP
        "SP": {"Tuesday": ["3-4", "4-5"]},
        # TEACHER KN
        "KN": {"Thursday": ["3-4", "4-5"]},
    }

    # 2. Load the generated timetable
    try:
        with open('updated_timetable.json', 'r') as f:
            timetable = json.load(f)
    except FileNotFoundError:
        print("❌ Error: 'updated_timetable.json' not found.")
        print("Please run 'python solver.py' first to generate it.")
        sys.exit(1)
        
    # 3. Load config for days/slots
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: 'config.json' not found.")
        sys.exit(1)
        
    days = config['settings']['days']
    slots = config['settings']['all_slots']
    
    violations = 0
    print("🕵️  Checking 'updated_timetable.json' against unavailability constraints...")
    
    # 4. Iterate through all assigned slots and check for violations
    for day in days:
        for section_obj in timetable.get(day, []):
            for slot in slots:
                if slot not in section_obj: continue
                
                slot_info = section_obj[slot][0]
                
                if slot_info.get('status') == "Assigned":
                    teacher_str = slot_info.get('teacher')
                    if not teacher_str: continue
                    
                    # This handles both single theory teachers ("SS")
                    # and parallel lab teachers ("SK / SS")
                    teachers_in_slot = [t.strip() for t in teacher_str.split('/')]
                    
                    for teacher in teachers_in_slot:
                        if teacher in teacher_unavailability:
                            if day in teacher_unavailability[teacher] and slot in teacher_unavailability[teacher][day]:
                                print(f"\n--- 🔴 VIOLATION FOUND! ---")
                                print(f"  Teacher:  {teacher}")
                                print(f"  Section:  {section_obj['section']}")
                                print(f"  When:     {day} at {slot}")
                                print(f"  Subject:  {slot_info.get('subject')}")
                                print(f"  Problem:  Teacher is scheduled but listed as unavailable at this time.\n")
                                violations += 1

    if violations == 0:
        print("\n✅ SUCCESS: No unavailability constraint violations found.")
    else:
        print(f"\n❌ FAILED: Found {violations} total violations.")
        
    print("Check complete.")

if __name__ == "__main__":
    check_unavailability()