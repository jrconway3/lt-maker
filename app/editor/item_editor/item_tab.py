from app.data.database import DB

from app.editor.base_database_gui import DatabaseTab
from app.editor.item_editor.item_properties import ItemProperties
from app.editor.item_editor.item_model import ItemModel

class ItemDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.items
        title = "Item"
        right_frame = ItemProperties
        deletion_criteria = None
        collection_model = ItemModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

# Testing
# Run "python -m app.editor.item_editor.item_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ItemDatabase.create()
    window.show()
    app.exec_()
