import re
from collections import Counter

class Multiset(Counter):
    def __contains__(self, item):
        return self[item] > 0

def get_next_name(name, names):
    if name not in names:
        return name
    else:
        counter = 1
        while True:
            test_name = name + (' (%s)' % counter)
            if test_name not in names:
                return test_name
            counter += 1

def get_next_int(name, names):
    if name not in names:
        return name
    else:
        counter = 1
        while True:
            test_name = str(counter)
            if test_name not in names:
                return test_name
            counter += 1

def get_next_generic_nid(name, names):
    if name not in names:
        return name
    else:
        counter = int(name) + 1
        while True:
            test_name = str(counter)
            if test_name not in names:
                return test_name
            counter += 1

def find_last_number(s: str):
    last_number = re.findall(r'\d+$', s)
    if last_number:
        return int(last_number[-1])
    return None

def get_prefix(s: str):
    last_number = re.findall(r'\d+', s)
    if last_number:
        idx = re.search(r'\d+', s).span(0)[0]
        return s[:idx]
    else:
        idx = s.index('.')
        return s[:idx]

def intify(s: str) -> list:
    vals = s.split(',')
    return [int(i) for i in vals]

def skill_parser(s: str) -> list:
    if s is not None:
        each_skill = [each.split(',') for each in s.split(';')]
        split_line = [(int(s_l[0]), s_l[1]) for s_l in each_skill]
        return split_line
    else:
        return []

def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

def clamp(i, min_, max_):
    return min(max_, max(min_, i))

def lerp(a, b, t):
    t = clamp(t, 0, 1)
    return (b - a) * t

def compare_teams(t1: str, t2: str) -> bool:
    # Returns True if allies, False if enemies
    if t1 is None or t2 is None:
        return None
    elif t1 == t2:
        return True
    elif (t1 == 'player' and t2 == 'other') or (t2 == 'player' and t1 == 'other'):
        return True
    else:
        return False

def calculate_distance(pos1: tuple, pos2: tuple) -> int:
    """
    Taxicab/Manhattan distance
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def process_terms(terms):
    """ 
    Processes weighted lists
    """
    weight_sum = sum(term[1] for term in terms)
    if weight_sum <= 0:
        return 0
    return sum(float(val * weight) for weight, val in terms) / weight_sum

def dot_product(a: tuple, b: tuple) -> float:
    return sum(a[i] * b[i] for i in range(len(b)))

def farthest_away_pos(pos, valid_moves: set, enemy_pos: set):
    if valid_moves and enemy_pos:
        avg_x, avg_y = 0, 0
        for x, y in enemy_pos:
            avg_x += x
            avg_y += y
        avg_x /= len(enemy_pos)
        avg_y /= len(enemy_pos)
        return sorted(valid_moves, key=lambda move: calculate_distance((avg_x, avg_y), move))[-1]
    else:
        return None

def smart_farthest_away_pos(position, valid_moves: set, enemy_pos: set):
    # Figure out avg position of enemies
    if valid_moves and enemy_pos:
        avg_x, avg_y = 0, 0
        for pos, mag in enemy_pos:
            diff_x = position[0] - pos[0]
            diff_y = position[1] - pos[1]
            diff_x /= mag
            diff_y /= mag
            avg_x += diff_x
            avg_y += diff_y
        avg_x /= len(enemy_pos)
        avg_y /= len(enemy_pos)
        # Now have vector pointing away from average enemy position
        # I want the dot product between that vector and the vector of each possible move
        # The highest dot product is the best 
        return sorted(valid_moves, key=lambda move: dot_product((move[0] - position[0], move[1] - position[1]), (avg_x, avg_y)))[-1]
    else:
        return None
