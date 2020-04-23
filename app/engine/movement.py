from app.constants import TILEWIDTH, TILEHEIGHT
from app import utilities
from app.data.database import DB

import app.engine.config as cf
from app.engine import engine, action
from app.engine.game_state import game

class MovementData():
    def __init__(self, path, event):
        self.path = path
        self.last_update = 0
        self.event = event

class MovementManager():
    def __init__(self):
        self.moving_units = {}
        self.camera_follow = None

    def add(self, unit, path, event=False):
        self.moving_units[unit.nid] = MovementData(path, event)

    def begin_move(self, unit, path, event=False):
        self.add(unit, path, event)
        unit.sprite.change_state('moving')
        game.leave(unit)

    def __len__(self):
        return len(self.moving_units)

    def get_last_update(self, nid):
        data = self.moving_units.get(nid)
        if data:
            return data.last_update
        else:
            return 0

    def get_next_position(self, nid):
        data = self.moving_units.get(nid)
        if data and data.path:
            return data.path[-1]
        else:
            return None

    def get_mcost(unit_to_move, pos):
        terrain = game.tilemap.tiles[pos].terrain_nid
        mtype = terrain.mtype
        movement_group = DB.classes.get(unit_to_move.klass).movement_group
        mcost = DB.mcost.get_mcost(movement_group, mtype)
        return mcost

    def forced_movement(self, unit_to_move, anchor_unit, anchor_pos, move_component):
        mtype, magnitude = move_component
        if not utilities.is_int(magnitude):
            dist = utilities.calculate_distance(unit_to_move.position, anchor_pos)
            magnitude = game.equations.get(magnitude, unit_to_move, None, dist)

        if mtype == 'shove':
            new_position = self.check_shove(unit_to_move, anchor_pos, magnitude)
            if new_position:
                unit_to_move.sprite.set_transition('fake_in')
                x_offset = unit_to_move.position[0] - new_position[0] * TILEWIDTH
                y_offset = unit_to_move.position[1] - new_position[1] * TILEHEIGHT
                unit_to_move.sprite.set_offset(x_offset, y_offset)
                action.do(action.ForcedMovement(unit_to_move, new_position))
        elif mtype == 'swap':
            new_position = anchor_pos
            action.do(action.ForcedMovement(unit_to_move, new_position))
        elif mtype == 'warp':
            action.do(action.Warp(unit_to_move, anchor_pos))

    def check_shove(self, unit_to_move, anchor_pos, magnitude):
        pos_offset_x = unit_to_move.position[0] - anchor_pos[0]
        pos_offset_y = unit_to_move.position[1] - anchor_pos[1]
        new_position = (unit_to_move.position[0] + pos_offset_x * magnitude,
                        unit_to_move.position[1] + pos_offset_y * magnitude)

        mcost = self.get_mcost(unit_to_move, new_position)
        if game.tilemap.check_bounds(new_position) and \
                not game.grid.get_unit(new_position) and \
                mcost < 5:
            return new_position
        return False

    def update(self):
        current_time = engine.get_time()
        for unit_nid in list(self.moving_units.keys()):
            data = self.moving_units[unit_nid]
            if current_time - data.last_update > cf.SETTINGS['unit_speed']:
                data.last_update = current_time
                unit = game.level.units.get(unit_nid)

                if data.path:
                    new_position = data.path.pop()
                    if unit.position != new_position:
                        mcost = self.get_mcost(unit, new_position)
                        unit.movement_left -= mcost
                    unit.position = new_position
                    # Handle camera following moving unit
                    if not data.event:
                        if not self.camera_follow:
                            self.camera_follow = unit_nid
                    if self.camera_follow == unit_nid:
                        game.cursor.set_pos(unit.position)

                else: # Path is empty, so we are done
                    del self.moving_units[unit_nid]
                    game.arrive(unit)
                    if data.event:
                        unit.sprite.change_state('normal')
                    else:
                        unit.has_moved = True
                    # Handle camera auto-follow
                    if self.camera_follow == unit_nid:
                        self.camera_follow = None
