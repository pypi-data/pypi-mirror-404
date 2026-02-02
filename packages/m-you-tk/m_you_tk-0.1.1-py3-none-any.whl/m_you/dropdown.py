import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import time

# Глобальный таймер для предотвращения "сквозного клика"
_last_close_time = 0

def is_globally_locked():
    """Проверяет, прошло ли более 200мс с момента закрытия любого меню"""
    return (time.time() - _last_close_time) < 0.2

class MaterialDropdown(tk.Canvas):
    def __init__(self, master, label="Select Option", options=None, width=300, **kwargs):
        self.bg_color = "#2B2930"
        self.line_idle = "#49454F"
        self.line_active = "#6121ff"
        self.label_color = "#CAC4D0"
        self.text_color = "#E6E1E5"

        self.label_text = label
        self.options = options or []
        self.width_val = width
        self.is_open = False
        self.is_animating = False
        self.anim_progress = 0.0
        self.after_id = None
        self.dropdown_after_id = None

        kwargs.setdefault('height', 56)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', master.cget('bg'))
        kwargs.setdefault('width', width)  # Добавляем эту строку
        super().__init__(master, **kwargs)

        # 1. Фон
        self.rect = self.create_rectangle(0, 0, width, 56, fill=self.bg_color, outline="", tags="target")
        
        # 2. Текст
        self.label_id = self.create_text(16, 28, text=label, fill=self.label_color, 
                                         font=("Segoe UI", 11), anchor="w", tags="target")
        
        # 3. Стрелка (подвинута на 32 от края)
        self._create_arrow_image()
        self.arrow_id = self.create_image(width - 32, 28, image=self.arrow_tk, tags="target")

        # 4. Линии
        self.create_line(0, 54, width, 54, fill=self.line_idle, width=1, tags="line_layer")
        self.active_line = self.create_line(width/2, 54, width/2, 54, fill=self.line_active, width=3, tags="line_layer")
        self.tag_raise("line_layer")

        self.list_window = None

        # Бинды
        self.tag_bind("target", "<Button-1>", self.toggle_menu)

    def _create_arrow_image(self):
        size = 24
        self.base_arrow = Image.new("RGBA", (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(self.base_arrow)
        padding = 7
        coords = [(padding, padding+2), (size-padding, padding+2), (size/2, size-padding+2)]
        draw.polygon(coords, fill=self.label_color)
        self.arrow_tk = ImageTk.PhotoImage(self.base_arrow)

    def toggle_menu(self, event=None):
        if self.is_animating: return 
        if self.is_open:
            self.close_menu()
        else:
            self.open_menu()

    def open_menu(self):
        if self.is_open and not self.is_animating: return
        self.is_open = True
        self.is_animating = True
        self._start_animation(True)
        
        # Создаем Toplevel
        self.list_window = tk.Toplevel(self)
        self.list_window.overrideredirect(True)
        self.list_window.configure(bg="#2B2930")
        self.list_window.attributes("-topmost", True)
        
        container = tk.Frame(self.list_window, bg="#2B2930", padx=2, pady=2)
        container.pack(fill="both", expand=True)

        for opt in self.options:
            btn = tk.Label(container, text=opt, bg="#2B2930", fg=self.text_color,
                           font=("Segoe UI", 11), anchor="w", padx=14, pady=10, cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#36343B"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#2B2930"))
            btn.bind("<Button-1>", lambda e, v=opt: self.select_option(v))

        # --- ИСПРАВЛЕНИЕ: используем self.width_val вместо winfo_width() ---
        # 1. Используем заданную ширину (width=300 или width=400)
        actual_w = self.width_val
        # 2. Получаем координаты относительно экрана
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        
        target_h = len(self.options) * 42 + 4
        # 3. Устанавливаем ширину окна в точности как у Canvas
        self.list_window.geometry(f"{actual_w}x0+{x}+{y}")
        # ------------------------------------

        self._animate_dropdown(0, target_h, actual_w)
        self.list_window.focus_set()
        self.list_window.bind("<FocusOut>", lambda e: self.close_menu())

    def _animate_dropdown(self, current_h, target_h, width):
        if not self.list_window: return
        step = (target_h - current_h) * 0.3 + 2
        if current_h < target_h - 1:
            new_h = int(current_h + step)
            self.list_window.geometry(f"{width}x{new_h}")
            self.dropdown_after_id = self.after(10, lambda: self._animate_dropdown(new_h, target_h, width))
        else:
            self.list_window.geometry(f"{width}x{target_h}")
            self.is_animating = False

    def select_option(self, value):
        self.itemconfig(self.label_id, text=value, fill=self.text_color)
        self.close_menu()

    def close_menu(self, event=None):
        global _last_close_time
        if not self.is_open: return
        self.is_open = False
        self.is_animating = True
        self._start_animation(False)
        
        if self.list_window:
            self.list_window.destroy()
            self.list_window = None
        
        # Ставим метку времени закрытия
        _last_close_time = time.time()
        self.after(150, lambda: setattr(self, 'is_animating', False))

    def _start_animation(self, focus):
        if self.after_id: self.after_cancel(self.after_id)
        target = 1.0 if focus else 0.0
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

    def _lerp_color(self, color_start, color_end, fraction):
        def hex_to_rgb(hex_c):
            hex_c = hex_c.lstrip('#')
            return tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
        c1, c2 = hex_to_rgb(color_start), hex_to_rgb(color_end)
        curr_rgb = tuple(int(c1[i] + (c2[i] - c1[i]) * fraction) for i in range(3))
        return "#%02x%02x%02x" % curr_rgb

    def _update_ui(self):
        p = self.anim_progress
        curr_color = self._lerp_color(self.label_color, self.line_active, p)
        self.itemconfig(self.label_id, fill=curr_color)
        
        # Анимация стрелки
        angle = p * -180
        rotated = self.base_arrow.rotate(angle, resample=Image.BICUBIC)
        r_t, g_t, b_t = tuple(int(curr_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        data = rotated.getdata()
        new_data = [ (r_t, g_t, b_t, item[3]) if item[3] > 0 else item for item in data ]
        rotated.putdata(new_data)
        self.arrow_tk = ImageTk.PhotoImage(rotated)
        self.itemconfig(self.arrow_id, image=self.arrow_tk)
        
        # Линия
        x_start = (self.width_val / 2) * (1 - p)
        x_end = (self.width_val / 2) * (1 + p)
        self.coords(self.active_line, x_start, 54, x_end, 54)
        self.tag_raise("line_layer")

    def get(self):
        val = self.itemcget(self.label_id, "text")
        return val if val != self.label_text else ""