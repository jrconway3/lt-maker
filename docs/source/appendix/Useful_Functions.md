# Useful Functions

There are a number of useful functions that can be employed in event eval zones to fetch some aspect of the game. This page is exhaustive; it will list every ready-made
function that can query the game state.

## Map Functions

#### Get Allies Within Distance

    get_allies_within_distance(self, position: Tuple[int, int], dist: int = 1) 
		-> List[Tuple[app.engine.objects.unit.UnitObject, int]]

Return a list containing all player units within `dist` distance to the specific position.

        Args:
            position (Tuple[int, int]):  Position to query.
            dist (int, optional): How far to search. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns all pairs of `(unit, distance)`
            within the specified `dist`.
        
  ---------------------


#### Get Closest Allies

    get_closest_allies(self, position: Tuple[int, int], num: int = 1) 
		-> List[Tuple[app.engine.objects.unit.UnitObject, int]]

Return a list containing the closest player units and their distances.

        Args:
            position (Tuple[int, int]): Position to query.
            num (int, optional): How many allies to search for. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns `num` pairs of `(unit, distance)` to the position.
            Will return fewer if there are fewer player units than `num`.
        
  ---------------------

## Skills

#### Get Skill By Nid

    get_skill_by_nid(self, unit: app.engine.objects.unit.UnitObject, skill_nid: str) 
		-> app.engine.objects.skill.SkillObject

Returns a skill object by nid.

        Args:
            unit (UnitObject): Unit in question
            skill_nid (NID): NID of skill

        Returns:
            SkillObject | None: Skill, if exists on unit, else None.
        
  ---------------------

