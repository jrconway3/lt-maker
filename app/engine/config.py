import os
from collections import OrderedDict

def read_config_file():
    lines = OrderedDict([('debug', 1),
                         ('random_seed', -1),
                         ('screen_size', 2),
                         ('temp_screen_size', 2),
                         ('sound_buffer_size', 4),
                         ('animation', 'Always'),
                         ('unit_speed', 120),
                         ('text_speed', 10),
                         ('cursor_speed', 80),
                         ('show_terrain', 1),
                         ('show_objective', 1),
                         ('autocursor', 1),
                         ('music_volume', 0.3),
                         ('sound_volume', 0.3),
                         ('autoend_turn', 1),
                         ('confirm_end', 1),
                         ('hp_map_team', 'All'),
                         ('hp_map_cull', 'All'),
                         ('display_hints', 0),
                         ('key_SELECT', 120),
                         ('key_BACK', 122),
                         ('key_INFO', 99),
                         ('key_AUX', 97),
                         ('key_START', 115),
                         ('key_LEFT', 276),
                         ('key_RIGHT', 275),
                         ('key_UP', 273),
                         ('key_DOWN', 274)])

    def parse_ini(fn):
        with open(fn) as fp:
            for line in fp:
                split_line = line.strip().split('=')
                lines[split_line[0]] = split_line[1]

    try:
        parse_ini('saves/config.ini')
    except OSError:
        if os.path.exists('data/config.ini'):
            parse_ini('data/config.ini')

    float_vals = ('music_volume', 'sound_volume')
    string_vals = ('animation', 'hp_map_team', 'hp_map_cull')
    for k, v in lines.items():
        if k in float_vals:
            lines[k] = float(v)
        elif k in string_vals:
            pass
        else:  # convert to int
            lines[k] = int(v) 

    return lines

def save_settings():
    with open('saves/config.ini', 'w') as fp:
        write_out = '\n'.join([k + '=' + str(v) for k, v in SETTINGS.items()])
        fp.write(write_out)

text_speed_options = list(reversed([0, 1, 5, 10, 15, 20, 32, 50, 80, 112, 150]))
SETTINGS = read_config_file()
print("debug: %s" % SETTINGS['debug'])
