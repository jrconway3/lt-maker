from app.utilities.data import Data, Prefab

class PartyPrefab(Prefab):
    nid: str = None
    name: str = None
    leader: str = None

class PartyCatalog(Data):
    datatype = PartyPrefab
