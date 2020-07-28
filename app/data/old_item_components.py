from app.data.data import Data

class ItemComponent():
    def __init__(self, nid=None, name='', attr=bool, value=True, requires=no_requirement, volatile=False):
        self.nid: str = nid
        self.name: str = name
        self.attr = attr
        self.value = value
        self.requires = requires
        self.volatile: bool = volatile

    def __getstate__(self):
        return self.nid, self.value

    def __setstate__(self, state):
        self.nid, self.value = state

    @classmethod
    def copy(cls, other):
        return cls(other.nid, other.name, other.attr, other.value, other.requires)

    def serialize(self):
        if isinstance(self.value, Data):
            return self.nid, self.value.save()
        elif isinstance(self.value, list):
            return self.nid, self.value
        else:
            return (self.nid, self.value)

    # For spell component only
    @property
    def weapon_type(self):
        return self.value[0]

    @property
    def affect(self):
        return self.value[1]

    @property
    def target(self):
        return self.value[2]

item_components = Data([
    ItemComponent('weapon', 'Weapon', 'WeaponType', None,
                  lambda x: 'spell' not in x),
    ItemComponent('spell', 'Spell', ('WeaponType', SpellAffect, SpellTarget),
                  (None, SpellAffect.Neutral, SpellTarget.Unit),
                  lambda x: 'weapon' not in x),
    ItemComponent('usable', 'Usable'),
    ItemComponent('might', 'Might', int, 0, requires_spell_or_weapon),
    ItemComponent('hit', 'Hit Rate', int, 0, requires_spell_or_weapon),
    ItemComponent('level', 'Weapon Level Required', 'WeaponRank', None, requires_spell_or_weapon),
    ItemComponent('weight', 'Weight', int, 0, requires_spell_or_weapon),
    ItemComponent('crit', 'Critical Rate', int, 0, requires_spell_or_weapon),
    ItemComponent('magic', 'Magical', bool, False, requires_spell_or_weapon),
    ItemComponent('exp', 'Custom Experience', int, 10, requires_aspect),
    ItemComponent('wexp', 'Custom Weapon Experience', int, 1, requires_spell_or_weapon),

    ItemComponent('uses', 'Total Uses', int, 30, requires_aspect, volatile=True),
    ItemComponent('c_uses', 'Uses per Chapter', int, 8, requires_aspect, volatile=True),
    ItemComponent('hp_cost', 'Costs HP', int, 0, requires_aspect),
    ItemComponent('mana_cost', 'Costs Mana', int, 0, requires_aspect),
    # ItemComponent('cooldown', 'Cooldown', int, 0, requires_aspect, volatile=True),
    
    ItemComponent('heal_on_hit', 'Heals Target', int, 0, requires_spell_or_weapon),
    ItemComponent('heal_on_use', 'Heal on Use', int, 10, requires_usable),

    ItemComponent('effective', 'Effective Against', EffectiveSubComponent, EffectiveData(), requires_spell_or_weapon),
    ItemComponent('prf_unit', 'Restricted to (Unit)', BasicSubComponent, PrfUnitData(), requires_aspect),
    ItemComponent('prf_class', 'Restricted to (Class)', BasicSubComponent, PrfClassData(), requires_aspect),
    ItemComponent('prf_tag', 'Restricted to (Tag)', BasicSubComponent, PrfTagData(), requires_aspect),

    ItemComponent('locked', 'Cannot be removed from Unit'),
    ItemComponent('brave', 'Brave', 'BraveChoice', 0, requires_spell_or_weapon),
    ItemComponent('reverse', 'Reverses Weapon Triangle', bool, False, requires_spell_or_weapon),
    ItemComponent('double_triangle', 'Doubles Effect of Weapon Triangle', bool, False, requires_spell_or_weapon),
    ItemComponent('cannot_be_countered', 'Cannot be Countered', bool, False, requires_weapon),
    ItemComponent('no_double', 'Cannot Double', bool, False, requires_weapon),
    ItemComponent('ignore_triangle', 'Ignores Weapon Triangle', bool, False, requires_spell_or_weapon),
    ItemComponent('damage_on_miss', 'Does %% Damage even on Miss', float, 0.5, requires_might_and_hit),
    ItemComponent('lifelink', 'Heals user %% of Damage Dealt', float, 0.5, requires_might),
    ItemComponent('unrepairable', 'Cannot be Repaired', bool, False, requires_uses),

    ItemComponent('aoe', 'Area of Effect', (AOEMode, SpellTarget, int), (AOEMode.Normal, SpellTarget.Unit, 0), requires_spell_or_weapon),

    ItemComponent('promotion', 'Promotes (Class)', BasicSubComponent, PromoteData(), requires_usable),
    ItemComponent('class_change', 'Changes (Class)', BasicSubComponent, ClassChangeData(), requires_usable),
    ItemComponent('permanent_stat_increase', 'Permanently Increases (Stat)', StatChangeSubComponent, StatChangeData(), requires_usable),
    ItemComponent('permanent_growth_increase', 'Permanently Increases (Growth)', GrowthChangeSubComponent, GrowthChangeData(), requires_usable),

    ItemComponent('custom_damage_equation', 'Custom Damage Equation', 'Equation', None, requires_might),
    ItemComponent('custom_defense_equation', 'Custom Defense Equation', 'Equation', None, requires_might),
    ItemComponent('custom_hit_equation', 'Custom Hit Equation', 'Equation', None, requires_hit),
    ItemComponent('custom_avoid_equation', 'Custom Avoid Equation', 'Equation', None, requires_hit),
    ItemComponent('custom_crit_equation', 'Custom Crit Equation', 'Equation', None, requires_crit),
    ItemComponent('custom_dodge_equation', 'Custom Crit Avoid Equation', 'Equation', None, requires_crit),
    ItemComponent('custom_double_atk_equation', 'Custom Double Attack Equation', 'Equation', None, requires_weapon),
    ItemComponent('custom_double_def_equation', 'Custom Double Defense Equation', 'Equation', None, requires_weapon),

    # ItemComponent('hit_status', 'Applies Status on hit', 'Status', None, requires_spell_or_weapon),
    # ItemComponent('use_status', 'Applies Status on use', 'Status', None, requires_usable),
    # ItemComponent('equip_status', 'Applies Status while equipped', 'Status', None, requires_weapon),
    # ItemComponent('hold_status', 'Applies Status while held', 'Status', None),

    # ItemComponent('movement_hit', 'Applies Movement on hit', 'Movement', None, requires_spell_or_weapon),
    # ItemComponent('movement_self_hit', 'Applies Movement to self on hit', 'Movement', None, requires_spell_or_weapon),
    # ItemComponent('movement_use', 'Applies Movement on use', 'Movement', None, requires_usable),

    ItemComponent('repair', 'Repairs Items', bool, True, repair_requires),
    # ItemComponent('target_restrict', 'Restrict Targets', 'Eval', '', requires_aspect),
    ItemComponent('multiple_targets', 'Multiple Targets', TargetSubComponent, TargetData(), requires_spell),
    # ItemComponent('multiple_target_restrict', 'Restrict Multiple Targets', 'Eval', '', requires_multiple_targets)
    # ItemComponent('interact', 'Interact with Event Tile', ??, None, requires_spell),
    # ItemComponent('event_on_use', ??)
    # ItemComponent('event_on_hit', ??)

    ItemComponent('no_ai', 'AI will not use', bool, True, requires_aspect),
    # ItemComponent('ai_target', 'Restrict AI Targets', 'Eval', '', requires_aspect),
    # ItemComponent('warning', 'Show Warning', 'Eval', '', requires_spell_or_weapon),

    ItemComponent('map_hit_color', 'Map Hit Color', 'Color', (255, 255, 255, 120), requires_aspect),
    # ItemComponent('aoe_anim', 'Custom AOE Map Animation', 'Animation', None, requires_aspect),
    # ItemComponent('target_anim', 'Custom Map Animation on target', 'Animation', None, requires_aspect),
    # ItemComponent('self_anim', 'Custom Map Animation on user', 'Animation', None, requires_aspect),
    # ItemComponent('custom_sfx', 'Custom Sound', 'Sound', None, requires_aspect),
    # ItemComponent('combat_effect', 'Custom Effect in Animation Combat', 'Effect', None, requires_weapon),
    # ItemComponent('custom_anim', 'Custom Combat Animation', 'Combat Anim', None, requires_aspect)

])

def get_component(nid):
    base = item_components.get(nid)
    return ItemComponent.copy(base)

def deserialize_component(dat):
    nid, value = dat
    base = item_components.get(nid)
    copy = ItemComponent.copy(base)
    if copy.attr in (EffectiveSubComponent, BasicSubComponent, StatChangeSubComponent, GrowthChangeSubComponent, TargetSubComponent):
        for v in value:
            deserialized = copy.attr.deserialize(v)
            copy.value.append(deserialized)
    else:
        copy.value = value
    return copy
