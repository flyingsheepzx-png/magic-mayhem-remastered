"""Portmanteau identity reconstruction from verified native inventory fields.

Research implementation of 0x575610. Inputs must come from a hash-gated reader.
This does not choose battle icons by their order.
"""

def native_layout(counts, equipped_spells, owned_items, spell_table, cached=None):
    if len(counts) != 3 or any(type(n) is not int or not 0 <= n <= 21 for n in counts):
        raise ValueError('Invalid native tray counts')
    if len(spell_table) != 25 or any(len(row) != 3 for row in spell_table):
        raise ValueError('Invalid native talisman table')
    layout = [list(row) for row in cached] if cached is not None else [[-1]*n for n in counts]
    if len(layout) != 3 or any(len(layout[t]) != counts[t] for t in range(3)):
        raise ValueError('Invalid cached slot layout')
    for spell in equipped_spells:
        if spell == -1:
            break
        match = next(((item, tray) for item, row in enumerate(spell_table)
                      for tray, value in enumerate(row) if value == spell), None)
        if match is None:
            continue
        item, tray = match
        if item not in layout[tray] and -1 in layout[tray]:
            layout[tray][layout[tray].index(-1)] = item
    owned = set(owned_items)
    for row in layout:
        for slot, item in enumerate(row):
            if item >= 0 and item not in owned:
                row[slot] = -1
    return layout

def equipped_slot_spells(layout, spell_table):
    return {(tray, slot): spell_table[item][tray]
            for tray, row in enumerate(layout) for slot, item in enumerate(row)
            if 0 <= item < len(spell_table)}

def battle_slot_icons(slot_spells, icons):
    """Only unique native type-0 spell identities; reject ambiguous duplicates."""
    result = {}
    for slot, spell in slot_spells.items():
        matches = [i for i, icon in enumerate(icons)
                   if icon['type'] == 0 and icon['spell'] == spell]
        if len(matches) == 1 and list(slot_spells.values()).count(spell) == 1:
            result[slot] = matches[0]
    return result
