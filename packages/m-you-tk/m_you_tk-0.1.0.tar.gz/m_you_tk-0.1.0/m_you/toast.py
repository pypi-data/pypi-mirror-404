import tkinter as tk

class MaterialToast(tk.Canvas):
    def __init__(self, master, message="Action completed", duration=2500, **kwargs):
        # Цвета из Button
        self.bg_color = "#543996"      
        self.text_color = "#EADDFF"    
        
        self.master = master
        self.duration = duration
        
        # 1. Адаптивный расчет ширины
        # Примерно 10 пикселей на символ + отступы по бокам
        self.width_val = len(message) * 9 + 60 
        # Ограничиваем, чтобы не был слишком узким или широким
        self.width_val = max(200, min(self.width_val, master.winfo_width() - 40))
        
        kwargs.setdefault('height', 48)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        kwargs.setdefault('width', self.width_val)
        super().__init__(master, **kwargs)

        # Рисуем скругленную капсулу
        r = 24 # Полное скругление для высоты 48
        self.create_oval(0, 0, r*2, 48, fill=self.bg_color, outline="")
        self.create_oval(self.width_val-r*2, 0, self.width_val, 48, fill=self.bg_color, outline="")
        self.create_rectangle(r, 0, self.width_val-r, 48, fill=self.bg_color, outline="")

        # Текст сообщения по центру
        self.create_text(self.width_val/2, 24, text=message, fill=self.text_color, 
                         font=("Segoe UI", 10, "bold"), anchor="center")

        self.is_showing = False

    def show(self):
        if self.is_showing: return
        self.is_showing = True
        
        # 2. Адаптивное позиционирование (всегда центр снизу)
        # Обновляем координаты прямо перед показом на случай, если окно меняли
        x = (self.master.winfo_width() - self.width_val) // 2
        y_start = self.master.winfo_height() + 10
        y_target = self.master.winfo_height() - 70 # Чуть ниже, чем раньше
        
        self.place(x=x, y=y_start)
        self._animate(y_start, y_target, "up")
        
        # Автоматическое скрытие
        self.master.after(self.duration, self.hide)

    def _animate(self, curr_y, target_y, direction):
        if not self.winfo_exists(): return
        
        diff = target_y - curr_y
        step = diff * 0.2 # Мягкий Easing
        
        if abs(diff) > 0.5:
            new_y = curr_y + step
            self.place(y=new_y)
            self.master.after(10, lambda: self._animate(new_y, target_y, direction))
        else:
            self.place(y=target_y)
            if direction == "down":
                self.place_forget()
                self.destroy()

    def hide(self):
        if not self.winfo_exists(): return
        y_curr = self.winfo_y()
        y_end = self.master.winfo_height() + 50
        self._animate(y_curr, y_end, "down")