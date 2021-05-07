def get_palette_pixmap(palette):
    # TODO

class PaletteModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            palette = self._data[index.row()]
            text = palette.nid
            return text
        elif role == Qt.DecorationRole:
            palette = self._data[index.row()]
            pixmap = get_palette_pixmap(palette)
            if pixmap:
                return QIcon(pixmap)
        return None

    def delete(self, idx):
        # Delete watchers
        # None needed -- Nothing else in editor/data uses support pairs 
        super().delete(idx)

    def on_nid_changed(self, old_value, new_value):
        pass

    def create_new(self):
        # TODO
        return Palette()