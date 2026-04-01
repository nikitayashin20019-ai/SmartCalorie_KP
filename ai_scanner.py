"""
Модуль для работы с ИИ (OpenRouter API).
Содержит: сканер по фото, чат-советник, генератор рецептов.
"""

import base64
import requests
import json

API_KEY = "ВАШ_OPENROUTER_API_KEY"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "meta-llama/llama-3.2-11b-vision-instruct"


def _send_to_ai(messages):
    """Базовая функция отправки запроса к ИИ."""
    if API_KEY == "ВАШ_OPENROUTER_API_KEY":
        return {"error": "API ключ не задан в ai_scanner.py"}
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"model": MODEL_NAME, "messages": messages}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return {"error": str(e)}


def _clean_json(text):
    """Очищает текст от markdown-оберток ```json ... ```"""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()


def analyze_image(image_path):
    """Сканер еды по фото. Возвращает список [{'name': '..', 'calories': X}]."""
    try:
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": 'Определи еду на фото. Верни СТРОГО JSON массив без markdown. Формат: [{"name": "Название", "calories": Число}]. Оцени порцию на 100 г.',
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ]
        content = _send_to_ai(messages)
        if isinstance(content, dict):
            return [content]

        parsed_data = json.loads(_clean_json(content))

        # ЗАЩИТА: Если ИИ вернул один объект {} вместо списка [],
        # мы искусственно оборачиваем его в список, чтобы код не сломался
        if isinstance(parsed_data, dict):
            return [parsed_data]

        return parsed_data
    except Exception as e:
        return [{"error": f"Ошибка парсинга: {e}"}]


def ask_dietitian(user_text):
    """Чат с ИИ-диетологом. Возвращает строку с советом."""
    system_prompt = "Ты профессиональный диетолог и фитнес-тренер. Отвечай кратко, по делу, максимум 3-4 предложения. Советуй здоровую еду."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]
    return _send_to_ai(messages)


def generate_recipe(ingredients_text):
    """Генерирует рецепт из переданных ингредиентов. Возвращает словарь как в recipes.json."""
    prompt = f'Придумай блюдо из этих ингредиентов: {ingredients_text}. Верни СТРОГО JSON объект без markdown. Формат: {{"name": "Название", "description": "Описание", "total_weight_grams": 300, "total_calories": 400, "macros_per_100g": {{"p": 10.0, "f": 5.0, "c": 20.0}}}}'
    messages = [{"role": "user", "content": prompt}]
    content = _send_to_ai(messages)
    if isinstance(content, dict):
        return content
    try:
        return json.loads(_clean_json(content))
    except Exception as e:
        return {"error": f"ИИ не смог сгенерировать рецепт: {e}"}
