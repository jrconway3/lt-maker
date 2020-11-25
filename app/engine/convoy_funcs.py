import random
from app.engine import item_system, item_funcs, equations
from app.engine.game_state import game

def can_restock(item) -> bool:
    convoy = game.party.convoy
    return bool(item.uses and item.data['uses'] < item.data['starting_uses'] and item.nid in [i.nid for i in convoy])

def restock(item):
    convoy = game.party.convoy
    if not can_restock(item):
        return

    other_items = sorted([i for i in convoy if i.nid == item.nid], key=lambda i: i.data['uses'])
    for i in other_items:
        diff_needed = item.data['starting_uses'] - item.data['uses']
        if diff_needed > 0:
            if i.data['uses'] >= diff_needed:
                i.data['uses'] -= diff_needed
                item.data['uses'] += diff_needed
                if i.data['uses'] <= 0:
                    convoy.remove(i)
            else:
                item.data['uses'] += i.data['uses']
                convoy.remove(i)
        else:
            break

def restock_convoy():
    convoy = game.party.convoy
    items = [i for i in convoy if can_restock(i)]
    items = sorted(items, key=lambda i: i.data['uses'], reverse=True)
    for item in items:
        if item.data['uses'] > 0:
            restock(item)

def optimize_all():
    units = game.get_units_in_party()
    random.shuffle(units)
    for unit in units:
        for item in item_funcs.get_all_tradeable_items(unit):
            store_item(item, unit)
    restock_convoy()
    # Distribute Weapons
    weapons = [item for item in game.party.convoy if item_system.is_weapon(None, item)]
    weapons = sorted(weapons, key=lambda i: (item_system.weapon_rank(None, i), 1000 - i.data.get('uses', 0)))
    for weapon in weapons:
        units_that_can_wield = [
            unit for unit in units
            if not item_funcs.inventory_full(unit, weapon) and
            item_system.available(unit, weapon) and
            weapon.nid not in [i.nid for i in unit.items]]
        units_that_can_wield = sorted(units_that_can_wield, key=lambda u: len(u.items), reverse=True)
        if units_that_can_wield:
            unit = units_that_can_wield.pop()
            take_item(weapon, unit)
    del weapon
    # Distribute Spells
    spells = [item for item in game.party.convoy if item_system.is_spell(None, item)]
    spells = sorted(spells, key=lambda i: (item_system.weapon_rank(None, i), 1000 - i.data.get('uses', 0)))
    for spell in spells:
        units_that_can_wield = [
            unit for unit in units
            if not item_funcs.inventory_full(unit, spell) and
            item_system.available(unit, spell) and
            spell.nid not in [i.nid for i in unit.items]]
        units_that_can_wield = sorted(units_that_can_wield, key=lambda u: len(u.items), reverse=True)
        if units_that_can_wield:
            unit = units_that_can_wield.pop()
            take_item(spell, unit)
    del spell
    # Distribute healing items
    healing_items = sorted([item for item in game.party.convoy if item.heal], key=lambda i: (i.heal.value, 1000 - i.data.get('uses', 0)))
    # Sort by max hp
    for item in reversed(healing_items):
        units_that_can_wield = [
            unit for unit in units
            if not item_funcs.inventory_full(unit, item) and
            not any(item.heal for item in unit.items)]
        units_that_can_wield = sorted(units_that_can_wield, key=lambda u: equations.parser.hitpoints(u))
        if units_that_can_wield:
            unit = units_that_can_wield.pop()
            take_item(item, unit)
    # Done!

def optimize(unit):
    for item in item_funcs.get_all_tradeable_items(unit):
        store_item(item, unit)
    # Distribute Weapons
    weapons = [
        item for item in game.party.convoy 
        if item_system.is_weapon(None, item) and 
        item_system.available(unit, item)]
    weapons = sorted(weapons, key=lambda i: (item_system.weapon_rank(None, i), 1000 - i.data.get('uses', 0)))
    # Distribute Spells
    spells = [
        item for item in game.party.convoy 
        if item_system.is_spell(None, item) and
        item_system.available(unit, item)]
    spells = sorted(spells, key=lambda i: (item_system.weapon_rank(None, i), 1000 - i.data.get('uses', 0)))

    # Give two spells if possible
    num_weapons = 2
    if spells:
        for _ in range(2):
            for spell in spells:
                if not item_system.inventory_full(unit, spell) and \
                        spell.nid not in [i.nid for i in unit.items]:
                    take_item(spell, unit)
                    break
    else:
        num_weapons = 4
    for _ in range(num_weapons):
        for weapon in weapons:
            if not item_system.inventory_full(unit, weapon) and \
                    weapon.nid not in [i.nid for i in unit.items]:
                take_item(weapon, unit)
                break

    # Distribute healing items
    healing_items = sorted([item for item in game.party.convoy if item.heal], key=lambda i: (i.heal.value, 1000 - i.data.get('uses', 0)))
    for item in reversed(healing_items):
        if not item_system.inventory_full(unit, item) and \
                item.nid not in [i.nid for i in unit.items]:
            take_item(item, unit)
            break
    # Done!

def take_item(item, unit):
    convoy = game.party.convoy
    convoy.remove(item)
    unit.add_item(item)

def store_item(item, unit):
    convoy = game.party.convoy
    unit.remove_item(item)
    convoy.append(item)

def trade_items(convoy_item, unit_item, unit):
    convoy = game.party.convoy
    idx = unit.items.index(unit_item)
    unit.remove_item(unit_item)
    convoy.remove(convoy_item)
    convoy.append(unit_item)
    unit.insert_item(idx, convoy_item)
