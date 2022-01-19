import random

RANDOM_SEED = 0

def random_choice(choices: list, pos: tuple, seed: int = None):
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed + pos[0] * 1024 + pos[1])
    return random.choice(choices)

def random_random(pos: tuple, seed: int = None, offset: int = 0):
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed + pos[0] * 1024 + pos[1] + offset)
    return random.random()

def edge_random(pos1: tuple, pos2: tuple, seed: int = None):
    """
    Uses two positions (essentially the edge between these two positions)
    to seed the RNG
    north, then south; west, then east
    """
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed + pos1[0] * 1024**3 + pos1[1] * 1024**2 + pos2[0] * 1024 + pos2[1])
    return random.random()

def flood_fill(tilemap, pos: tuple) -> set:
    blob_positions = set()
    unexplored_stack = []

    def find_similar(starting_pos, terrain_nid):
        unexplored_stack.append(starting_pos)

        while unexplored_stack:
            current_pos = unexplored_stack.pop()

            if current_pos in blob_positions:
                continue
            if not tilemap.check_bounds(current_pos):
                continue
            nid = tilemap.get_terrain(current_pos)
            if nid != terrain_nid:
                continue

            blob_positions.add(current_pos)
            unexplored_stack.append((current_pos[0] + 1, current_pos[1]))
            unexplored_stack.append((current_pos[0] - 1, current_pos[1]))
            unexplored_stack.append((current_pos[0], current_pos[1] + 1))
            unexplored_stack.append((current_pos[0], current_pos[1] - 1))

    # Get coords like current coord in current_layer
    current_tile = tilemap.get_terrain(pos)
    # Determine which coords should be flood-filled
    find_similar(pos, current_tile)
    return blob_positions
