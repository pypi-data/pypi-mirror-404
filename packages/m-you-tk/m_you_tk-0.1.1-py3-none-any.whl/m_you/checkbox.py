import tkinter as tk

class MaterialCheckbox(tk.Canvas):
    def __init__(self, master, text="Option", width=250, **kwargs):
        self.bg_idle = "#49454F"     
        self.bg_active = "#6121ff"   
        self.tick_color = "#FFFFFF"  
        self.text_color = "#E6E1E5"
        
        self.is_checked = False
        self.anim_p = 0.0
        self.after_id = None
        
        kwargs.setdefault('height', 40)
        kwargs.setdefault('width', width)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        super().__init__(master, **kwargs)

        # 1. НЕВИДИМАЯ ПОДЛОЖКА (Для клика по всей области)
        # Она ловит клики даже там, где нет текста или линий
        self.create_rectangle(0, 0, width, 40, fill="", outline="", tags="target")

        # 2. Рамка чекбокса
        self.box_id = self.create_rectangle(10, 10, 30, 30, outline=self.bg_idle, width=2, tags="target")
        
        # 3. Внутренняя заливка
        self.fill_id = self.create_rectangle(20, 20, 20, 20, fill="", outline="", tags="target")
        
        # 4. Галочка
        self.tick_line1 = self.create_line(14, 20, 14, 20, fill="", width=2, capstyle="round", tags="target")
        self.tick_line2 = self.create_line(19, 25, 19, 25, fill="", width=2, capstyle="round", tags="target")

        # 5. Текст
        self.create_text(40, 20, text=text, fill=self.text_color, 
                         font=("Segoe UI", 10), anchor="w", tags="target")

        # ТЕПЕРЬ ВСЁ С ТЕГОМ "target" БУДЕТ КЛИКАБЕЛЬНЫМ
        self.tag_bind("target", "<Button-1>", lambda e: self.toggle())
        
        # Добавим эффект наведения для всей зоны
        self.tag_bind("target", "<Enter>", lambda e: self.config(cursor="hand2"))
        self.tag_bind("target", "<Leave>", lambda e: self.config(cursor=""))

    def toggle(self):
        self.is_checked = not self.is_checked
        target = 1.0 if self.is_checked else 0.0
        self._animate(target)

    def _animate(self, target):
        if self.after_id: self.after_cancel(self.after_id)
        step = 0.25 # Чуть ускорим для отзывчивости
        diff = target - self.anim_p
        if abs(diff) > 0.01:
            self.anim_p += diff * step
            self._update_ui()
            self.after_id = self.after(10, lambda: self._animate(target))
        else:
            self.anim_p = target
            self._update_ui()

    def _update_ui(self):
        p = self.anim_p
        
        # Цвет и заливка
        if p > 0.05:
            size = 10 * p
            self.coords(self.fill_id, 20-size, 20-size, 20+size, 20+size)
            self.itemconfig(self.fill_id, fill=self.bg_active)
            self.itemconfig(self.box_id, outline=self.bg_active)
        else:
            self.itemconfig(self.fill_id, fill="")
            self.itemconfig(self.box_id, outline=self.bg_idle)

        # Галочка
        p1 = min(1.0, p * 2)
        p2 = max(0.0, (p-0.5)*2)
        
        if p > 0.3:
            color = self.tick_color
            x2, y2 = 14 + (5 * p1), 20 + (5 * p1)
            self.coords(self.tick_line1, 14, 20, x2, y2)
            self.itemconfig(self.tick_line1, fill=color)
            
            if p > 0.5:
                x3, y3 = 19 + (7 * p2), 25 - (10 * p2)
                self.coords(self.tick_line2, 19, 25, x3, y3)
                self.itemconfig(self.tick_line2, fill=color)
            else:
                self.itemconfig(self.tick_line2, fill="")
        else:
            self.itemconfig(self.tick_line1, fill="")
            self.itemconfig(self.tick_line2, fill="")

    def get(self):
        return self.is_checked