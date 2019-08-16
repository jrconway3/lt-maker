class TerrainMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.left_frame = Collection(self)
        self.right_frame = TerrainProperties(self)

        self.grid.addWidget(self.left_frame, 0, 0)
        self.grid.addWidget(self.right_frame, 0, 1)

class TerrainDictModel(QStandardItemModel):
    def __init__(self, window=None):
        super().__init__(window)
        self.terrain_dict = DB.terrain
        for terrain in self.terrain_dict.values():
            item = QStandardItem(terrain.nid + " : " + terrain.name)
            item.setIcon(self.create_terrain_icon(terrain))

    def create_terrain_icon(self, terrain):
        pass

class Collection(QWidget):
    def __init__(self, parent):
        super().__init_(parent)
        self.window = parent
        self.database_editor = self.window.window

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.list_view = QListView(self)
        self.list_view.setMinimumSize(128, 320)
        self.list_view.uniformItemSizes = True

        self.model = TerrainDictModel(self)
        self.list_view.setModel(self.mode)

        self.button = QPushButton("Create New Terrain Type...")
        self.button.clicked.connect(self.create_new_terrain_type)

        self.grid.addWidget(self.list_view, 0, 0)
        self.grid.addWidget(self.button, 1, 0)

    def create_new_terrain_type(self):
        c = commands.CreateNewTerrainType()
        self.database_editor.undo_stack.push(c)

class TerrainProperties(QWidget):
    def __init__(self, parent, current):
        super().__init__(parent)
        self.window = parent
        self.database_editor = self.window.window

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.current = current

        self.portrait = QLabel()

        nid_label = QLabel('Unique ID: ')
        self.nid_edit = QLineEdit(self)
        self.nid_edit.setMaxLength(12)

        name_label = QLabel('Display Name: ')
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(12)

        minimap_label = QLabel('Minimap Type: ')
        self.minimap_edit = QComboBox(self)

        platform_label = QLabel('Combat Platform Type: ')
        self.platform_edit = QComboBox(self)

        movement_label = QLabel('Movement Type: ')
        self.movement_edit = QComboBox(self)







