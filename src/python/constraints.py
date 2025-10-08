# constraints.py

def add_hard_constraints(model, class_vars, config):
    """Adds all the mandatory (hard) constraints to the model."""
    _add_resource_uniqueness(model, class_vars, config)
    _add_scheduling_rules(model, class_vars, config)
    _add_workload_limits(model, class_vars, config)
    _add_teacher_constraints(model, class_vars, config)
    _add_section_recess_constraints(model, class_vars, config)
    
    # --- ADDED NEW HARD CONSTRAINTS ---
    _add_parallel_lab_constraint(model, class_vars, config)
    _add_fixed_schedules_and_unavailability(model, class_vars, config)


def add_soft_constraints(model, class_vars, config, penalties):
    """Adds soft constraints to improve timetable quality."""
    _add_continuous_blocks_preference(model, class_vars, config, penalties)


# ---------------- HARD CONSTRAINTS ---------------- #

def _add_resource_uniqueness(model, class_vars, config):
    """Ensures rooms, teachers, and sections are not double-booked."""
    # 1. A room can have only one class per slot
    for day_idx in range(len(config.DAYS)):
        for slot_idx in range(len(config.ALL_SLOTS)):
            for room in config.ALL_ROOMS:
                active_in_slot = []
                for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                    if d == day_idx and rm == room:
                        if ('Lab' in subj and (s == slot_idx or s + 1 == slot_idx)) or \
                           ('Lab' not in subj and s == slot_idx):
                            active_in_slot.append(var)
                model.AddAtMostOne(active_in_slot)

    # 2. A teacher can teach only one class per slot
    for day_idx in range(len(config.DAYS)):
        for slot_idx in range(len(config.ALL_SLOTS)):
            for teacher in config.ALL_TEACHERS:
                active_in_slot = []
                for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                    if d == day_idx and tc == teacher:
                        if ('Lab' in subj and (s == slot_idx or s + 1 == slot_idx)) or \
                           ('Lab' not in subj and s == slot_idx):
                            active_in_slot.append(var)
                model.AddAtMostOne(active_in_slot)

    # 3. A section/group can have only one class per slot
    for section in config.SECTIONS:
        for group in config.GROUPS + ['ALL']:
            for day_idx in range(len(config.DAYS)):
                for slot_idx in range(len(config.ALL_SLOTS)):
                    active_in_slot = []
                    for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                        if sec == section and d == day_idx and (grp == group or (group == 'ALL' and grp in config.GROUPS)):
                            if ('Lab' in subj and (s == slot_idx or s + 1 == slot_idx)) or \
                               ('Lab' not in subj and s == slot_idx):
                                active_in_slot.append(var)
                    model.AddAtMostOne(active_in_slot)

def _add_scheduling_rules(model, class_vars, config):
    """Adds specific rules like class counts."""
    # 4. Each theory subject taught exactly 3 times a week
    for section, section_subjects in config.SUBJECTS.items():
        for subject, teacher in section_subjects:
            vars_for_subject = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                                if sec == section and subj == subject]
            if vars_for_subject:
                model.Add(sum(vars_for_subject) == 3)

    # 5. Each lab for each group scheduled exactly once
    for section, section_labs in config.LABS.items():
        for lab_name in section_labs:
            for group in config.GROUPS:
                vars_for_lab = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                                if sec == section and grp == group and subj == lab_name]
                if vars_for_lab:
                    model.AddExactlyOne(vars_for_lab)

def _add_workload_limits(model, class_vars, config):
    """Adds rules to limit the number of classes per day."""
    # 6. Max 4 theory classes per section per day
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            daily_theory = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                            if sec == section and d == day_idx and 'Lab' not in subj]
            model.Add(sum(daily_theory) <= 4)

    # 7. Max 2 labs per section per group per day
    for section in config.SECTIONS:
        for group in config.GROUPS:
            for day_idx in range(len(config.DAYS)):
                daily_labs = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                              if sec == section and grp == group and d == day_idx and 'Lab' in subj]
                model.Add(sum(daily_labs) <= 2)

def _add_teacher_constraints(model, class_vars, config):
    """A teacher can teach at most one class per section per day + recess rule."""
    slot_12_1_idx = config.ALL_SLOTS.index("12-1")
    slot_2_3_idx = config.ALL_SLOTS.index("2-3")
    for teacher in config.ALL_TEACHERS:
        for section in config.SECTIONS:
            for day_idx in range(len(config.DAYS)):
                classes_for_teacher = [
                    var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                    if tc == teacher and sec == section and d == day_idx
                ]
                if classes_for_teacher:
                    model.Add(sum(classes_for_teacher) <= 1)
        # Recess rule for teachers
        for day_idx in range(len(config.DAYS)):
            busy_at_12 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                          if tc == teacher and d == day_idx and s == slot_12_1_idx]
            busy_at_2 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                         if tc == teacher and d == day_idx and s == slot_2_3_idx]
            if busy_at_12 and busy_at_2:
                model.Add(sum(busy_at_12) + sum(busy_at_2) <= 1)

def _add_section_recess_constraints(model, class_vars, config):
    """Recess rule also applies to sections."""
    slot_12_1_idx = config.ALL_SLOTS.index("12-1")
    slot_2_3_idx = config.ALL_SLOTS.index("2-3")
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            busy_at_12 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                          if sec == section and d == day_idx and s == slot_12_1_idx]
            busy_at_2 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                         if sec == section and d == day_idx and s == slot_2_3_idx]
            if busy_at_12 and busy_at_2:
                model.Add(sum(busy_at_12) + sum(busy_at_2) <= 1)

# --- NEW HARD CONSTRAINT FUNCTION ---
def _add_parallel_lab_constraint(model, class_vars, config):
    """Ensures that labs for Group A and Group B of the same subject run in parallel."""
    for section, section_labs in config.LABS.items():
        for lab_name in section_labs:
            for day_idx in range(len(config.DAYS)):
                for slot_idx, slot in enumerate(config.ALL_SLOTS):
                    if slot not in config.LAB_SLOT_STARTS:
                        continue
                    
                    # Find potential variables for this lab session for each group
                    gA_vars = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                               if sec == section and subj == lab_name and grp == 'A' and d == day_idx and s == slot_idx]
                    gB_vars = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                               if sec == section and subj == lab_name and grp == 'B' and d == day_idx and s == slot_idx]

                    if not gA_vars or not gB_vars:
                        continue
                    
                    # Create boolean variables to indicate if a group is active in this slot
                    gA_active = model.NewBoolVar(f'{section}_{lab_name}_d{day_idx}_s{slot_idx}_gA_active')
                    gB_active = model.NewBoolVar(f'{section}_{lab_name}_d{day_idx}_s{slot_idx}_gB_active')

                    # Link the booleans to the sum of variables
                    model.Add(sum(gA_vars) > 0).OnlyEnforceIf(gA_active)
                    model.Add(sum(gA_vars) == 0).OnlyEnforceIf(gA_active.Not())
                    model.Add(sum(gB_vars) > 0).OnlyEnforceIf(gB_active)
                    model.Add(sum(gB_vars) == 0).OnlyEnforceIf(gB_active.Not())
                    
                    # Enforce that their active status must be the same
                    model.Add(gA_active == gB_active)

# --- FINALIZED FUNCTION WITH ALL RULES ---
def _add_fixed_schedules_and_unavailability(model, class_vars, config):
    """Adds hard constraints for fixed schedules and teacher/section non-availability."""
    
    # Helper to find a specific class variable
    def get_class_var(section, subject, day_idx, slot_idx):
        for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
            if sec == section and subj == subject and d == day_idx and s == slot_idx:
                return var
        return None

    # --- 1. Fixed Schedule for 3rd Semester (from PDF) ---
    fixed_classes_3rd_sem = [
        ("CSE-3-2", "MATH", 0, 3), ("AIML-3", "MATH", 0, 2),
        ("CSE-3-1", "EE", 2, 3), ("CSE-3-1", "MATH", 2, 4),
        ("CSE-3-2", "MATH", 3, 1), ("AIML-3", "MATH", 3, 1),
        ("CSE-3-1", "MATH", 3, 5), ("CSE-3-1", "EE", 3, 6),
        ("CSE-3-1", "MATH", 4, 0), ("CSE-3-1", "EE", 4, 1),
        ("CSE-3-2", "EE", 4, 3)
    ]
    for section, subject, day, slot in fixed_classes_3rd_sem:
        class_var = get_class_var(section, subject, day, slot)
        if class_var is not None:
            model.Add(class_var == 1)

    # --- 2. Fixed Schedule for 5th Semester ---
    fixed_classes_5th_sem = [
        ("CSE-5", "ISE", 0, 0), ("CSE-5", "ED", 0, 4), ("CSE-5", "ED", 0, 5),
        ("CSE-5", "ISE", 1, 5), ("CSE-5", "ISE", 1, 6),
        ("IT-5", "ISE", 2, 5), ("IT-5", "ISE", 2, 6),
        ("IT-5", "ISE", 3, 6),
        ("IT-5", "ED", 4, 4), ("IT-5", "ED", 4, 5)
    ]
    for section, subject, day, slot in fixed_classes_5th_sem:
        class_var = get_class_var(section, subject, day, slot)
        if class_var is not None:
            model.Add(class_var == 1)
            
    # --- 3. Teacher Unavailability ---
    unavailable_slots = {
        "SA":  [(0, 2), (0, 3), (0, 5), (2, 0), (3, 2)],
        "EO":  [(1, 1), (1, 2), (1, 3), (2, 3), (3, 5), (4, 0), (4, 1)],
        "GF7": [(0, 4), (1, 3), (2, 0), (3, 5), (3, 6)],
        "SPS": [(0, 0), (2, 2), (2, 3), (2, 6), (4, 1)],
        "GF8": [(0, 3), (1, 2), (1, 3), (2, 2), (3, 5)],
        "SS":  [(1, 1), (2, 2), (3, 2), (3, 3), (4, 5)],
        "GF9": [(0, 5), (1, 2), (1, 5), (1, 6), (2, 5)],
        "GF10":[(0, 5), (0, 6), (1, 0), (3, 1), (4, 3)],
        "AS":  [(0, 5), (0, 6)], "SP":  [(1, 5), (1, 6)], "KN":  [(3, 5), (3, 6)]
    }
    for teacher, slots in unavailable_slots.items():
        for day_idx, slot_idx in slots:
            vars_to_block = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if tc == teacher and d == day_idx and s == slot_idx
            ]
            if vars_to_block:
                model.Add(sum(vars_to_block) == 0)

    # --- 4. Section Unavailability for 3rd Sem (THEORY CLASSES ONLY) ---
    section_unavailable_slots = {
        "CSE-3-1": [(0, 2), (0, 3), (2, 2), (2, 5), (2, 6), (3, 0), (3, 3), (3, 4), (4, 2), (4, 3)],
        "CSE-3-2": [(0, 0), (0, 1), (0, 4), (0, 5), (0, 6), (2, 0), (2, 3), (2, 4), (3, 5), (3, 6), (4, 0), (4, 1), (4, 4), (4, 5), (4, 6)],
        "AIML-3":  [(0, 0), (0, 1), (0, 4), (0, 5), (0, 6), (1, 2), (2, 0), (2, 3), (2, 4), (3, 3), (3, 6), (4, 0), (4, 1), (4, 4), (4, 5), (4, 6)]
    }

    for section, slots in section_unavailable_slots.items():
        for day_idx, slot_idx in slots:
            # Block any THEORY class for this section in the unavailable slot. Labs are allowed.
            vars_to_block = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and d == day_idx and 'Lab' not in subj and s == slot_idx
            ]
            if vars_to_block:
                model.Add(sum(vars_to_block) == 0)

# ---------------- SOFT CONSTRAINTS ---------------- #

def _add_continuous_blocks_preference(model, class_vars, config, penalties):
    """Encourage continuous classes for each section."""
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            for slot_idx in range(len(config.ALL_SLOTS) - 1):
                v1 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() if sec == section and d == day_idx and s == slot_idx]
                v2 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() if sec == section and d == day_idx and s == slot_idx + 1]
                if v1 and v2:
                    penalty = model.NewIntVar(0, 1, f"gap_{section}_{day_idx}_{slot_idx}")
                    model.Add(sum(v1) - sum(v2) <= penalty)
                    model.Add(sum(v2) - sum(v1) <= penalty)
                    penalties.append(penalty)

