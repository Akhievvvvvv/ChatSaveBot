import os
import json
from datetime import datetime, timedelta

USERS_FILE = "data/users.json"
MESSAGES_DIR = "data/messages/"

os.makedirs(MESSAGES_DIR, exist_ok=True)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def add_message(user_id, chat_id, message_data):
    chat_dir = os.path.join(MESSAGES_DIR, str(user_id))
    os.makedirs(chat_dir, exist_ok=True)
    filename = os.path.join(chat_dir, f"{chat_id}_{datetime.now().timestamp()}.json")
    with open(filename, "w") as f:
        json.dump(message_data, f, ensure_ascii=False)
