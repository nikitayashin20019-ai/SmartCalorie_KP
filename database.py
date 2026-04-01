"""
Модуль для работы с базой данных (JSON-файлы).
Поддерживает историю по дням, редактирование и БЖУ.
"""

import json
import os
from datetime import date

DIR_DATA = "data"
FILE_PRODUCTS = os.path.join(DIR_DATA, "products.json")
FILE_RECIPES = os.path.join(DIR_DATA, "recipes.json")
FILE_USER_DATA = "user_data.json"


def load_json(filepath):
    if not os.path.exists(filepath):
        return {} if "products" in filepath else []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_user_data(data):
    with open(FILE_USER_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_products():
    return load_json(FILE_PRODUCTS)


def get_recipes():
    return load_json(FILE_RECIPES)


def _get_data():
    if not os.path.exists(FILE_USER_DATA):
        return {}
    data = load_json(FILE_USER_DATA)
    if isinstance(data, list):
        today = str(date.today())
        migrated_data = {today: data}
        save_user_data(migrated_data)
        return migrated_data
    return data


# --- Универсальные функции с поддержкой дат (date_str=None означает "сегодня") ---


def get_log(date_str=None):
    data = _get_data()
    day = date_str or str(date.today())
    return data.get(day, [])


def add_to_log(
    item_name, calories, meal_type="lunch", grams=None, macros=None, date_str=None
):
    data = _get_data()
    day = date_str or str(date.today())
    if day not in data:
        data[day] = []
    record = {"name": item_name, "calories": calories, "meal": meal_type}
    if grams is not None:
        record["grams"] = grams
    if macros is not None:
        record["macros"] = macros
    data[day].append(record)
    save_user_data(data)


def delete_from_log(index, date_str=None):
    data = _get_data()
    day = date_str or str(date.today())
    if day in data and 0 <= index < len(data[day]):
        del data[day][index]
        save_user_data(data)


def update_log(index, new_calories, new_grams, new_macros, date_str=None):
    """Обновляет существующую запись (для функции редактирования)."""
    data = _get_data()
    day = date_str or str(date.today())
    if day in data and 0 <= index < len(data[day]):
        data[day][index]["calories"] = new_calories
        data[day][index]["grams"] = new_grams
        data[day][index]["macros"] = new_macros
        save_user_data(data)


def get_total(date_str=None):
    return sum(item["calories"] for item in get_log(date_str))


def get_macros(date_str=None):
    log = get_log(date_str)
    total_p, total_f, total_c = 0, 0, 0
    for item in log:
        macros = item.get("macros", {})
        total_p += macros.get("p", 0)
        total_f += macros.get("f", 0)
        total_c += macros.get("c", 0)
    return {"p": round(total_p, 1), "f": round(total_f, 1), "c": round(total_c, 1)}


def get_user_goal():
    return _get_data().get("goal", 2200)


def save_user_goal(new_goal):
    data = _get_data()
    data["goal"] = new_goal
    save_user_data(data)


def get_user_macros_goal():
    return _get_data().get("macros_goal", {"p": 100, "f": 70, "c": 300})


def save_user_macros_goal(p, f, c):
    data = _get_data()
    data["macros_goal"] = {"p": p, "f": f, "c": c}
    save_user_data(data)


# --- Вода ---
def get_water(date_str=None):
    data = _get_data()
    day = date_str or str(date.today())
    return data.get("water_" + day, 0)


def add_water(ml, date_str=None):
    data = _get_data()
    day = date_str or str(date.today())
    key = "water_" + day
    data[key] = data.get(key, 0) + ml
    save_user_data(data)


def reset_water(date_str=None):
    data = _get_data()
    day = date_str or str(date.today())
    data["water_" + day] = 0
    save_user_data(data)
