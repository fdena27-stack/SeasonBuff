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

def sync_web_user_id_by_name(user_id, char_name):
    """Автоматически привязывает сгенерированный веб-ID к загруженным из файла баффам, заменяя 0"""
    data = load_lists()
    updated = False
    name_lower = char_name.lower().strip()
    
    for category in ["stroyka", "laboratoriya"]:
        for item in data[category]:
            if item["user_name"].lower().strip() == name_lower and item["user_id"] == 0:
                item["user_id"] = user_id
                updated = True
    if updated:
        save_lists(data)

def get_user_cooldown(category, username):
    """Расчет кулдауна переведен строго на 48 часов"""
    data = load_lists()
    cooldowns = data.get("cooldowns", {})
    user_key = username.lower().strip()
    
    if category in cooldowns and user_key in cooldowns[category]:
        last_give_time = datetime.fromisoformat(cooldowns[category][user_key])
        time_passed = datetime.now() - last_give_time
        remaining_seconds = 48 * 3600 - time_passed.total_seconds()
        if remaining_seconds > 0:
            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            return f"{hours} ч. {minutes} мин."
    return None

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
            uid = generate_web_user_id(existing_user_key, password)
            sync_web_user_id_by_name(uid, existing_user_key)
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
        
        uid = generate_web_user_id(name_key, password)
        sync_web_user_id_by_name(uid, name_key)
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
        
        new_uid = generate_web_user_id(target_username, new_password)
        sync_web_user_id_by_name(new_uid, target_username)
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
    """Логика выдачи баффа с фиксацией категории в основном тексте лога"""
    clean_expired_buffs()
    data = load_lists()
    if index < 0 or index >= len(data[category]): return None
        
    item = data[category][index]
    
    if item["user_name"].lower().strip() == current_user_name.lower().strip():
        time_stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        log_text = f"[{time_stamp}] НАРУШЕНИЕ: Персонаж [{current_user_name}] пытался выдать бафф самому себе в категории {category.upper()}"
        data["archive"].append(log_text)
        save_lists(data)
        return "self_buff_error"
        
    # Проверяем откат выдающего игрока
    cd_check = get_user_cooldown(category, current_user_name)
    if cd_check:
        time_stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        log_text = f"[{time_stamp}] ОШИБКА ДОСТУПА: Персонаж [{current_user_name}] пытался обойти откат в категории {category.upper()}"
        data["archive"].append(log_text)
        save_lists(data)
        return f"cooldown_active:{cd_check}"
        
    percent_value = int(percent_str.replace("%", ""))
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
    
    # ФИКС: Явно переводим ключ категории в читаемый русский текст для основного лога
    cat_title_ru = "СТРОЙКА" if category == "stroyka" else "ЛАБОРАТОРИЯ"
    
    # Добавили [{cat_title_ru}] в текст лога для однозначности
    archive_log = f"[{time_stamp}] Игрок [{current_user_name}] применил Ускорение {percent_str} в категории [{cat_title_ru}] для [{item['user_name']}] (-{reduction} дн.). Новый срок: {item['duration_days']} дн."
    if is_user_in_lists:
        archive_log += f" (Также применилось к нему же как к выдающему: -{giver_reduction} дн.)"
        
    if "cooldowns" not in data:
        data["cooldowns"] = {}
    if category not in data["cooldowns"]:
        data["cooldowns"][category] = {}
    data["cooldowns"][category][c_name_lower] = datetime.now().isoformat()
        
    data["archive"].append(archive_log)
    save_lists(data)
    clean_expired_buffs()
