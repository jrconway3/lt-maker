from app.map_maker.value_noise import get_generic_noise_map
from app.map_maker.terrain_database import DB_terrain
from app.map_maker.map_prefab import MapPrefab

# Generate truly random terrain

def generate(tilemap: MapPrefab) -> MapPrefab:
    tilemap.resize(30, 30, 0, 0)
    
    noise_map = get_generic_noise_map(tilemap.width, tilemap.height)
    for x in range(tilemap.width):
        for y in range(tilemap.height):
            pos = (x, y)
            value = noise_map.get(*pos)
            if value > 0.75:
                tilemap.set(pos, None, DB_terrain.get('Mountain'))
            elif value > 0.7:
                tilemap.set(pos, None, DB_terrain.get('Hill'))
            elif value > 0.4:
                tilemap.set(pos, None, DB_terrain.get('Plains'))
            elif value > 0.3:
                tilemap.set(pos, None, DB_terrain.get('Sand'))
            else:
                tilemap.set(pos, None, DB_terrain.get('Sea'))

    return tilemap
