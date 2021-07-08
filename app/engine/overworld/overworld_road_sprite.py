import logging
from app.constants import TILEHEIGHT, TILEWIDTH
from typing import List
from pygame import Surface
from app.sprites import SPRITES
from app.engine import engine
from app.utilities.typing import Point
from app.utilities.enums import Direction
from app.utilities.utils import dot_product, tuple_sub, tmult, tuple_add

class OverworldRoadSpriteWrapper():
    """Not a real class, just factoring out some sprite-specific logic.
    If you don't have `overworld_routes.png` open as you're reading this code,
    it will make 0 sense.
    """
    SPRITE_DIMENSIONS = (8, 8)
    # the real spritesheet (see overworld_routes.png) includes sea routes
    # for a total of 120x8 pixels, but i'm not doing the dotted-line sea routes
    # since those seem like a pain, so I'm leaving them as a future todo
    SPRITESHEET_DIMENSIONS = (64, 8)

    def __init__(self):
        road_sprite = SPRITES['overworld_routes']
        self.sprite_dict = {}
        if road_sprite:
            if not road_sprite.image:
                road_sprite.image = engine.image_load(road_sprite.full_path)
        self.road_sprite = road_sprite
        if self.road_sprite:
            self.subsprites: List[Surface] = []
            for x in range(0, self.SPRITESHEET_DIMENSIONS[0], self.SPRITE_DIMENSIONS[0]):
                self.subsprites.append(engine.subsurface(road_sprite.image, (x, 0, 8, 8)))
            self.htop = self.subsprites[1]
            self.hbot = self.subsprites[2]
            self.vleft = self.subsprites[3]
            self.vright = self.subsprites[4]
            self.right_angle = self.subsprites[5]
            self.diag_main = self.subsprites[6]
            self.diag_corner = self.subsprites[7]

    def has_image(self) -> bool:
        return self.road_sprite is not None

    @classmethod
    def road_to_full_points_list(cls, road: List[Point]) -> List[Point]:
        """'unpacks' a road into constituent points (e.g. [(0, 0), (3, 3)] => [(0, 0), (1, 1), (2, 2), (3, 3)]).
        This requires that the road is a "locked" road, i.e. it only contains 45 and 90 degree angles.

        Args:
            road (List[Point]): initial road

        Returns:
            List[Point]: unpacked points
        """
        unpacked: List[Point] = []
        prev_point = road[0]
        for point in road:
            if point == prev_point:
                continue
            diff = tuple_sub(point, prev_point)
            length = max(abs(diff[0]), abs(diff[1]))
            inc = tmult(diff, 1 / length)
            inc = (int(inc[0]), int(inc[1]))
            start = prev_point
            while start != tuple(point):
                unpacked.append(start)
                start = tuple_add(start, inc)
            prev_point = point
        unpacked.append(road[-1])
        return unpacked

    def _draw_straight(self, surf: Surface, tile_pos: Point, direction: Direction):
        left, top = tile_pos[0] * TILEWIDTH, tile_pos[1] * TILEHEIGHT
        off_x, off_y = TILEWIDTH / 2, TILEHEIGHT / 2
        # quadrants oriented like cartesian plane
        q1 = (left + off_x, top)
        q2 = (left, top)
        q3 = (left, top + off_y)
        q4 = (left + off_x, top + off_y)

        if direction == Direction.UP:
            surf.blit(self.vleft, q2)
            surf.blit(self.vright, q1)
        elif direction == Direction.DOWN:
            surf.blit(self.vleft, q3)
            surf.blit(self.vright, q4)
        elif direction == Direction.LEFT:
            surf.blit(self.htop, q2)
            surf.blit(self.hbot, q3)
        elif direction == Direction.RIGHT:
            surf.blit(self.htop, q1)
            surf.blit(self.hbot, q4)

    def _draw_diagonal(self, surf: Surface, tile_pos: Point, direction: Direction, is_vertical_right_angle: bool=False):
        # shorthand
        left, top = tile_pos[0] * TILEWIDTH, tile_pos[1] * TILEHEIGHT
        off_x, off_y = TILEWIDTH / 2, TILEHEIGHT / 2
        # quadrants oriented like cartesian plane
        q1 = (left + off_x, top)
        q2 = (left, top)
        q3 = (left, top + off_y)
        q4 = (left + off_x, top + off_y)

        quadrant = q1
        if direction == Direction.UP_LEFT:
            quadrant = q2
            sprite = self.diag_main
        elif direction == Direction.UP_RIGHT:
            quadrant = q1
            sprite = engine.transform_rotate(self.diag_main, 90)
        elif direction == Direction.DOWN_LEFT:
            quadrant = q3
            sprite = engine.transform_rotate(self.diag_main, 90)
        elif direction == Direction.DOWN_RIGHT:
            quadrant = q4
            sprite = self.diag_main

        surf.blit(sprite, quadrant)
        x, y = quadrant
        if is_vertical_right_angle:
            if quadrant == q1:
                surf.blit(engine.transform_rotate(self.diag_corner, 270), (x, y - off_y))
                surf.blit(engine.transform_rotate(self.diag_corner, 270))
            elif quadrant == q2:
                surf.blit(engine.transform_rotate(self.diag_corner, 0), (x, y - off_y))
                surf.blit(engine.transform_rotate(self.diag_corner, 0), (x + off_x, y))
            elif quadrant == q3:
                surf.blit(engine.transform_rotate(self.diag_corner, 90), (x, y + off_y))
                surf.blit(engine.transform_rotate(self.diag_corner, 90), (x + off_x, y))
            elif quadrant == q4:
                surf.blit(engine.transform_rotate(self.diag_corner, 180), (x, y + off_y))
                surf.blit(engine.transform_rotate(self.diag_corner, 180), (x - off_x, y))
        else:
            if quadrant in [q1, q3]:
                surf.blit(engine.transform_rotate(self.diag_corner, 270), (x, y - off_y))
                surf.blit(engine.transform_rotate(self.diag_corner, 90), (x, y + off_y))
            else:
                surf.blit(engine.transform_rotate(self.diag_corner, 0), (x, y - off_y))
                surf.blit(engine.transform_rotate(self.diag_corner, 180), (x, y + off_y))

    def _draw_turn(self, surf: Surface, tile_pos: Point, directions: List[Direction]):
        # shorthand
        left, top = tile_pos[0] * TILEWIDTH, tile_pos[1] * TILEHEIGHT
        off_x, off_y = TILEWIDTH / 2, TILEHEIGHT / 2
        # quadrants oriented like cartesian plane
        q1 = (left + off_x, top)
        q2 = (left, top)
        q3 = (left, top + off_y)
        q4 = (left + off_x, top + off_y)

        if Direction.UP in directions:
            if Direction.LEFT in directions: # up left
                surf.blit(engine.transform_rotate(self.right_angle, 90), q2)
                surf.blit(self.hbot, q3)
                surf.blit(self.vright, q1)
            else: # up right
                surf.blit(engine.transform_rotate(self.right_angle, 180), q1)
                surf.blit(self.vleft, q2)
                surf.blit(self.hbot, q4)
        else:
            if Direction.LEFT in directions: # down left
                surf.blit(engine.transform_rotate(self.right_angle), q3)
                surf.blit(self.htop, q2)
                surf.blit(self.vright, q4)
            else: # down right
                surf.blit(engine.transform_rotate(self.right_angle, 270), q4)
                surf.blit(self.htop, q1)
                surf.blit(self.vleft, q3)

    def draw_tile(self, surf: Surface, tile_pos: Point, neighbor_points: List[Point]):
        """I apologize to anyone who has to read this code."""
        """Note: `neighbor_points` can be very far away, they are just used to establish angle"""
        if not self.has_image():
            logging.error("Road Sprite not found!")
            return
        # quadrants oriented like cartesian plane
        is_diagonal_vertical_right_angle = False

        # first, if we're at right angles, use special logic
        if len(neighbor_points) == 2:
            vec_a = tuple_sub(neighbor_points[0], tile_pos)
            vec_b = tuple_sub(neighbor_points[1], tile_pos)
            is_perpendicular = dot_product(vec_a, vec_b) == 0
            if is_perpendicular and (0 in vec_a or 0 in vec_b): # right angle, draw corner
                direcs = [Direction.parse_map_direction(v[0], v[1]) for v in [vec_a, vec_b]]
                print(direcs)
                self._draw_turn(surf, tile_pos, direcs)
                return
            elif is_perpendicular and not (0 in vec_a or 0 in vec_b): # right angle but diagonal
                if Direction.which_vertical_dir(Direction.parse_map_direction(*vec_a)) != Direction.which_vertical_dir(Direction.parse_map_direction(*vec_b)):
                    is_diagonal_vertical_right_angle = True

        for point in neighbor_points:
            direc = Direction.parse_map_direction(*tuple_sub(point, tile_pos))
            if direc in [Direction.UP, Direction.DOWN, Direction.RIGHT, Direction.LEFT]:
                self._draw_straight(surf, tile_pos, direc)
            else: # diagonal
                self._draw_diagonal(surf, tile_pos, direc, is_diagonal_vertical_right_angle)
