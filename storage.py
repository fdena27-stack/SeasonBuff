import json
import os

# Проверяем, запущен ли бот на сервере Amvera
if os.path.exists("/data") or os.environ.get("AMVERA_APP_ID"):
    # Если папки /data физически еще нет в контейнере, принудительно создаем ее
    if not os.path.exists("/data"):
        try:
            os.makedirs("/data", exist_ok=True)
        except Exception:
            pass
    JSON_FILE = "/data/lists.json"  # Строго в постоянное хранилище Amvera
else:
    JSON_FILE = "lists.json"        # Локально на вашем ПК

def load_lists():
    if not os.path.exists(JSON_FILE):
        return {"users": {}, "stroyka": [], "laboratoriya": [], "archive": []}
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {"users": {}, "stroyka": [], "laboratoriya": [], "archive": []}
        
        if not isinstance(data, dict):
            data = {}
        if "users" not in data:
            data["users"] = {}
        if "stroyka" not in data:
            data["stroyka"] = []
        if "laboratoriya" not in data:
            data["laboratoriya"] = []
        if "archive" not in data:
            data["archive"] = []
            
        return data

def save_lists(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
