import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import date, timedelta, datetime


from database import (
    get_products,
    get_recipes,
    get_log,
    add_to_log,
    get_total,
    delete_from_log,
    update_log,
    get_user_goal,
    save_user_goal,
    get_water,
    add_water,
    reset_water,
    get_macros,
    get_user_macros_goal,
    save_user_macros_goal,
)
import ai_scanner

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MEAL_TYPES = {
    "breakfast": {"title": "🌅 Завтрак", "color": "#F39C12"},
    "lunch": {"title": "☀️ Обед", "color": "#E74C3C"},
    "dinner": {"title": "🌙 Ужин", "color": "#3498DB"},
    "snack": {"title": "🍎 Перекус", "color": "#2ECC71"},
}

# ==========================================
# ВСПЛЫВАЮЩИЕ ОКНА (ДИАЛОГИ)
# ==========================================


class InputDialog(ctk.CTkToplevel):
    def __init__(self, title, prompt, parent):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x180")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        ctk.CTkLabel(self, text=prompt, font=ctk.CTkFont(size=16)).pack(pady=(20, 10))
        self.entry = ctk.CTkEntry(
            self, height=40, font=ctk.CTkFont(size=16), justify="center"
        )
        self.entry.pack(padx=20, fill="x")
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self.on_ok())
        ctk.CTkButton(self, text="ОК", height=35, command=self.on_ok).pack(pady=15)

    def on_ok(self):
        self.result = self.entry.get()
        self.destroy()


class MacroGoalDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Нормы БЖУ")
        self.geometry("300x250")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        ctk.CTkLabel(
            self,
            text="Введите нормы на день:",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 15))
        goals = get_user_macros_goal()
        self.entry_p = ctk.CTkEntry(self, placeholder_text="Белки (г)", height=35)
        self.entry_p.pack(padx=30, fill="x", pady=5)
        self.entry_p.insert(0, str(goals["p"]))
        self.entry_f = ctk.CTkEntry(self, placeholder_text="Жиры (г)", height=35)
        self.entry_f.pack(padx=30, fill="x", pady=5)
        self.entry_f.insert(0, str(goals["f"]))
        self.entry_c = ctk.CTkEntry(self, placeholder_text="Углеводы (г)", height=35)
        self.entry_c.pack(padx=30, fill="x", pady=5)
        self.entry_c.insert(0, str(goals["c"]))
        ctk.CTkButton(
            self,
            text="Сохранить",
            height=35,
            fg_color="#27AE60",
            hover_color="#2ECC71",
            command=self.on_ok,
        ).pack(pady=15)

    def on_ok(self):
        try:
            self.result = {
                "p": float(self.entry_p.get()),
                "f": float(self.entry_f.get()),
                "c": float(self.entry_c.get()),
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числа", parent=self)


class AnalysisDialog(ctk.CTkToplevel):
    def __init__(self, title, text, parent):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        self.grab_set()
        self.txt = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14))
        self.txt.pack(fill="both", expand=True, padx=10, pady=10)
        self.txt.insert("1.0", text)
        self.txt.configure(state="disabled")
        ctk.CTkButton(self, text="Закрыть", command=self.destroy).pack(pady=(0, 10))


class AddFoodDialog(ctk.CTkToplevel):
    def __init__(self, product_name, product_data, parent):
        super().__init__(parent)
        self.title("Добавить в дневник")
        self.geometry("350x300")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self.base_cal = product_data["cal"]
        self.base_macros = {
            "p": product_data.get("p", 0),
            "f": product_data.get("f", 0),
            "c": product_data.get("c", 0),
        }
        if "(1 шт" in product_name or "(ломтик" in product_name:
            self.is_piece = True
            label_text = "Количество (шт):"
            default_val = "1"
            mult = 1
        else:
            self.is_piece = False
            label_text = "Сколько грамм съели?"
            default_val = "100"
            mult = 100
        self.mult = mult
        ctk.CTkLabel(
            self, text=product_name, font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 5))
        ctk.CTkLabel(
            self,
            text=f"{self.base_cal} ккал | Б:{self.base_macros['p']} Ж:{self.base_macros['f']} У:{self.base_macros['c']} в 100г",
            text_color="gray50",
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 15))
        ctk.CTkLabel(self, text=label_text).pack()
        frame_entry = ctk.CTkFrame(self, fg_color="transparent")
        frame_entry.pack(pady=10)
        self.entry = ctk.CTkEntry(
            frame_entry,
            width=150,
            height=40,
            font=ctk.CTkFont(size=16),
            justify="center",
        )
        self.entry.pack(side="left", padx=(0, 10))
        self.entry.insert(0, default_val)
        self.entry.bind("<KeyRelease>", self._update_calc)
        self.btn_add = ctk.CTkButton(
            frame_entry,
            text="Добавить",
            width=120,
            height=40,
            fg_color="#27AE60",
            hover_color="#2ECC71",
            command=self._on_ok,
        )
        self.btn_add.pack(side="left")
        self._update_calc()
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def _update_calc(self, event=None):
        try:
            val = float(self.entry.get().replace(",", "."))
            mult = val / self.mult
            self._tmp_macros = {
                "p": round(self.base_macros["p"] * mult, 1),
                "f": round(self.base_macros["f"] * mult, 1),
                "c": round(self.base_macros["c"] * mult, 1),
            }
            self.btn_add.configure(
                text=f"Добавить ({round(self.base_cal * mult)} ккал)"
            )
        except ValueError:
            self.btn_add.configure(text="Добавить")
            self._tmp_macros = {}

    def _on_ok(self):
        try:
            val = float(self.entry.get().replace(",", "."))
            if val <= 0:
                raise ValueError
            self.result = {
                "calories": round((val / self.mult) * self.base_cal),
                "grams": val if not self.is_piece else None,
                "macros": self._tmp_macros,
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число", parent=self)


class EditEntryDialog(ctk.CTkToplevel):
    def __init__(self, item_data, parent):
        super().__init__(parent)
        self.title("Редактировать порцию")
        self.geometry("300x200")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self.old_cal = item_data["calories"]
        self.old_macros = item_data.get("macros", {})
        self.old_grams = item_data.get("grams")
        ctk.CTkLabel(
            self, text=item_data["name"], font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))
        label = "Новое количество (шт):" if self.old_grams is None else "Новые граммы:"
        ctk.CTkLabel(self, text=label).pack()
        self.entry = ctk.CTkEntry(
            self, height=40, font=ctk.CTkFont(size=16), justify="center"
        )
        self.entry.pack(padx=20, fill="x", pady=10)
        self.entry.insert(0, str(self.old_grams if self.old_grams else 1))
        self.entry.bind("<KeyRelease>", self._update_calc)
        self.btn_ok = ctk.CTkButton(
            self,
            text="Сохранить",
            height=35,
            fg_color="#F39C12",
            hover_color="#F1C40F",
            command=self._on_ok,
        )
        self.btn_ok.pack(pady=10)
        self._update_calc()

    def _update_calc(self, event=None):
        try:
            old_val = (
                float(str(self.old_grams).replace(",", ".")) if self.old_grams else 1.0
            )
            new_val = float(self.entry.get().replace(",", "."))
            mult = (new_val / old_val) if old_val != 0 else 1
            self._new_cal = round(self.old_cal * mult)
            self._new_macros = {
                k: round(v * mult, 1) for k, v in self.old_macros.items()
            }
            self.btn_ok.configure(text=f"Сохранить ({self._new_cal} ккал)")
        except ValueError:
            pass

    def _on_ok(self):
        try:
            val = float(self.entry.get().replace(",", "."))
            if val <= 0:
                raise ValueError
            self.result = {
                "calories": self._new_cal,
                "grams": val if self.old_grams is not None else None,
                "macros": self._new_macros,
            }
            self.destroy()
        except:
            messagebox.showerror("Ошибка", "Введите число", parent=self)


class AddRecipeDialog(ctk.CTkToplevel):
    def __init__(self, recipe, parent):
        super().__init__(parent)
        self.title("Добавить рецепт")
        self.geometry("400x350")
        self.resizable(False, False)
        self.grab_set()
        self.recipe = recipe
        self.result = None
        tw = recipe["total_weight_grams"]
        ctk.CTkLabel(
            self, text=recipe["name"], font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=recipe["description"], text_color="gray50").pack()
        macros = recipe.get("macros_per_100g", {})
        ctk.CTkLabel(
            self,
            text=f"Б:{macros.get('p','?')} Ж:{macros.get('f','?')} У:{macros.get('c','?')} на 100г",
            text_color="gray40",
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 15))
        ctk.CTkLabel(self, text=f"Сколько грамм съели? (Всего: {tw}г)").pack()
        frame_entry = ctk.CTkFrame(self, fg_color="transparent")
        frame_entry.pack(pady=10)
        self.entry = ctk.CTkEntry(
            frame_entry,
            width=150,
            height=40,
            font=ctk.CTkFont(size=16),
            justify="center",
        )
        self.entry.pack(side="left", padx=(0, 10))
        self.entry.insert(0, str(tw))
        self.entry.bind("<KeyRelease>", self._update_calc)
        self.btn_add = ctk.CTkButton(
            frame_entry,
            text="Добавить",
            width=120,
            height=40,
            fg_color="#27AE60",
            hover_color="#2ECC71",
            command=self._on_ok,
        )
        self.btn_add.pack(side="left")
        self._update_calc()
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def _update_calc(self, event=None):
        try:
            grams = float(self.entry.get().replace(",", "."))
            tw = self.recipe["total_weight_grams"]
            calc_cal = round((grams / tw) * self.recipe["total_calories"])
            macros = self.recipe.get("macros_per_100g", {})
            self._tmp_macros = {
                "p": round(macros.get("p", 0) * (grams / 100), 1),
                "f": round(macros.get("f", 0) * (grams / 100), 1),
                "c": round(macros.get("c", 0) * (grams / 100), 1),
            }
            self.btn_add.configure(text=f"Добавить ({calc_cal} ккал)")
        except ValueError:
            self.btn_add.configure(text="Добавить")
            self._tmp_macros = {}

    def _on_ok(self):
        try:
            grams = float(self.entry.get().replace(",", "."))
            if grams <= 0:
                raise ValueError
            tw = self.recipe["total_weight_grams"]
            calc_cal = round((grams / tw) * self.recipe["total_calories"])
            self.result = {
                "calories": calc_cal,
                "grams": grams,
                "macros": self._tmp_macros,
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число", parent=self)


# ==========================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ==========================================


class CalorieApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SmartCalorie — Трекер питания с ИИ")
        self.geometry("850x650")
        self.minsize(800, 550)
        self.current_meal = "lunch"
        self.current_date = str(date.today())

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._create_sidebar()
        self._create_main_content()

    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="🍽 SmartCalorie",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 30))

        btns = [
            ("📊 Дашборд", self._show_dashboard, 1),
            ("➕ Добавить еду", self._show_add_food, 2),
            ("📖 Рецепты", self._show_recipes, 3),
            ("🤖 ИИ Сканер", self._show_ai, 4),
            ("💬 ИИ Советник", self._show_chat, 5),
            ("📈 Аналитика", self._show_analytics, 6),
        ]
        for text, cmd, row in btns:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=cmd,
            )
            btn.grid(row=row, column=0, padx=20, pady=8)

        ctk.CTkButton(
            self.sidebar_frame,
            text="🌙/☀️ Тема",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self._toggle_theme,
        ).grid(row=7, column=0, padx=20, pady=20)

    def _create_main_content(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self._show_dashboard()

    def _clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        for w in self.sidebar_frame.winfo_children():
            if isinstance(w, ctk.CTkButton):
                w.configure(fg_color="transparent")

    def _toggle_theme(self):
        ctk.set_appearance_mode(
            "light" if ctk.get_appearance_mode() == "dark" else "dark"
        )

    # ==================== ДАШБОРД ====================
    def _show_dashboard(self):
        self._clear_content()
        self.sidebar_frame.winfo_children()[1].configure(fg_color=("gray75", "gray25"))
        d = self.current_date

        # Навигация
        nav_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkButton(
            nav_frame,
            text="← Вчера",
            width=80,
            height=28,
            fg_color="transparent",
            border_width=1,
            command=lambda: self._change_date(-1),
        ).pack(side="left")
        date_text = d
        if d == str(date.today()):
            date_text = "Сегодня"
        elif d == str(date.today() - timedelta(days=1)):
            date_text = "Вчера"
        ctk.CTkLabel(
            nav_frame, text=date_text, font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            nav_frame,
            text="Завтра →",
            width=80,
            height=28,
            fg_color="transparent",
            border_width=1,
            command=lambda: self._change_date(1),
        ).pack(side="right")

        # Кнопки настроек
        set_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        set_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(
            set_frame,
            text="⚙ Цель (Ккал)",
            width=100,
            height=28,
            fg_color="transparent",
            border_width=1,
            command=self._change_goal_dialog,
        ).pack(side="left")
        ctk.CTkButton(
            set_frame,
            text="⚙ БЖУ Нормы",
            width=100,
            height=28,
            fg_color="transparent",
            border_width=1,
            command=self._change_macros_goal_dialog,
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            set_frame,
            text="🧠 ИИ Анализ дня",
            width=130,
            height=28,
            fg_color="#8E44AD",
            hover_color="#9B59B6",
            command=self._analyze_day_with_ai,
        ).pack(side="left")

        # Блок 1: Калории и Вода
        top_widgets = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_widgets.pack(fill="x", pady=(0, 10))
        top_widgets.grid_columnconfigure(0, weight=1)
        top_widgets.grid_columnconfigure(1, weight=1)

        prog_frame = ctk.CTkFrame(
            top_widgets, corner_radius=10, fg_color=("gray85", "gray15")
        )
        prog_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        goal = get_user_goal()
        total = get_total(d)
        pct = min((total / goal) * 100, 100)
        ctk.CTkLabel(
            prog_frame,
            text=f"Калории: {total} / {goal}",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(15, 5), padx=15, anchor="w")
        bar = ctk.CTkProgressBar(prog_frame)
        bar.pack(padx=15, fill="x", pady=(0, 15))
        bar.set(pct / 100)

        water_frame = ctk.CTkFrame(
            top_widgets, corner_radius=10, fg_color=("gray85", "gray15")
        )
        water_frame.grid(row=0, column=1, sticky="nsew")
        water_ml = get_water(d)
        water_pct = min((water_ml / 2000) * 100, 100)
        ctk.CTkLabel(
            water_frame,
            text=f"💧 Вода: {water_ml} мл",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(15, 5), padx=15, anchor="w")
        w_bar = ctk.CTkProgressBar(water_frame, fg_color="#3498DB")
        w_bar.pack(padx=15, fill="x")
        w_bar.set(water_pct / 100)
        water_btn_frame = ctk.CTkFrame(water_frame, fg_color="transparent")
        water_btn_frame.pack(pady=(5, 15))
        ctk.CTkButton(
            water_btn_frame,
            text="+ 250 мл",
            height=25,
            fg_color="#3498DB",
            width=100,
            command=lambda: self._water_action(add=True),
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            water_btn_frame,
            text="Сбросить 💧",
            height=25,
            fg_color="transparent",
            border_width=1,
            text_color="gray50",
            width=100,
            command=lambda: self._water_action(add=False),
        ).pack(side="left", padx=5)

        # Блок 2: Шкалы БЖУ
        macros_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        macros_frame.pack(fill="x", pady=(0, 10))
        macros_frame.grid_columnconfigure(0, weight=1)
        macros_frame.grid_columnconfigure(1, weight=1)
        macros_frame.grid_columnconfigure(2, weight=1)
        current_macros = get_macros(d)
        goal_macros = get_user_macros_goal()
        colors = [
            ("Белки", "p", "#E74C3C", 0),
            ("Жиры", "f", "#F1C40F", 1),
            ("Углеводы", "c", "#3498DB", 2),
        ]
        for name, key, color, col in colors:
            frame = ctk.CTkFrame(
                macros_frame, corner_radius=10, fg_color=("gray85", "gray15")
            )
            frame.grid(row=0, column=col, sticky="nsew", padx=5 if col != 0 else (0, 5))
            val = current_macros[key]
            g = goal_macros[key]
            p = min((val / g) * 100, 100) if g > 0 else 0
            ctk.CTkLabel(
                frame,
                text=f"{name}: {val}/{g}г",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color,
            ).pack(pady=(10, 2), padx=10, anchor="w")
            bar = ctk.CTkProgressBar(frame, fg_color=color)
            bar.pack(padx=10, fill="x", pady=(0, 10))
            bar.set(p / 100)

        # Блок 3: Список еды
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        log = get_log(d)
        grouped_log = {m: [] for m in MEAL_TYPES}
        for item in log:
            meal = item.get("meal", "snack")
            if meal not in grouped_log:
                meal = "snack"
            grouped_log[meal].append(item)

        has_food = False
        for meal_key, meal_info in MEAL_TYPES.items():
            items = grouped_log[meal_key]
            if not items:
                continue
            has_food = True
            ctk.CTkLabel(
                scroll,
                text=meal_info["title"],
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=meal_info["color"],
                anchor="w",
            ).pack(fill="x", pady=(15, 5), anchor="w")
            ctk.CTkLabel(
                scroll,
                text=f"{sum(i['calories'] for i in items)} ккал",
                text_color="gray50",
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).pack(anchor="w")

            for item in items:
                actual_index = log.index(item)
                card = ctk.CTkFrame(
                    scroll,
                    corner_radius=8,
                    border_width=1,
                    border_color=("gray70", "gray30"),
                )
                card.pack(fill="x", pady=3)
                card.bind(
                    "<Button-1>",
                    lambda e, idx=actual_index, itm=item: self._edit_action(idx, itm),
                )

                txt_frame = ctk.CTkFrame(card, fg_color="transparent")
                txt_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                name_str = item["name"]
                if item.get("grams"):
                    name_str += f" ({item['grams']}г)"
                if item.get("macros"):
                    m = item["macros"]
                    name_str += (
                        f"  [Б:{m.get('p',0)} Ж:{m.get('f',0)} У:{m.get('c',0)}]"
                    )

                lbl = ctk.CTkLabel(
                    txt_frame,
                    text=name_str,
                    font=ctk.CTkFont(size=14),
                    anchor="w",
                    cursor="hand2",
                )
                lbl.pack(anchor="w")
                lbl.bind(
                    "<Button-1>",
                    lambda e, idx=actual_index, itm=item: self._edit_action(idx, itm),
                )

                ctk.CTkButton(
                    card,
                    text="✕",
                    width=30,
                    height=30,
                    fg_color="transparent",
                    text_color="red",
                    hover_color=("gray60", "gray40"),
                    command=lambda idx=actual_index: self._delete_action(idx),
                ).pack(side="right", padx=5)

        if not has_food:
            ctk.CTkLabel(scroll, text="Пока пусто.", text_color="gray50").pack(pady=40)

    def _change_date(self, days):
        d = datetime.strptime(self.current_date, "%Y-%m-%d").date() + timedelta(
            days=days
        )
        self.current_date = str(d)
        self._show_dashboard()

    def _water_action(self, add=True):
        if add:
            add_water(250, self.current_date)
        else:
            reset_water(self.current_date)
        self._show_dashboard()

    def _delete_action(self, index):
        delete_from_log(index, self.current_date)
        self._show_dashboard()

    def _edit_action(self, index, item_data):
        dialog = EditEntryDialog(item_data, self)
        self.wait_window(dialog)
        if dialog.result:
            update_log(
                index,
                dialog.result["calories"],
                dialog.result["grams"],
                dialog.result["macros"],
                self.current_date,
            )
            self._show_dashboard()

    def _change_goal_dialog(self):
        dialog = InputDialog("Настройки", "Новая норма калорий:", self)
        self.wait_window(dialog)
        if dialog.result:
            try:
                save_user_goal(int(dialog.result))
                self._show_dashboard()
            except ValueError:
                pass

    def _change_macros_goal_dialog(self):
        dialog = MacroGoalDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            save_user_macros_goal(**dialog.result)
            self._show_dashboard()

    def _analyze_day_with_ai(self):
        log = get_log(self.current_date)
        if not log:
            return messagebox.showinfo("Пусто", "Сначала добавьте еду!")
        total = get_total(self.current_date)
        goal = get_user_goal()
        macros = get_macros(self.current_date)
        goal_macros = get_user_macros_goal()
        meal_summary = "\n".join(
            [f"- {item['name']} ({item['calories']} ккал)" for item in log]
        )

        prompt = f"""Проанализируй день как диетолог. Цель: {goal} ккал. Съел: {total} ккал.
Макросы: Б:{macros['p']}/{goal_macros['p']}г Ж:{macros['f']}/{goal_macros['f']}г У:{macros['c']}/{goal_macros['c']}г.
Меню:\n{meal_summary}
Краткий вывод на 4 предложения: что хорошо, что плохо, что съесть завтра?"""

        dialog = AnalysisDialog("🧠 ИИ Анализ", "⏳ Анализирую ваш день...\n\n", self)
        self.update()
        response = ai_scanner.ask_dietitian(prompt)
        dialog.txt.configure(state="normal")
        dialog.txt.delete("1.0", "end")
        if isinstance(response, dict):
            dialog.txt.insert("1.0", f"❌ Ошибка: {response.get('error', '')}")
        else:
            dialog.txt.insert("1.0", f"✅ Анализ за {self.current_date}:\n\n{response}")
        dialog.txt.configure(state="disabled")

    # ==================== ДОБАВИТЬ ЕДУ ====================
    def _show_add_food(self):
        self._clear_content()
        self.sidebar_frame.winfo_children()[2].configure(fg_color=("gray75", "gray25"))
        ctk.CTkLabel(
            self.content_frame,
            text="Добавить продукт",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))
        seg = ctk.CTkSegmentedButton(
            self.content_frame,
            values=[v["title"] for v in MEAL_TYPES.values()],
            command=self._change_meal,
        )
        seg.pack(fill="x", pady=(0, 15))
        seg.set(MEAL_TYPES[self.current_meal]["title"])

        custom_frame = ctk.CTkFrame(
            self.content_frame, corner_radius=10, fg_color=("gray85", "gray15")
        )
        custom_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(
            custom_frame,
            text="Нет в списке? Введите вручную:",
            text_color="gray50",
            font=ctk.CTkFont(size=13),
        ).pack(pady=(10, 5), padx=15, anchor="w")
        custom_entry_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        custom_entry_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.custom_name = ctk.CTkEntry(
            custom_entry_frame, placeholder_text="Название", height=35
        )
        self.custom_name.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.custom_cal = ctk.CTkEntry(
            custom_entry_frame, placeholder_text="Ккал", width=80, height=35
        )
        self.custom_cal.pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            custom_entry_frame,
            text="+",
            width=35,
            height=35,
            fg_color="#27AE60",
            command=self._add_custom_food,
        ).pack(side="left")

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._update_search)
        ctk.CTkEntry(
            self.content_frame,
            textvariable=self.search_var,
            placeholder_text="Поиск продукта...",
            height=40,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", pady=(0, 15))
        self.search_results = ctk.CTkScrollableFrame(
            self.content_frame, fg_color="transparent"
        )
        self.search_results.pack(fill="both", expand=True)
        self._update_search()

    def _add_custom_food(self):
        name, cal = self.custom_name.get(), self.custom_cal.get()
        if not name or not cal:
            return messagebox.showwarning("Ошибка", "Заполните поля")
        try:
            add_to_log(name, int(cal), self.current_meal, date_str=self.current_date)
            self.custom_name.delete(0, "end")
            self.custom_cal.delete(0, "end")
        except ValueError:
            messagebox.showerror("Ошибка", "Калории должны быть числом")

    def _change_meal(self, value):
        for key, val in MEAL_TYPES.items():
            if val["title"] == value:
                self.current_meal = key

    def _update_search(self, *args):
        for w in self.search_results.winfo_children():
            w.destroy()
        query = self.search_var.get().lower()
        for name, data in get_products().items():
            if query in name.lower():
                text = f"{name}  —  {data['cal']} ккал  [Б:{data.get('p',0)} Ж:{data.get('f',0)} У:{data.get('c',0)}]"
                card = ctk.CTkFrame(
                    self.search_results,
                    corner_radius=8,
                    border_width=1,
                    border_color=("gray70", "gray30"),
                )
                card.pack(fill="x", pady=4)
                lbl = ctk.CTkLabel(
                    card,
                    text=text,
                    anchor="w",
                    font=ctk.CTkFont(size=13),
                    cursor="hand2",
                )
                lbl.pack(padx=15, pady=10, anchor="w", fill="x")
                lbl.bind(
                    "<Button-1>", lambda e, n=name, d=data: self._open_food_dialog(n, d)
                )

    def _open_food_dialog(self, name, data):
        dialog = AddFoodDialog(name, data, self)
        self.wait_window(dialog)
        if dialog.result:
            add_to_log(
                name,
                dialog.result["calories"],
                self.current_meal,
                dialog.result.get("grams"),
                dialog.result.get("macros"),
                self.current_date,
            )

    # ==================== РЕЦЕПТЫ ====================
    def _show_recipes(self):
        self._clear_content()
        self.sidebar_frame.winfo_children()[3].configure(fg_color=("gray75", "gray25"))
        ctk.CTkButton(
            self.content_frame,
            text="✨ Придумать рецепт из того, что есть в холодильнике",
            height=40,
            fg_color="#8E44AD",
            hover_color="#9B59B6",
            command=self._generate_ai_recipe,
        ).pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(
            self.content_frame,
            text="Книга рецептов",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(0, 15))
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        for r in get_recipes():
            tw, cal = r["total_weight_grams"], r["total_calories"]
            macros = r.get("macros_per_100g", {})
            sub = f"{r['description']} | Б:{macros.get('p','?')} Ж:{macros.get('f','?')} У:{macros.get('c','?')}"
            card = ctk.CTkFrame(
                scroll,
                corner_radius=10,
                border_width=1,
                border_color=("gray70", "gray30"),
            )
            card.pack(fill="x", pady=8)
            lbl_name = ctk.CTkLabel(
                card,
                text=f"{r['name']}  —  {cal} ккал",
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w",
                cursor="hand2",
            )
            lbl_name.pack(padx=15, pady=(10, 0), anchor="w")
            lbl_name.bind("<Button-1>", lambda e, rec=r: self._open_recipe_dialog(rec))
            lbl_sub = ctk.CTkLabel(
                card,
                text=sub,
                text_color="gray50",
                font=ctk.CTkFont(size=12),
                anchor="w",
                cursor="hand2",
            )
            lbl_sub.pack(padx=15, pady=(0, 10), anchor="w")
            lbl_sub.bind("<Button-1>", lambda e, rec=r: self._open_recipe_dialog(rec))

    def _generate_ai_recipe(self):
        dialog = InputDialog("ИИ-Повар", "Что у вас есть? (через запятую)", self)
        self.wait_window(dialog)
        if dialog.result:
            result = ai_scanner.generate_recipe(dialog.result)
            if "error" in result:
                messagebox.showerror("Ошибка ИИ", result["error"])
            else:
                self._open_recipe_dialog(result)

    def _open_recipe_dialog(self, recipe):
        dialog = AddRecipeDialog(recipe, self)
        self.wait_window(dialog)
        if dialog.result:
            add_to_log(
                f"{recipe['name']} ({dialog.result['grams']}г)",
                dialog.result["calories"],
                self.current_meal,
                dialog.result["grams"],
                dialog.result.get("macros"),
                self.current_date,
            )

    # ==================== ИИ СКАНЕР ====================
    def _show_ai(self):
        self._clear_content()
        self.sidebar_frame.winfo_children()[4].configure(fg_color=("gray75", "gray25"))
        ctk.CTkLabel(
            self.content_frame,
            text="ИИ Сканер еды",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))
        seg = ctk.CTkSegmentedButton(
            self.content_frame,
            values=[v["title"] for v in MEAL_TYPES.values()],
            command=self._change_meal,
        )
        seg.pack(fill="x", pady=(0, 15))
        seg.set(MEAL_TYPES[self.current_meal]["title"])
        upload_fr = ctk.CTkFrame(
            self.content_frame,
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color="transparent",
        )
        upload_fr.pack(fill="x", pady=(0, 15), ipady=20)
        self.lbl_img = ctk.CTkLabel(
            upload_fr, text="Фото не выбрано", text_color="gray50"
        )
        self.lbl_img.pack()
        ctk.CTkButton(upload_fr, text="Выбрать фото", command=self._select_img).pack(
            pady=(15, 0)
        )
        ctk.CTkButton(
            self.content_frame,
            text="🚀 Распознать",
            height=40,
            fg_color="#D35400",
            hover_color="#E67E22",
            command=self._scan_img,
        ).pack(fill="x", pady=(0, 15))
        self.txt_res = ctk.CTkTextbox(
            self.content_frame, state="disabled", font=ctk.CTkFont(size=14)
        )
        self.txt_res.pack(fill="both", expand=True)

    def _select_img(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.lbl_img.configure(
                text=path.split("/")[-1], text_color=("gray10", "gray90")
            )
            self._cur_img_path = path

    def _scan_img(self):
        if not hasattr(self, "_cur_img_path"):
            return messagebox.showwarning("Ошибка", "Выберите фото!")
        self.txt_res.configure(state="normal")
        self.txt_res.delete("1.0", "end")
        self.txt_res.insert("1.0", "⏳ Анализирую фото...\n")
        self.txt_res.configure(state="disabled")
        self.update()
        result = ai_scanner.analyze_image(self._cur_img_path)
        self.txt_res.configure(state="normal")
        self.txt_res.delete("1.0", "end")
        if result and "error" not in result[0]:
            total = 0
            self.txt_res.insert("end", "✅ Найдено:\n\n")
            for item in result:
                self.txt_res.insert(
                    "end", f"• {item['name']}: {item['calories']} ккал\n"
                )
                total += item["calories"]
                add_to_log(
                    f"[ИИ] {item['name']}",
                    item["calories"],
                    self.current_meal,
                    date_str=self.current_date,
                )
            self.txt_res.insert("end", f"\nИтого: {total} ккал.")
        else:
            self.txt_res.insert(
                "end", f"❌ Ошибка: {result[0].get('error', 'Неизвестно')}"
            )
        self.txt_res.configure(state="disabled")

    # ==================== ИИ ЧАТ ====================
    def _show_chat(self):
        self._clear_content()
        self.sidebar_frame.winfo_children()[5].configure(fg_color=("gray75", "gray25"))
        ctk.CTkLabel(
            self.content_frame,
            text="💬 ИИ Диетолог",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(
            self.content_frame, text="Спросите совет по питанию.", text_color="gray50"
        ).pack(anchor="w", pady=(0, 15))
        self.chat_box = ctk.CTkTextbox(self.content_frame, font=ctk.CTkFont(size=14))
        self.chat_box.pack(fill="both", expand=True, pady=(0, 15))
        self.chat_box.insert("1.0", "ИИ: Здравствуйте! Чем могу помочь?\n\n")
        self.chat_box.configure(state="disabled")
        input_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        input_frame.pack(fill="x")
        self.chat_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Напишите вопрос...",
            height=45,
            font=ctk.CTkFont(size=14),
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda e: self._send_chat())
        ctk.CTkButton(
            input_frame,
            text="Отправить",
            width=120,
            height=45,
            fg_color="#8E44AD",
            hover_color="#9B59B6",
            command=self._send_chat,
        ).pack(side="right")

    def _send_chat(self):
        text = self.chat_entry.get().strip()
        if not text:
            return
        self.chat_entry.delete(0, "end")
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"Вы: {text}\n\nИИ: Думаю...\n\n")
        self.chat_box.configure(state="disabled")
        self.update()
        response = ai_scanner.ask_dietitian(text)
        self.chat_box.configure(state="normal")
        content = self.chat_box.get("1.0", "end").replace("ИИ: Думаю...\n\n", "")
        self.chat_box.delete("1.0", "end")
        self.chat_box.insert("1.0", content)
        if isinstance(response, dict):
            self.chat_box.insert("end", f"ИИ: Ошибка API\n\n")
        else:
            self.chat_box.insert("end", f"ИИ: {response}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    # ==================== АНАЛИТИКА ====================
    # ==================== АНАЛИТИКА (NATIVE CANVAS UI) ====================
    def _show_analytics(self):
        self._clear_content()
        self.sidebar_frame.winfo_children()[6].configure(fg_color=("gray75", "gray25"))
        ctk.CTkLabel(
            self.content_frame,
            text="Статистика за 7 дней",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(0, 20))

        # --- Собираем данные ---
        days_list, cals_list = [], []
        today = date.today()
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            d_str = str(d)
            days_list.append(d.strftime("%d.%m"))
            cals_list.append(get_total(d_str))
        goal = get_user_goal()

        # --- Виджеты сверху ---
        widgets_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        widgets_frame.pack(fill="x", pady=(0, 20))
        widgets_frame.grid_columnconfigure(0, weight=1)
        widgets_frame.grid_columnconfigure(1, weight=1)
        widgets_frame.grid_columnconfigure(2, weight=1)

        avg_cal = round(sum(cals_list) / 7) if cals_list else 0
        min_cal = min(cals_list) if cals_list else 0
        max_cal = max(cals_list) if cals_list else 0

        stats = [
            ("📉 Среднее", f"{avg_cal} ккал", "#E67E22"),
            ("⬇️ Минимум", f"{min_cal} ккал", "#2ECC71"),
            ("⬆️ Максимум", f"{max_cal} ккал", "#E74C3C"),
        ]
        for i, (title, val, color) in enumerate(stats):
            card = ctk.CTkFrame(
                widgets_frame, corner_radius=10, fg_color=("gray85", "gray15")
            )
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            ctk.CTkLabel(
                card, text=title, text_color="gray50", font=ctk.CTkFont(size=13)
            ).pack(pady=(15, 0))
            ctk.CTkLabel(
                card,
                text=val,
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=color,
            ).pack(pady=(0, 15))

        chart_card = ctk.CTkFrame(
            self.content_frame, corner_radius=15, fg_color="#050505", height=200
        )
        chart_card.pack(fill="x", pady=(0, 0))

        # Создаем холст внутри карточки (используем стандартный tk.Canvas для точного контроля фона)
        import tkinter as tk

        canvas = tk.Canvas(chart_card, bg="#050505", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=20, pady=20)

        # Палитра (Строгий минимализм)
        bar_color = "#E67E22"  # Оранжевый
        text_color = "#666666"  # Тусклый серый
        goal_color = "#333333"  # Едва заметная линия нормы

        # Отступы внутри холста
        pad_left = 40
        pad_right = 20
        pad_top = 30
        pad_bottom = 25
        bar_width = 15  # ТОНКИЕ столбцы

        # Ждем обновления экрана, чтобы получить реальные размеры холста
        chart_card.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()

        # Защита от слишком маленького окна
        if w < 100 or h < 100:
            w, h = 600, 150

        # Математика масштаба
        max_y = max(
            goal, max(cals_list) if cals_list else 0, 500
        )  # Минимум 500, чтобы нули не выглядели гигантскими
        available_h = h - pad_top - pad_bottom
        available_w = w - pad_left - pad_right
        step_x = available_w / 7

        # Рисуем линию нормы (если она влезает)
        if goal <= max_y:
            goal_y = pad_top + available_h - (goal / max_y) * available_h
            canvas.create_line(
                pad_left,
                goal_y,
                w - pad_right,
                goal_y,
                fill=goal_color,
                width=1,
                dash=(4, 4),
            )
            canvas.create_text(
                pad_left - 5,
                goal_y,
                text=str(goal),
                fill=goal_color,
                anchor="e",
                font=("Segoe UI", 9),
            )

        # Рисуем столбцы и цифры
        for i in range(7):
            val = cals_list[i]
            date_str = days_list[i]

            # Координаты
            x_center = pad_left + step_x * i + step_x / 2
            x_left = x_center - bar_width / 2

            if val > 0:
                bar_height = (val / max_y) * available_h
                y_bottom = pad_top + available_h
                y_top = y_bottom - bar_height

                # Рисуем столбец
                canvas.create_rectangle(
                    x_left,
                    y_top,
                    x_left + bar_width,
                    y_bottom,
                    fill=bar_color,
                    outline="",
                )

                # Рисуем цифру над столбцом
                canvas.create_text(
                    x_center,
                    y_top - 10,
                    text=str(val),
                    fill=text_color,
                    font=("Segoe UI", 9),
                )
            else:
                y_bottom = pad_top + available_h

            # Рисуем дату снизу
            canvas.create_text(
                x_center,
                y_bottom + 15,
                text=date_str,
                fill=text_color,
                font=("Segoe UI", 10),
            )
