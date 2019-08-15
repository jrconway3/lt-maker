from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap, QPainter

from app.data.constants import TILEWIDTH, TILEHEIGHT

class MapView(QGraphicsView):
    def __init__(self, window=None):
        super().__init__()
        self.window = window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setMinimumSize(15*TILEWIDTH, 10*TILEHEIGHT)
        self.setStyleSheet("background-color:rgb(128, 128, 128);")

        self.current_map = None
        self.pixmap = None
        self.screen_scale = 1

    def set_current_map(self, tilemap):
        self.current_map = tilemap
        self.update_view()

    def clear_scene(self):
        self.scene.clear()

    def update_view(self):
        self.clear_scene()
        self.show_map()

    def show_map(self):
        if self.current_map:
            self.scene.addPixmap(QPixmap(self.current_map.base_image))

    def show_map_from_individual_sprites(self):
        if self.current_map:
            image = QImage(self.current_map.width * TILEWIDTH, 
                           self.current_map.height * TILEHEIGHT, 
                           QImage.Format_RGB32)

            painter = QPainter()
            painter.begin(image)
            for coord, tile_image in self.current_map.get_tile_sprites():
                painter.drawImage(coord[0] * TILEWIDTH, 
                                  coord[1] * TILEHEIGHT, tile_image)
            painter.end()

            self.clear_scene()
            self.pixmap = QPixmap.fromImage(image)
            self.scene.addPixmap(self.pixmap)

    def wheelEvent(self, event):
        if event.angleDelta() > 0 and self.screen_scale < 4:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.angleDelta() < 0 and self.screen_scale > 1:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)
