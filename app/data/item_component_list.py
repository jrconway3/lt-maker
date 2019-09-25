# Item Components

Weapon (bool) : Cannot be Spell
Spell (Beneficial/Detrimental/Neutral AND Target (Ally/Enemy/Unit/Tile/Tile Without Unit)) : Cannot be Weapon
Usable (bool)
Might (int) : Spell or Weapon
Hit (int): Spell or Weapon
Rank (Weapon Rank): Spell or Weapon
Status on Hit (Status): Spell or Weapon
Status while Equipped (Status): Weapon
Status while Held (Status)
Status on Use (Status): Usable
Droppable (bool)
Locked (bool)
Uses (int)
Chapter Uses (int)
Weight (int): Spell or Weapon
Experience (int): Spell or Weapon
Maximum Experience (int): Spell or Weapon
Unrepairable (bool)
Movement on Hit (Movement): Spell or Weapon
Movement on Use (Movement): Usable
Brave (bool): Weapon
Brave on Attack (bool): Weapon
Brave on Defense (bool): Weapon
Cannot Be Countered (bool): Weapon
Cannot Double (bool): Weapon
Heal on Hit (int): Weapon or Spell
Heal on Use (int): Usable
Repair (bool): Spell or Usable  -- will work on both hit and use
Unlock (bool): Spell
Extra Targets (list of (Min Range / Max Range AND Target)): Spell
Target Restrict (Eval): Spell
Crit (int): Weapon or Spell AND Might
Effective Versus (list of (Tag and int)): Weapon or Spell AND Might
Reverse (bool): Weapon or Spell
Magical (bool): Weapon or Spell
Magical only at Range (bool): Weapon or Spell
Ignores Weapon Triangle (bool): Weapon or Spell
Weapon Experience (int): Weapon or Spell
Does Half Damage on Miss (bool): Weapon or Spell
Lifelink (bool): Weapon or Spell
Half Lifelink (bool): Weapon or Spell
Ignore Defense (bool): Weapon or Spell
Ignore Half Defense (bool): Weapon or Spell
Area of Effect (AOEType): Weapon or Spell
Alternate Damage, Defense, Accuracy, Avoid, Crit Accuracy, Crit Avoid (Equation): Weapon or Spell AND associated Might, Hit, or Crit component
Booster (bool): Usable
Promotion (list of Classes): Usable
Permanent Stat Increase (list of Stats): Usable
Permanent Growth Increase (list of Growths): Usable

No AI (bool)
AI Item Priority (float)


