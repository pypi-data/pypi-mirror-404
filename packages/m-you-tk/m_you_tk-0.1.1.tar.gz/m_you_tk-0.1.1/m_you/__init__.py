import ctypes
import os
import sys

# 1. Находим ПРАВИЛЬНЫЙ путь к файлу шрифта внутри установленного пакета
# __file__ указывает на текущий __init__.py, берем его папку и идем в assets
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(CURRENT_DIR, "assets", "material.ttf")

def load_font():
    if not os.path.exists(font_path):
        return

    if sys.platform == "win32":
        # Код для Windows
        ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
    else:
        # Для Linux (Arch) шрифт обычно подгружается через Fontconfig
        # Если ты используешь PIL (Pillow) для отрисовки иконок, 
        # нужно передавать полный путь font_path прямо в ImageFont.truetype()
        pass

load_font()
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