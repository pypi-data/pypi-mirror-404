import tkinter as tk

class MaterialRadioButton(tk.Canvas):
    def __init__(self, master, text="Option", value=None, variable=None, command=None, **kwargs):
        self.idle_color = "#543996"
        self.active_color = "#6121ff"   
        self.text_color = "#E6E1E5"
        
        self.text = text # Сохраняем текст в self, чтобы он был доступен везде
        self.value = value
        self.variable = variable
        self.command = command
        
        # Параметры анимации точки
        self.dot_size = 0.0  # 0.0 - нет точки, 1.0 - полная точка
        
        kwargs.setdefault('height', 28)
        kwargs.setdefault('width', 180)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        super().__init__(master, **kwargs)
        
        self._draw()
        self.bind("<Button-1>", self._on_click)
        
        if self.variable:
            self.variable.trace_add("write", lambda *args: self._animate_toggle())

    def _draw(self):
        self.delete("all")
        h = int(self.cget('height'))
        self.r = 10 
        self.center_y = h / 2
        self.center_x = 15
        
        # Внешнее кольцо
        self.outer = self.create_oval(
            self.center_x - self.r, self.center_y - self.r, 
            self.center_x + self.r, self.center_y + self.r, 
            outline=self.idle_color, width=2
        )
        
        # Внутренняя точка (теперь она будет менять размер)
        self.inner = self.create_oval(0, 0, 0, 0, fill=self.active_color, outline="")
        
        # Текст (теперь берем из self.text)
        self.create_text(35, self.center_y, text=self.text, fill=self.text_color, 
                         font=("Segoe UI", 10), anchor="w")
        
        self._update_ui()

    def _animate_toggle(self):
        # Логика LERP для размера точки
        is_selected = self.variable.get() == self.value
        target = 1.0 if is_selected else 0.0
        
        diff = target - self.dot_size
        if abs(diff) > 0.05:
            self.dot_size += diff * 0.2
            self._update_ui()
            self.after(16, self._animate_toggle)
        else:
            self.dot_size = target
            self._update_ui()

    def _update_ui(self):
        # Меняем цвет кольца
        color = self.active_color if self.variable.get() == self.value else self.idle_color
        self.itemconfig(self.outer, outline=color)
        
        # Меняем размер точки
        current_r = (self.r - 4) * self.dot_size
        if current_r > 0:
            self.coords(self.inner, 
                        self.center_x - current_r, self.center_y - current_r,
                        self.center_x + current_r, self.center_y + current_r)
            self.itemconfig(self.inner, state="normal")
        else:
            self.itemconfig(self.inner, state="hidden")

    def _on_click(self, event):
        if self.variable:
            self.variable.set(self.value)
        if self.command:
            self.command()