import tkinter as tk

class MaterialSwitch(tk.Canvas):
    def __init__(self, master, text="", width=250, **kwargs):
        # Цвета Material You
        self.track_off = "#49454F"
        self.track_on = "#381E72"
        self.thumb_off = "#938F99"
        self.thumb_on = "#D0BCFF"
        self.text_color = "#E6E1E5"
        
        self.is_on = False
        self.anim_p = 0.0
        self.after_id = None
        
        kwargs.setdefault('height', 48)
        kwargs.setdefault('width', width)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        super().__init__(master, **kwargs)

        # 1. Подложка (Track) — капсула
        # Координаты: x=10, y=12 до x=62, y=36 (стандартный размер свитча)
        self.track_id = self.create_oval(10, 12, 34, 36, fill=self.track_off, outline="", tags="target")
        self.track_rect = self.create_rectangle(22, 12, 50, 38, fill=self.track_off, outline="", tags="target")
        self.track_end = self.create_oval(38, 12, 62, 36, fill=self.track_off, outline="", tags="target")

        # 2. Ползунок (Thumb)
        # В выключенном состоянии он меньше и серый
        self.thumb_id = self.create_oval(16, 18, 30, 32, fill=self.thumb_off, outline="", tags="target")

        # 3. Текст
        self.create_text(74, 24, text=text, fill=self.text_color, 
                         font=("Segoe UI", 11), anchor="w", tags="target")

        # Бинды
        self.tag_bind("target", "<Button-1>", lambda e: self.toggle())

    def toggle(self):
        self.is_on = not self.is_on
        target = 1.0 if self.is_on else 0.0
        self._animate(target)

    def _animate(self, target):
        if self.after_id: self.after_cancel(self.after_id)
        step = 0.2
        diff = target - self.anim_p
        if abs(diff) > 0.01:
            self.anim_p += diff * step
            self._update_ui()
            self.after_id = self.after(10, lambda: self._animate(target))
        else:
            self.anim_p = target
            self._update_ui()

    def _lerp_color(self, c1, c2, p):
        def to_rgb(h): return tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb1, rgb2 = to_rgb(c1), to_rgb(c2)
        res = tuple(int(rgb1[i] + (rgb2[i] - rgb1[i]) * p) for i in range(3))
        return "#%02x%02x%02x" % res

    def _update_ui(self):
        p = self.anim_p
        
        # Цвета
        t_color = self._lerp_color(self.track_off, self.track_on, p)
        thumb_color = self._lerp_color(self.thumb_off, self.thumb_on, p)
        
        for tid in [self.track_id, self.track_rect, self.track_end]:
            self.itemconfig(tid, fill=t_color)
        self.itemconfig(self.thumb_id, fill=thumb_color)

        # Движение и размер ручки
        # Выкл: x=16, size=14. Вкл: x=40, size=20
        size = 14 + (6 * p)
        x_base = 16 + (24 * p)
        y_center = 24
        self.coords(self.thumb_id, x_base, y_center - size/2, x_base + size, y_center + size/2)

    def get(self):
        return self.is_on