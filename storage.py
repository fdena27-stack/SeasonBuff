import json
import os

JSON_FILE = "lists.json"

def load_lists():
    if not os.path.exists(JSON_FILE):
        return {"users": {}, "stroyka": [], "laboratoriya": [], "archive": []}
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "users" not in data:
            data["users"] = {}
        if "archive" not in data:
            data["archive"] = []
        return data

def save_lists(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
