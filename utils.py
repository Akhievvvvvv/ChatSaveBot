import os, json
from config import DATA_PATH

# Создаём папку для данных, если нет
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

def load_users():
    path = os.path.join(DATA_PATH, "users.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    path = os.path.join(DATA_PATH, "users.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def save_message(user_id, message):
    path = os.path.join(DATA_PATH, f"{user_id}_messages.json")
    data = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(message)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
