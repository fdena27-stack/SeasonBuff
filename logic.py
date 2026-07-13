import hashlib
from datetime import datetime, timedelta
from storage import load_lists, save_lists

def clean_expired_buffs():
    """Проверяет 24 часа без изменений, отнимает дни и удаляет баффы <= 7 дней"""
    data = load_lists()
    updated = False
    now = datetime.now()
    time_stamp = now.strftime("%d.%m.%Y %H:%M")
    
    for category in ["stroyka", "laboratoriya"]:
        valid_buffs = []
        cat_title = "СТРОЙКА" if category == "stroyka" else "ЛАБОРАТОРИЯ"
        
        for item in data[category]:
            last_updated_date = datetime.fromisoformat(item["last_updated"])
            hours_passed = (now - last_updated_date).total_seconds() / 3600
            days_to_subtract = int(hours_passed // 24)
            
            if days_to_subtract > 0:
                old_days = item["duration_days"]
                item["duration_days"] -= days_to_subtract
                auto_log = f"[{time_stamp}] АВТО-ОБНОВЛЕНИЕ: Прошло {days_to_subtract} дн. Срок [{item['user_name']}] в {cat_title} уменьшен с {old_days} до {item['duration_days']} дн."
                data["archive"].append(auto_log)
                item["last_updated"] = (last_updated_date + timedelta(days=days_to_subtract)).isoformat()
                updated = True
            
            created_date = datetime.fromisoformat(item["created_at"])
            end_date = created_date + timedelta(days=item["duration_days"])
            days_left = (end_date - now).days + 1
            
            if days_left > 7 and item["duration_days"] > 7:
                valid_buffs.append(item)
            else:
                del_log = f"[{time_stamp}] АВТО-УДАЛЕНИЕ: Запрос [{item['user_name']}] в {cat_title} удален (Оставалось: {item['duration_days']} дн.)"
                data["archive"].append(del_log)
                updated = True
                
        data[category] = valid_buffs
    if updated:
        save_lists(data)

def hash_password(password):
    """Шифрует пароль в SHA-256 хэш"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_web_user_id(username, password):
    """Генерирует уникальный цифровой ID на основе связки Ник + Пароль (аналог Telegram ID)"""
    combined = f"{username.lower().strip()}:{password}"
    return abs(hash(combined)) % (10**8)

def verify_or_register_user(username, password):
    """Проверяет пароль существующего или регистрирует нового пользователя"""
    data = load_lists()
    name_key = username.strip()
    name_lower = name_key.lower()
    time_stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    existing_user_key = None
    for u in data["users"]:
        if u.lower() == name_lower:
            existing_user_key = u
            break
            
    p_hash = hash_password(password)
    
    if existing_user_key:
        if data["users"][existing_user_key] == p_hash:
            return "auth_success"
        else:
            log_text = f"[{time_stamp}] НАРУШЕНИЕ: Попытка подбора пароля к нику [{existing_user_key}]"
            data["archive"].append(log_text)
            save_lists(data)
            return "wrong_password"
    else:
        data["users"][name_key] = p_hash
        log_text = f"[{time_stamp}] РЕГИСТРАЦИЯ: Создан новый аккаунт персонажа [{name_key}]"
        data["archive"].append(log_text)
        save_lists(data)
        return "reg_success"

def admin_reset_user_password(target_username, new_password):
    """Позволяет админу принудительно переписать пароль любого пользователя"""
    data = load_lists()
    time_stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    if target_username in data["users"]:
        new_hash = hash_password(new_password)
        data["users"][target_username] = new_hash
        log_text = f"[{time_stamp}] АДМИН-ДЕЙСТВИЕ: Администратор принудительно изменил пароль пользователю [{target_username}]"
        data["archive"].append(log_text)
        save_lists(data)
        return True
    return False

def add_buff_request(category, user_id, user_name, text, duration_days):
    if duration_days <= 7: return False
    clean_expired_buffs()
    data = load_lists()
    time_stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    c_name_lower = user_name.lower().strip()
    cat_title = "СТРОЙКА" if category == "stroyka" else "ЛАБОРАТОРИЯ"
    
    for item in data[category]:
        item_name_lower = item["user_name"].lower().strip()
        if item["user_id"] == user_id or item_name_lower == c_name_lower:
            log_text = f"[{time_stamp}] НАРУШЕНИЕ: Персонаж [{user_name}] (ID: {user_id}) пытался повторно добавиться в категорию {cat_title}"
            data["archive"].append(log_text)
            save_lists(data)
            return False
    
    now_str = datetime.now().isoformat()
    data[category].append({
        "user_id": user_id, 
        "user_name": user_name,
        "text": text,
        "duration_days": duration_days, 
        "created_at": now_str, 
        "last_updated": now_str
    })
    save_lists(data)
    return True

def remove_user_buff(category, user_id):
    clean_expired_buffs()
    data = load_lists()
    for index, item in enumerate(data[category]):
        if item["user_id"] == user_id:
            removed = data[category].pop(index)
            save_lists(data)
            return removed
    return None

def process_give_buff(category, index, percent_str, current_user_id, current_user_name):
    """Логика выдачи баффа: теперь имя выдающего пишется в лог ВСЕГДА"""
    clean_expired_buffs()
    data = load_lists()
    if index < 0 or index >= len(data[category]): return None
        
    percent_value = int(percent_str.replace("%", ""))
    item = data[category][index]
    
    old_duration = item["duration_days"]
    reduction = int((old_duration * percent_value / 100) + 0.99)
    if reduction == 0: reduction = 1
        
    item["duration_days"] -= reduction
    item["last_updated"] = datetime.now().isoformat()
    
    c_name_lower = current_user_name.lower().strip()
    is_user_in_lists = False
    giver_reduction = 0
    
    for b in data[category]:
        if b["user_id"] == current_user_id or b["user_name"].lower().strip() == c_name_lower:
            is_user_in_lists = True
            b_old = b["duration_days"]
            giver_reduction = int((b_old * percent_value / 100) + 0.99)
            if giver_reduction == 0: giver_reduction = 1
            b["duration_days"] -= giver_reduction
            b["last_updated"] = datetime.now().isoformat()
            break
                
    buff_result_text = f"Ускорение {percent_str} - {item['user_name']}"
    time_stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # ФИКС: В базовый текст лога добавлено имя выдающего — [current_user_name]
    archive_log = f"[{time_stamp}] Игрок [{current_user_name}] применил Ускорение {percent_str} для [{item['user_name']}] (-{reduction} дн.). Новый срок: {item['duration_days']} дн."
    if is_user_in_lists:
        archive_log += f" (Также применилось к нему же как к выдающему в категории {category}: -{giver_reduction} дн.)"
        
    data["archive"].append(archive_log)
    save_lists(data)
    clean_expired_buffs()
    return buff_result_text
