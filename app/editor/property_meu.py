import os

from PyQt5.QtWidgets import QDialog, QFormLayout, QFileDialog
from PyQt5.QtCore import QDir

from app.editor.custom_gui import LineSearch

class MusicDialog(QDialog):
    def __init__(self, parent, level):
        super().__init__(parent)
        self.setWindowTitle('Level Music')
        self.level = level

        form = QFormLayout(self)
        form.setVerticalSpacing(0)

        self.music_boxes = {}
        for key in self.level.music.keys():
            box = LineSearch(self)
            box.set_func(lambda: self.find_music(box.line_edit, key))
            form.addWidget(key.replace('_', ' ').capitalize(), box)
            self.music_boxes[key] = box

        self.load(self.level.music)

    def find_music(self, line_edit, music_path):
        starting_path = QDir.currentPath()
        music_file, _ = QFileDialog.getOpenFileName(self, "Select Music File", starting_path,
                                                    "OGG Files (*.ogg);;All Files (*)")
        if music_file:
            head, tail = os.path.split(music_file)
            print(head)
            # if os.path.normpath(head) != os.path.normpath(starting_path):
            #     print('Copying ' + music_file + ' to ' + starting_path)
            #     shutil.copy(music_file, starting_path)
            line_edit.setText(tail.split('.')[0])
            self.level.music[music_path] = music_file

    def load(self, music_dict):
        for key, value in music_dict.items():
            if value:
                head, tail = os.path.split(value)
                self.music_boxes[key].line_edit.setText(tail.split('.')[0])


class PropertiesMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)