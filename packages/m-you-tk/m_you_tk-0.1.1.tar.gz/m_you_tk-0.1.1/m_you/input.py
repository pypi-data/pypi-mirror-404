import tkinter as tk

class MaterialInput(tk.Canvas):
    def __init__(self, master, label="Username", icon=None, width=300, **kwargs):
        self.bg_color = "#2B2930"
        self.line_idle = "#49454F"
        self.line_active = "#6121ff"
        self.label_color = "#CAC4D0"
        self.text_color = "#E6E1E5"
        
        self.width_val = width
        kwargs.setdefault('height', 60) # Немного увеличим высоту, чтобы ничего не резало
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        super().__init__(master, **kwargs)
        
        self.anim_progress = 0.0
        self.after_id = None
        
        # Фон
        self.rect = self.create_rectangle(0, 0, self.width_val, 56, fill=self.bg_color, outline="")
        
        # Смещение текста
        self.text_offset = 16
        if icon:
            self.text_offset = 48
            try:
                from .button import ICON_MAP
                icon_char = ICON_MAP.get(icon.lower(), "")
            except: icon_char = "•"
            
            self.icon_id = self.create_text(24, 28, text=icon_char, fill=self.label_color, 
                                            font=("Material Icons", 18))

        # Поле ввода (Entry)
        # highlightthickness=0 и bd=0 убирают белые рамки и обрезку
        self.entry = tk.Entry(self, bg=self.bg_color, fg=self.text_color,
                              insertbackground=self.line_active, borderwidth=0,
                              highlightthickness=0, font=("Segoe UI", 12))
        
        # Размещаем Entry чуть выше линии
        self.entry_window = self.create_window(self.text_offset, 30, window=self.entry, 
                                               width=self.width_val - self.text_offset - 12, 
                                               anchor="nw")
        
        # Заголовок (Label)
        self.label_id = self.create_text(self.text_offset, 22, text=label, 
                                         fill=self.label_color, font=("Segoe UI", 11), anchor="w")
        
        # Линии
        # Рисуем линии на 1 пиксель короче ширины, чтобы края не "вылезали"
        self.create_line(2, 54, self.width_val-2, 54, fill=self.line_idle, width=1, tags="line")
        self.active_line = self.create_line(self.width_val/2, 54, self.width_val/2, 54, 
                                            fill=self.line_active, width=2, tags="line")

        # Бинды
        self.tag_bind(self.rect, "<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", lambda e: self._start_animation(True))
        self.entry.bind("<FocusOut>", lambda e: self._start_animation(False))

    def _start_animation(self, focus):
        if self.after_id: self.after_cancel(self.after_id)
        # Позиция: наверху если фокус или есть текст
        target = 1.0 if (focus or self.entry.get()) else 0.0
        self._animate_step(target)

    def _animate_step(self, target):
        step = 0.2
        diff = target - self.anim_progress
        if abs(diff) > 0.01:
            self.anim_progress += diff * step
            self._update_ui()
            self.after_id = self.after(10, lambda: self._animate_step(target))
        else:
            self.anim_progress = target
            self._update_ui()
            self.after_id = None

    def _update_ui(self):
        p = self.anim_progress
        has_focus = (self.focus_get() == self.entry)
        
        # Цвет: строго фиолетовый только при фокусе
        curr_color = self.line_active if has_focus else self.label_color
        
        # Позиция и размер текста
        curr_y = 22 - (18 * p)
        curr_size = int(11 - (2 * p))
        
        self.coords(self.label_id, self.text_offset, curr_y)
        self.itemconfig(self.label_id, 
                        font=("Segoe UI", curr_size, "bold" if has_focus else "normal"), 
                        fill=curr_color)
        
        # Линия
        line_visual_color = self.line_active if has_focus else self.line_idle
        self.itemconfig(self.active_line, fill=line_visual_color)
        
        x_start = (self.width_val / 2) * (1 - p) + 2
        x_end = (self.width_val / 2) * (1 + p) - 2
        self.coords(self.active_line, x_start, 54, x_end, 54)
        
        if hasattr(self, 'icon_id'):
            self.itemconfig(self.icon_id, fill=curr_color)
        
        # Чтобы линии всегда были поверх фона
        self.tag_raise("line")

    def get(self):
        return self.entry.get()