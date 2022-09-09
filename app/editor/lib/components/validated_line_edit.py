from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5.QtCore import QSize, QRegExp
from PyQt5.QtGui import QRegExpValidator

# Custom Widgets
from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ComboBox

class NidLineEdit(QLineEdit):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    reg_ex = QRegExp(r"[^\(\)]*")
    input_validator = QRegExpValidator(reg_ex, self)
    self.setValidator(input_validator)