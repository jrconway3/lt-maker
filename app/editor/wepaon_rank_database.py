class WeaponRankDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.weapon_ranks
        title: str = "Weapon Rank"
        right_frame = WeaponRankProperties

        def deletion_func(view, idx):
            return view.model().rowCount() > 1

        deletion_criteria = (deletion_func, "Cannot delete when only one rank left!")
        collection_molde = WeaponRankModel
        return cls(data, title, right_frame, deletion_criteria, collection_model, parent)

class WeaponRankModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            weapon_rank = self._data[index.row()]
            text = weapon_rank.nid
            return text
        return None

    def create_new(self):
        return self._data.add_new_defaut(DB)

    # Called on delete
    def delete(self, idx):
        weapon_rank = self._data[idx]
        nid = weapon_rank.nid

    # Called on create_new, new, and duplicate
    def update_watchers(self, idx):
        pass

    # Called on drag and drop
    def update_drag_watchers(self, fro, to):
        pass    

class WeaponRankProperties(QWidget):
    def __init__(self, parent, current=None):
        pass