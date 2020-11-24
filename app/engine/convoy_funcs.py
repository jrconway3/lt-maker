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
