import inspect
import os

from PyQt5.QtCore import QSettings



GEOMETRY_SETTING_PREFIX = "geometry_setting:"
STATE_SETTING_PREFIX = "state_setting:"

class ComponentSettingsController():
    """
    Provides an interface for interacting with geometry
    settings for the application.
    """
    def __init__(self, company='rainlash', product='Lex Talionis'):
        QSettings.setDefaultFormat(QSettings.IniFormat)
        self.state = QSettings(company, product)
    
    def set_geometry(self, class_type=None, value=None):
        """Sets geometry settings for a specific class

        Args:
            class_type (typeof class): class of object. Defaults to None.
            value (optional): geometry value. Defaults to None.
        """
        if class_type:
            key = _generate_component_key(class_type)
            self.state.setValue(GEOMETRY_SETTING_PREFIX + key, value)

    def get_geometry(self, class_type=None):
        """gets geometry settings for a specific class

        Args:
            class_type (typeof class): class of object. Defaults to None.
        """
        if class_type:
            key = _generate_component_key(class_type)
            self.state.value(GEOMETRY_SETTING_PREFIX + key)

    def set_state(self, class_type=None, value=None):
        """sets state settings for a specific component

        Args:
            class_type ([type], optional): class of object. Defaults to None.
            value ([type], optional): value of state. Defaults to None.
        """
        if class_type:
            key = _generate_component_key(class_type)
            self.state.setValue(STATE_SETTING_PREFIX + key, value)

    def get_state(self, class_type=None):
        """gets state settings for a specific component

        Args:
            class_type ([type], optional): class of object. Defaults to None.
        """
        if class_type:
            key = _generate_component_key(class_type)
            self.state.value(STATE_SETTING_PREFIX + key)

def _generate_component_key(class_type):
    """Given a class, generates a key for said class.
    Used in ComponentSettingsController to key component settings.

    Args:
        class_type (typeof(class)): a class; not an instance of an object, but the class

    Returns:
        string: a key string of the form (file_of_class::class_name)
    """
    return os.path.basename(inspect.getmodule(class_type).__file__) + "::" + class_type.__name__