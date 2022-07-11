# Useful Functions

There are a number of useful functions that can be employed in event eval zones to fetch some aspect of the game. This page is exhaustive; it will list every ready-made
function that can query the game state.


## Items



#### Get Item

    get_item(self, unit, item) 
		-> app.engine.objects.item.ItemObject

Returns a item object by nid.

        Args:
            unit: unit to check
            item: item to check

        Returns:
            ItemObject | None: Item if exists on unit, otherwise None
        
  ---------------------


#### Has Item

    has_item(self, unit, item) 
		-> bool

Check if unit has item.

        Args:
            unit: unit to check
            item: item to check

        Returns:
            bool: True if unit has item, else False
        
  ---------------------


## Map Functions



#### Get Allies Within Distance

    get_allies_within_distance(self, position, dist: int = 1) 
		-> List[Tuple[app.engine.objects.unit.UnitObject, int]]

Return a list containing all player units within `dist` distance to the specific position.

        Args:
            position: position or unit
            dist (int, optional): How far to search. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns all pairs of `(unit, distance)`
            within the specified `dist`.
        
  ---------------------


#### Get Closest Allies

    get_closest_allies(self, position, num: int = 1) 
		-> List[Tuple[app.engine.objects.unit.UnitObject, int]]

Return a list containing the closest player units and their distances.

        Args:
            position: position or unit
            num (int, optional): How many allies to search for. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns `num` pairs of `(unit, distance)` to the position.
            Will return fewer if there are fewer player units than `num`.
        
  ---------------------


#### Get Units In Area

    get_units_in_area(self, position_corner_1: Tuple[int, int], position_corner_2: Tuple[int, int]) 
		-> List[app.engine.objects.unit.UnitObject]

Returns a list of units within a rectangular area.

        Args:
            position_corner_1 (Tuple[int, int]): (x, y) coordinates for one corner of the area
            position_corner_2 (Tuple[int, int]): (x, y) coordinates for the opposite corner

        Returns:
            List[UnitObject]: Returns all units with positions with values between those
            specified by the corners (inclusive), or an empty list if no units exist in that area
        
  ---------------------


## Skills



#### Get Debuff Count

    get_debuff_count(self, unit) 
		-> int

Checks how many negative skills the unit has.

        Args:
            unit: Unit in question

        Returns:
            int: Number of unique negative skills on the unit
        
  ---------------------


#### Get Skill

    get_skill(self, unit, skill) 
		-> app.engine.objects.skill.SkillObject

Returns a skill object by nid.

        Args:
            unit: unit in question
            skill: nid of skill

        Returns:
            SkillObject | None: Skill, if exists on unit, else None.
        
  ---------------------


#### Has Skill

    has_skill(self, unit, skill) 
		-> bool

checks if unit has skill

        Args:
            unit: unit to check
            skill: skill to check

        Returns:
            bool: True if unit has skill, else false
        
  ---------------------

