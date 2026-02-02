import tkinter as tk

class MaterialSlider(tk.Canvas):
    def __init__(self, master, from_=0, to=100, step=1, value=None, **kwargs):
        # 1. Определяем ширину: берем из kwargs или ставим 300 по дефолту
        self.width_val = kwargs.get('width', 300)
        
        # Настройки Canvas
        kwargs.setdefault('height', 70)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', '#1C1B1F')
        super().__init__(master, **kwargs)
        
        # Параметры
        self.from_ = from_
        self.to = to
        self.step = step
        self.idle_color = "#543996"   # Темный в покое
        self.active_color = "#6121ff"  # Твой яркий цвет при движении
        self.track_color = "#38393E"   # Убрал лишнюю запятую тут!
        
        self.margin = 20
        self.current_x = self.margin
        self.target_x = self.margin
        self.value = from_

        # Рисуем трек
        self.track = self.create_line(self.margin, 30, self.width_val - self.margin, 30, 
                                      width=16, capstyle='round', fill=self.track_color)
        
        # Активная линия
        self.active_line = self.create_line(self.margin, 30, self.margin, 30, 
                                            width=16, capstyle='round', fill=self.idle_color)
        
        # Текст значения
        self.label = self.create_text(self.margin, 55, text="", 
                                      fill="#E6E1E5", font=("Arial", 10, "bold"), anchor="w")

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)
        self.bind("<ButtonRelease-1>", lambda e: self.itemconfig(self.active_line, fill=self.idle_color))
        
        self._animate()

        # Установка начального значения
        initial_val = value if value is not None else from_
        self.set(initial_val)

    def _on_drag(self, event):
        self.itemconfig(self.active_line, fill=self.active_color)
        self.target_x = max(self.margin, min(event.x, self.width_val - self.margin))

    def _animate(self):
        lerp_factor = 0.15
        diff = self.target_x - self.current_x
        
        if abs(diff) > 0.1:
            self.current_x += diff * lerp_factor
            self._update_ui(self.current_x)
        
        self.after(16, self._animate)

    def _update_ui(self, x):
        self.coords(self.active_line, self.margin, 30, x, 30)
        
        range_px = self.width_val - (2 * self.margin)
        raw_pos = (x - self.margin) / range_px
        
        # Защита от выхода за границы
        raw_pos = max(0.0, min(raw_pos, 1.0))
        
        val = self.from_ + raw_pos * (self.to - self.from_)
        
        if self.step:
            self.value = round(val / self.step) * self.step
        else:
            self.value = val

        display_text = int(self.value) if self.value == int(self.value) else round(self.value, 1)
        self.itemconfig(self.label, text=str(display_text))

    def get(self):
        return self.value

    def set(self, val):
        # Ограничиваем значение
        val = max(self.from_, min(val, self.to))
        self.value = val
        
        # Рассчитываем целевой X
        range_px = self.width_val - (2 * self.margin)
        percent = (val - self.from_) / (self.to - self.from_)
        self.target_x = self.margin + (percent * range_px)
        
        # Обновляем текст сразу
        display_text = int(self.value) if self.value == int(self.value) else round(self.value, 1)
        self.itemconfig(self.label, text=str(display_text))