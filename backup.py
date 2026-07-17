from datetime import datetime, timedelta
from storage import load_lists, save_lists

def export_to_txt(clean_callback, user_id):
    """Генерирует расширенное содержимое файла с глубокой фильтрацией журналов для суперадмина"""
    clean_callback()
    data = load_lists()
    now = datetime.now()
    
    lines = [
        "======= ОТЧЕТ СИСТЕМЫ =======",
        "СТРОЙКА:"
    ]
    for item in data["stroyka"]:
        end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
        days_left = (end_date - now).days + 1
        lines.append(f"• {item['user_name']} — {days_left} дн.")
    if not data["stroyka"]: lines.append("Пусто")
        
    lines.append("")
    lines.append("ЛАБОРАТОРИЯ:")
    for item in data["laboratoriya"]:
        end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
        days_left = (end_date - now).days + 1
        lines.append(f"• {item['user_name']} — {days_left} дн.")
    if not data["laboratoriya"]: lines.append("Пусто")

    # Раздел 1: Только ручные ускорения игроков
    lines.append("")
    lines.append("АРХИВ ЛОГОВ УСКОРЕНИЙ:")
    buff_logs = [x for x in data.get("archive", []) if "Ускорение" in x]
    for i, x in enumerate(buff_logs):
        lines.append(f"{i+1}. {x}")
    if not buff_logs: lines.append("Пусто")

    # Скрытые разделы безопасности — доступны строго для вашего ID 368060674
    if int(user_id) == 368060674:
        # Раздел 2: Регистрации, переименования, авто-обновления и авто-удаления времени
        lines.append("")
        lines.append("======= ЖУРНАЛ СОБЫТИЙ СИСТЕМЫ =======")
        system_logs = [
            x for x in data.get("archive", []) 
            if "РЕГИСТРАЦИЯ" in x or "ПЕРЕИМЕНОВАНИЕ" in x or "АВТО-ОБНОВЛЕНИЕ" in x or "АВТО-УДАЛЕНИЕ" in x or "АДМИН-ДЕЙСТВИЕ" in x
        ]
        for i, x in enumerate(system_logs):
            lines.append(f"{i+1}. {x}")
        if not system_logs: lines.append("Пусто")

        # Раздел 3: Попытки подбора паролей, само-баффы и дубликаты
        lines.append("")
        lines.append("======= ЖУРНАЛ НАРУШЕНИЙ БЕЗОПАСНОСТИ =======")
        security_logs = [
            x for x in data.get("archive", []) 
            if "НАРУШЕНИЕ" in x or "ОШИБКА ДОСТУПА" in x
        ]
        for i, x in enumerate(security_logs):
            lines.append(f"{i+1}. {x}")
        if not security_logs: lines.append("Пусто")
        
    # Блок технической загрузки с оригинальными датами
    lines.append("")
    lines.append("======= ДЛЯ ЗАГРУЗКИ =======")
    lines.append("--- СТРОЙКА ---")
    for item in data["stroyka"]:
        lines.append(f"{item['user_name']} | {item['duration_days']} | {item['created_at']} | {item['last_updated']}")
        
    lines.append("")
    lines.append("--- ЛАБОРАТОРИЯ ---")
    for item in data["laboratoriya"]:
        lines.append(f"{item['user_name']} | {item['duration_days']} | {item['created_at']} | {item['last_updated']}")
        
    return "\n".join(lines)

def import_from_txt(content):
    """Парсит только нижнюю часть файла 'ДЛЯ ЗАГРУЗКИ', сохраняя текущих пользователей и их пароли"""
    current_data = load_lists()
    
    data = {
        "users": current_data.get("users", {}),
        "cooldowns": current_data.get("cooldowns", {}),
        "stroyka": [],
        "laboratoriya": [],
        "archive": current_data.get("archive", [])  # ФИКС: Сохраняем прошлую историю логов при импорте, а не зануляем её
    }
    
    current_section = None
    in_upload_zone = False
    
    for line in content.splitlines():
        line = line.strip()
        if not line: continue
            
        if "======= ДЛЯ ЗАГРУЗКИ =======" in line:
            in_upload_zone = True
            continue
            
        if not in_upload_zone: continue
            
        if "--- СТРОЙКА ---" in line:
            current_section = "stroyka"
            continue
        elif "--- ЛАБОРАТОРИЯ ---" in line:
            current_section = "laboratoriya"
            continue
            
        if current_section in ["stroyka", "laboratoriya"]:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 4:
                    user_name = parts[0]
                    duration_days = int(parts[1]) if parts[1].isdigit() else 90
                    created_at = parts[2]
                    last_updated = parts[3]
                    
                    cat_name_ru = "Стройку" if current_section == "stroyka" else "Лабораторию"
                    data[current_section].append({
                        "user_id": 0,  
                        "user_name": user_name,
                        "text": f"Запрос баффа на {cat_name_ru}",
                        "duration_days": duration_days,
                        "created_at": created_at,    
                        "last_updated": last_updated  
                    })
            else:
                if " " in line:
                    parts = line.rsplit(" ", 1)
                    user_name = parts[0].strip()
                    duration_str = parts[1].strip()
                    
                    if duration_str.isdigit():
                        duration_days = int(duration_str)
                        now_str = datetime.now().isoformat()
                        cat_name_ru = "Стройку" if current_section == "stroyka" else "Лабораторию"
                        data[current_section].append({
                            "user_id": 0,  
                            "user_name": user_name,
                            "text": f"Запрос баффа на {cat_name_ru}",
                            "duration_days": duration_days,
                            "created_at": now_str,
                            "last_updated": now_str
                        })
                    
    save_lists(data)
