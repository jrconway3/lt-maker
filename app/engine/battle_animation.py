from app.resources.resources import RESOURCES
from app.data.database import DB

from app.engine.sound import SOUNDTHREAD

battle_anim_speed = 1

class BattleAnimation():
    idle_poses = {'Stand', 'RangedStand', 'TransformStand'}

    def __init__(self, anim_prefab, unit, item):
        self.anim_prefab = anim_prefab
        self.unit = unit
        self.item = item

        self.poses = []  # TODO Generate poses
        self.frame_directory = {}  # TODO Generate Frame directory
        self.current_pose = None
        self.current_palette = None

        self.state = 'inert'
        self.in_basic_state: bool = False  # Is animation in a basic state?
        self.processing = False

        self.wait_for_hit: bool = False
        self.script_idx = 0
        self.current_frame = None
        self.under_frame = None
        self.over_frame = None
        self.frame_count = 0
        self.num_frames = 0

        # Pairing stuff
        self.owner = None
        self.partner_anim = None
        self.right = True
        self.at_range = 0
        self.init_position = None
        self.init_speed = 0
        self.entrance = 0

        # Effect stuff
        self.child_effects = []
        self.under_child_effects = []

        # For drawing
        self.blend = 0
        # Flash Frames
        self.flash_color = None
        self.flash_frames = 0
        self.background = None
        # Opacity
        self.opacity = 0
        self.death_opacity = []
        # Offset
        self.under_static = False
        self.static = False # Animation will always be in the same place on the screen
        self.over_static = False  
        self.ignore_pan = False  # Animation will ignore any panning
        self.pan_away = False

    def pair(self, owner, partner_anim, right, at_range, entrance_frames=0, position=None):
        self.owner = owner
        self.partner_anim = partner_anim
        self.right = right
        self.at_range = at_range
        self.entrance_frames = entrance_frames
        self.entrance_counter = entrance_frames
        self.init_position = position
        self.get_stand()
        self.script_idx = 0
        self.current_frame = None
        self.under_frame = None
        self.over_frame = None
        self.reset()

    def get_stand(self):
        if self.at_range:
            self.current_pose = 'RangedStand'
        else:
            self.current_pose = 'Stand'

    def start_anim(self, pose):
        self.change_pose(pose)
        self.script_idx = 0
        self.wait_for_hit = True
        self.reset_frames()

    def change_pose(self, pose):
        self.current_pose = pose

    def has_pose(self, pose) -> bool:
        return pose in self.poses

    def end_current_pose(self):
        if 'Stand' in self.poses:
            self.get_stand()
            self.state = 'run'
        else:
            self.state = 'inert'
        # Make sure to return to correct pan if we somehow didn't
        if self.pan_away:
            self.pan_away = False
            self.owner.pan_back()
        self.script_idx = 0

    def finish(self):
        self.get_stand()
        self.state = 'leaving'
        self.script_idx = 0

    def reset_frames(self):
        self.state = 'run'
        self.frame_count = 0
        self.num_frames = 0

    def can_proceed(self):
        return self.loop or self.state == 'wait'

    def done(self) -> bool:
        return self.state == 'inert' or (self.state == 'run' and self.current_pose in self.idle_poses)

    def add_effect(self, effect):
        pass

    def get_frames(self, num) -> int:
        return max(1, int(int(num) * battle_anim_speed))

    def start_dying_animation(self):
        self.state = 'dying'
        self.death_opacity = [0, 20, 20, 20, 20, 44, 44, 44, 44, 64,
                              64, 64, 64, 84, 84, 84, 108, 108, 108, 108, 
                              128, 128, 128, 128, 148, 148, 148, 148, 172, 172, 
                              172, 192, 192, 192, 192, 212, 212, 212, 212, 236,
                              236, 236, 236, 255, 255, 255, 0, 0, 0, 0,
                              0, 0, -1, 0, 0, 0, 0, 0, 0, 255, 
                              0, 0, 0, 0, 0, 0, 255, 0, 0, 0,
                              0, 0, 0, 255, 0, 0, 0, 0, 0, 0,
                              255, 0, 0, 0, 0, 0, 0]

    def wait_for_dying(self):
        if self.in_basic_state:
            self.num_frames = int(42 * battle_anim_speed)

    def clear_all_effects(self):
        for child in self.child_effects:
            child.clear_all_effects()
        for child in self.under_child_effects:
            child.clear_all_effects()
        self.child_effects.clear()
        self.under_child_effects.clear()

    def update(self):
        if self.state == 'run':
            # Read script
            if self.frame_count >= self.num_frames:
                self.processing = True
                self.read_script()
            if self.current_pose in self.poses:
                if self.script_idx >= len(self.poses[self.current_pose]):
                    # Check whether we should loop or end
                    if self.current_pose in self.idle_poses:
                        self.script_idx = 0  # Loop
                    else:
                        self.end_current_pose()
            else:
                self.end_current_pose()

            self.frame_count += 1
            if self.entrance_counter:
                self.entrance_counter -= 1

        elif self.state == 'dying':
            if self.death_opacity:
                opacity = self.death_opacity.pop()
                if opacity == -1:
                    opacity = 255
                    self.flash_color = (248, 248, 248)
                    self.flash_frames = 100
                    SOUNDTHREAD.play_sfx('CombatDeath')
                self.opacity = opacity
            else:
                self.state = 'inert'

        elif self.state == 'leaving':
            self.entrance_counter += 1
            if self.entrance_counter > self.entrance_frames:
                self.entrance_counter = self.entrance_frames
                self.state = 'inert'  # done

        elif self.state == 'wait':
            pass

        # Handle effects
        for child in self.child_effects:
            child.update()
        for child in self.under_child_effects:
            child.update()

        # Remove completed child effects
        self.child_effects = [child for child in self.child_effects if child.state != 'inert']
        self.under_child_effects = [child for child in self.under_child_effects if child.state != 'inert']

    def read_script(self):
        if not self.has_pose(self.current_pose):
            return
        script = self.poses[self.current_pose]
        while self.script_idx < len(script) and self.processing:
            command = script[self.script_idx]
            self.run_command(command)
            self.script_idx += 1

    def run_command(self, command):
        self.in_basic_state = False

        values = command.values
        if command.nid == 'frame':
            self.frame_count = 0
            self.num_frames = self.get_frames(values[0])
            self.current_frame = self.frame_directory.get(values[1])
            self.processing = False  # No more processing -- need to wait at least a frame

    def draw(self, surf, shake=(0, 0), range_offset=0, pan_offset=0):
        if self.state == 'inert':
            return

        # Screen flash
        if self.background and not self.blend:
            engine.blit(surf, self.background, (0, 0), None, engine.BLEND_RGB_ADD)

        for child in self.under_child_effects:
            child.draw(surf, (0, 0), range_offset, pan_offset)

        if self.current_frame is not None:
            image, offset = self.get_image(self.current_frame, shake, range_offset, pan_offset, self.static)

            # Move the animations in at the beginnign and out at the end
            if self.entrance_counter:
                progress = (self.entrance_frames - self.entrance_counter) / self.entrance_frames
                new_size = int(progress * image.get_width()), int(progress * image.get_height())
                image = engine.transform_scale(image. new_size)
                if self.flash_color and self.flash_image:
                    self.flash_image = image
                diff_x = offset[0] - self.init_position[0]
                diff_y = offset[1] - self.init_position[1]
                offset = int(self.init_position[0] + progress * diff_x), int(self.init_position[1] + progress * diff_y)

            # Self flash

def get_battle_anim(unit, item) -> BattleAnimation:
    class_obj = DB.classes.get(unit.klass)
    combat_anim_nid = class_obj.combat_anim_nid
    if unit.variant:
        combat_anim_nid += unit.variant
    res = RESOURCES.combat_anims.get(combat_anim_nid)
    if not res:  # Try without unit variant
        res = RESOURCES.combat_anims.get(class_obj.combat_anim_nid)
    if not res:
        return None

    battle_anim = BattleAnimation(res, unit, item)
    return battle_anim
