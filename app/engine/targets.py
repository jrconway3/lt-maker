from app.data.database import DB
from app.engine import a_star
from app.engine.game_state import game

class TargetSystem():
    def __init__(self):
        pass

    def get_valid_moves(self, unit, force=False):
        # Assumes unit is on the map
        if not force and unit.finished or (unit.has_moved and not unit.has_canto()):
            return set()

        mtype = DB.classes.get(unit.klass).mtype
        grid = game.grid.get_grid(mtype)
        width, height = game.tilemap.width, game.tilemap.height
        pathfinder = a_star.Djikstra(unit.position, grid, width, height, unit.team, 'pass_through' in unit.status_bundle)

        movement_left = equations.movement(unit) if force else unit.movement_left

        valid_moves = pathfinder.process(game.grid.team_grid, movement_left)
        valid_moves.add(unit.position)
        return valid_moves
