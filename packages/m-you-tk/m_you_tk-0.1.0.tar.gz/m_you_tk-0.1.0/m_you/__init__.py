import ctypes
import os
import sys

# --- 1. ЛОГИКА ЗАГРУЗКИ ШРИФТА ---
# Используем dirname(__file__), чтобы путь всегда вел внутрь установленного пакета
font_path = os.path.join(os.path.dirname(__file__), "assets", "material.ttf")

if os.path.exists(font_path):
    if sys.platform == "win32":
        # Загрузка для Windows (без установки в систему)
        ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
    # На Linux (Arch) шрифты обычно подхватываются из папки ~/.fonts или через fontconfig,
    # но для кроссплатформенности на Win этого кода достаточно.
else:
    # Не принтим ошибку в продакшне, чтобы не спамить пользователю в консоль, 
    # либо используем logging
    pass

# --- 2. ЭКСПОРТ КОМПОНЕНТОВ ---
# Это позволяет писать: from m_you import MaterialButton
from .button import MaterialButton
from .input import MaterialInput
from .dropdown import MaterialDropdown
from .checkbox import MaterialCheckbox
from .switch import MaterialSwitch
from .slider import MaterialSlider
from .radiobutton import MaterialRadioButton
from .toast import MaterialToast

# Список того, что будет доступно при "from m_you import *"
__all__ = [
    "MaterialButton",
    "MaterialInput",
    "MaterialDropdown",
    "MaterialCheckbox",
    "MaterialSwitch",
    "MaterialSlider",
    "MaterialRadioButton",
    "MaterialToast"
]