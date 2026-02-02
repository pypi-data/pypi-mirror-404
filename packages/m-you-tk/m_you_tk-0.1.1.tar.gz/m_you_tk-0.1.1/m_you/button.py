import tkinter as tk
from .dropdown import is_globally_locked

ICON_MAP = {
    "edit": "\ue3c9", "settings": "\ue8b8", "home": "\ue88a",
    "search": "\ue8b6", "favorite": "\ue87d", "delete": "\ue872",
    "add": "\ue145", "check": "\ue5ca", "close": "\ue5cd",
    "menu": "\ue5d2", "person": "\ue7fd", "share": "\ue80d",
    "sound": "\ue050", "wifi": "\ue63e", "battery": "\ue1a4",
    "camera": "\ue412", "folder": "\ue2c7", "email": "\ue0be", "clock": "\ue192" 
}

class MaterialButton(tk.Canvas):
    def __init__(self, master, text="Default", icon="home", command=None, **kwargs):
        self.idle_color = "#543996"
        self.active_color = "#6121ff"
        self.text_color = "#EADDFF"
        
        self.icon_char = ICON_MAP.get(icon.lower(), ICON_MAP["home"])

        kwargs.setdefault('height', 60)
        kwargs.setdefault('width', 200)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        super().__init__(master, **kwargs)
        
        self.command = command
        self._draw(text)

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, text):
        self.delete("all")
        w, h = int(self.cget('width')), int(self.cget('height'))
        pad = 6 
        r = h - (pad * 2)
        
        # Форма кнопки
        self.create_oval(pad, pad, r+pad, h-pad, fill=self.idle_color, outline="", tags="shape")
        self.create_oval(w-r-pad, pad, w-pad, h-pad, fill=self.idle_color, outline="", tags="shape")
        self.create_rectangle(pad+r/2, pad, w-pad-r/2, h-pad + 1, fill=self.idle_color, outline="", tags="shape")
        
        # Контент
        self.create_text(pad + r/2 + 5, h/2, text=self.icon_char, fill=self.text_color,
                         font=("Material Icons", 18), tags="content")
        self.create_text(w/2 + 10, h/2, text=text, fill=self.text_color,
                         font=("Segoe UI", 11, "bold"), tags="content")

    def _on_press(self, event):
        self.itemconfig("shape", fill=self.active_color)
        self.move("all", 1, 1)

    def _on_release(self, event):
        self.itemconfig("shape", fill=self.idle_color)
        self.move("all", -1, -1)
        
        # ПРОВЕРКА: Если только что закрыли меню — игнорируем клик
        if is_globally_locked():
            return
            
        if self.command: 
            self.command()