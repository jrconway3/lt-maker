from app.utilities.typing import NestedPrimitiveDict
from app.data.serialization.migrators.migrator_base import MigratorBase


class Migrator0(MigratorBase):
    """Migration from version 0 to 1 - Add Weight stat"""
    
    def migrate_database(self, db_dict: NestedPrimitiveDict) -> NestedPrimitiveDict:
        """Add Weight stat if it doesn't exist"""
        
        # Ensure stats list exists
        if 'stats' not in db_dict:
            db_dict['stats'] = []
        
        # Check if Weight stat already exists
        existing_stats = {stat.get('nid') for stat in db_dict['stats'] if isinstance(stat, dict)}
        
        if 'WT' not in existing_stats:
            # Add Weight stat
            weight_stat = {
                'nid': 'WT',
                'name': 'Weight',
                'maximum': 30,
                'desc': 'Cumulative weight of equipped items',
                'position': 'hidden',
                'growth_colors': False,
                'hidden_stat': True
            }
            db_dict['stats'].append(weight_stat)
            
            # Add Weight stat to all units
            if 'units' in db_dict:
                for unit in db_dict['units']:
                    if isinstance(unit, dict):
                        if 'bases' in unit and isinstance(unit['bases'], dict):
                            unit['bases']['WT'] = 0
                        if 'growths' in unit and isinstance(unit['growths'], dict):
                            unit['growths']['WT'] = 0
            
            # Add Weight stat to all classes  
            if 'classes' in db_dict:
                for klass in db_dict['classes']:
                    if isinstance(klass, dict):
                        if 'bases' in klass and isinstance(klass['bases'], dict):
                            klass['bases']['WT'] = 0
                        if 'growths' in klass and isinstance(klass['growths'], dict):
                            klass['growths']['WT'] = 0
                        if 'growth_bonus' in klass and isinstance(klass['growth_bonus'], dict):
                            klass['growth_bonus']['WT'] = 0
                        if 'promotion' in klass and isinstance(klass['promotion'], dict):
                            klass['promotion']['WT'] = 0
                        if 'max_stats' in klass and isinstance(klass['max_stats'], dict):
                            klass['max_stats']['WT'] = 30
        
        return db_dict
    
    def migrate_resources(self, resource_dict: NestedPrimitiveDict, data_dir: str) -> NestedPrimitiveDict:
        """No resource changes needed for Weight stat migration"""
        return resource_dict