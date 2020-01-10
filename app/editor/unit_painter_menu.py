class UnitPainterMenu(QWidet):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.main_editor = self.window
        self.map_view = self.main_editor.map_view
        self.current_level = self.main_editor.current_level
        self._data = self.current_level.units

        grid = QGridLayout()
        self.setLayout(grid)

        self.list_view = QListView(self)
        self.list_view.currentChanged = self.on_item_changed

        self.model = UnitModel(self.current_level.units, self)
        self.list_view.setModel(self.model)
        self.list_view.setIconSize(QSize(32, 32))

        grid.addWidget(self.list_view, 0, 0)

        self.create_button = QPushButton("Create Generic Unit...")
        self.create_button.clicked.connect(self.create_generic)
        grid.addWidget(self.create_button, 1, 0)
        self.load_button = QPushButton("Load Unit...")
        self.load_button.clicked.connect(self.load_unit)
        grid.addWidget(self.load_button, 2, 0)

        self.last_touched_generic = None

    def select(self, idx):
        index = self.model.index(idx)
        self.list_view.setCurrentIndex(index)

    def on_item_changed(self, idx):
        # idx = int(idx)
        unit = self._data[idx]
        if unit.position:
            self.map_view.center_on_pos(unit.position)

    def create_generic(self):
        created_unit, ok = GenericUnitDialog.get_unit()
        if ok:
            self.last_touched_generic = created_unit
            self._data.append(created_unit)
            # Select the unit
            idx = self.model.index(self._data.index(created_unit))
            self.list_view.setCurrentIndex(idx)
            self.last_touched_generic = created_unit
            self.window.update_view()

    def load_unit(self):
        unit, ok = DatabaseEditor.get(self, "Units")
        if ok:
            self._data.append(unit)
            # Select the unit
            idx = self.model.index(self._data.index(unit))
            self.list_view.setCurrentIndex(idx)
            self.last_touched_generic = unit
            self.window.update_view()


