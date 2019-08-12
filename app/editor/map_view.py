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

    def update_view(self):
        pass

    def show_map(self):
        if self.current_map:
            image = QImage(self.current_map.width * TILEWIDTH, 
                           self.current_map.height * TILEHEIGHT, 
                           QImage.Format_RGB32)

            painter = QPainter()
            painter.begin(image)
            for coord, tile_image in self.map_grid.get_images():
                painter.drawImage(coord[0] * TILEWIDTH, 
                                  coord[1] * TILEHEIGHT, tile_image)
            painter.end()

            self.clear_scene()
            self.pixmap = QPixmap.fromImage(image)
            self.scene.addPixmap(self.pixmap)

    def wheelEvent(self, event):
        if event.delta() > 0 and self.screen_scale < 4:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.delta() < 0 and self.screen_scale > 1:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)
