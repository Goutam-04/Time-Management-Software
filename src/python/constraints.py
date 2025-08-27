# constraints.py

def add_hard_constraints(model, class_vars, config):
    """Adds all the mandatory (hard) constraints to the model."""
    _add_resource_uniqueness(model, class_vars, config)
    _add_scheduling_rules(model, class_vars, config)
    _add_workload_limits(model, class_vars, config)

def _add_resource_uniqueness(model, class_vars, config):
    """Ensures rooms, teachers, and sections are not double-booked."""
    # 1. A room can have only one class
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

    # 2. A teacher can teach only one class
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

    # 3. A section/group can have only one class
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
    """Adds specific rules like class counts and recess."""
    # 4. Each theory subject taught exactly 3 times a week
    for section, section_subjects in config.SUBJECTS.items():
        for subject, teacher in section_subjects:
            vars_for_subject = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                                if sec == section and subj == subject]
            model.Add(sum(vars_for_subject) == 3)

    # 5. Each lab for each group scheduled exactly once
    for section, section_labs in config.LABS.items():
        for lab_name in section_labs:
            for group in config.GROUPS:
                vars_for_lab = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                                if sec == section and grp == group and subj == lab_name]
                if vars_for_lab:
                    model.AddExactlyOne(vars_for_lab)

    # 6. Recess rule: no class at 2-3 if class at 12-1
    slot_12_1_idx = config.ALL_SLOTS.index("12-1")
    slot_2_3_idx = config.ALL_SLOTS.index("2-3")
    for teacher in config.ALL_TEACHERS:
        for day_idx in range(len(config.DAYS)):
            busy_at_12 = model.NewBoolVar(f't_{teacher}_d_{day_idx}_busy12')
            busy_at_2 = model.NewBoolVar(f't_{teacher}_d_{day_idx}_busy2')
            
            vars_at_12 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() if tc == teacher and d == day_idx and (s == slot_12_1_idx or ('Lab' in subj and s + 1 == slot_12_1_idx))]
            vars_at_2 = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() if tc == teacher and d == day_idx and s == slot_2_3_idx]
            
            model.Add(sum(vars_at_12) > 0).OnlyEnforceIf(busy_at_12)
            model.Add(sum(vars_at_12) == 0).OnlyEnforceIf(busy_at_12.Not())
            model.Add(sum(vars_at_2) > 0).OnlyEnforceIf(busy_at_2)
            model.Add(sum(vars_at_2) == 0).OnlyEnforceIf(busy_at_2.Not())
            
            model.AddBoolOr([busy_at_12.Not(), busy_at_2.Not()])

def _add_workload_limits(model, class_vars, config):
    """Adds rules to limit the number of classes per day."""
    # 7. Max 4 theory classes per section per day
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            daily_theory = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                            if sec == section and d == day_idx and 'Lab' not in subj]
            model.Add(sum(daily_theory) <= 4)
    
    # 8. Max 2 labs per section per group per day
    for section in config.SECTIONS:
        for group in config.GROUPS:
            for day_idx in range(len(config.DAYS)):
                daily_labs = [v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items()
                              if sec == section and grp == group and d == day_idx and 'Lab' in subj]
                model.Add(sum(daily_labs) <= 2)