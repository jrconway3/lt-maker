from app.data.database import DB

import app.engine.config as cf
from app.engine import engine, skill_system
from app.engine.game_state import game

class MovementData():
    def __init__(self, path, event, follow):
        self.path = path
        self.last_update = 0
        self.event = event
        self.follow = follow

class MovementManager():
    def __init__(self):
        self.moving_units = {}
        self.camera_follow = None

    def add(self, unit, path, event=False, follow=True):
        self.moving_units[unit.nid] = MovementData(path, event, follow)

    def begin_move(self, unit, path, event=False, follow=True):
        self.add(unit, path, event, follow)
        unit.sprite.change_state('moving')
        game.leave(unit)
        unit.sound.play()

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

    def get_movement_group(self, unit_to_move):
        movement_group = skill_system.movement_type(unit_to_move)
        if not movement_group:
            movement_group = DB.classes.get(unit_to_move.klass).movement_group
        return movement_group

    def get_mcost(self, unit_to_move, pos):
        terrain = game.tilemap.get_terrain(pos)
        mtype = DB.terrain.get(terrain).mtype
        movement_group = self.get_movement_group(unit_to_move)
        mcost = DB.mcost.get_mcost(movement_group, mtype)
        return mcost
        
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
                    # if not data.event:
                    if data.follow and not self.camera_follow:
                        self.camera_follow = unit_nid
                    if self.camera_follow == unit_nid:
                        game.cursor.set_pos(unit.position)

                else: # Path is empty, so we are done
                    del self.moving_units[unit_nid]
                    game.arrive(unit)
                    if unit.sound:
                        unit.sound.stop()
                    if data.event:
                        unit.sprite.change_state('normal')
                    else:
                        unit.has_moved = True
                    # Handle camera auto-follow
                    if self.camera_follow == unit_nid:
                        self.camera_follow = None
