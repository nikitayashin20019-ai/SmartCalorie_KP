import customtkinter as ctk
from gui import CalorieApp

if __name__ == "__main__":
    # Устанавливаем масштаб шрифтов для Retina дисплеев (по желанию)
    ctk.set_widget_scaling(1.1)

    app = CalorieApp()
    app.mainloop()
