from datetime import datetime, timedelta
from storage import load_lists, save_lists

def export_to_txt(clean_callback, user_id):
    """Генерирует расширенное содержимое файла. Журналы системы и нарушений доступны ТОЛЬКО для ID 368060674"""
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

    lines.append("")
    lines.append("АРХИВ ЛОГОВ УСКОРЕНИЙ:")
    buff_logs = [x for x in data.get("archive", []) if "Ускорение" in x]
    for i, x in enumerate(buff_logs):
        lines.append(f"{i+1}. {x}")
    if not buff_logs: lines.append("Пусто")

    # ФИКС: Эти два журнала добавляются в файл только для администратора с ID 368060674
    if int(user_id) == 368060674:
        lines.append("")
        lines.append("======= ЖУРНАЛ СОБЫТИЙ СИСТЕМЫ =======")
        system_logs = [x for x in data.get("archive", []) if "РЕГИСТРАЦИЯ" in x or "ПЕРЕИМЕНОВАНИЕ" in x]
        for i, x in enumerate(system_logs):
            lines.append(f"{i+1}. {x}")
        if not system_logs: lines.append("Пусто")

        lines.append("")
        lines.append("======= ЖУРНАЛ НАРУШЕНИЙ БЕЗОПАСНОСТИ =======")
        security_logs = [x for x in data.get("archive", []) if "НАРУШЕНИЕ" in x]
        for i, x in enumerate(security_logs):
            lines.append(f"{i+1}. {x}")
        if not security_logs: lines.append("Пусто")
        
    lines.append("")
    lines.append("======= ДЛЯ ЗАГРУЗКИ =======")
    lines.append("--- СТРОЙКА ---")
    for item in data["stroyka"]:
        end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
        days_left = (end_date - now).days + 1
        lines.append(f"{item['user_name']} {days_left}")
        
    lines.append("")
    lines.append("--- ЛАБОРАТОРИЯ ---")
    for item in data["laboratoriya"]:
        end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
        days_left = (end_date - now).days + 1
        lines.append(f"{item['user_name']} {days_left}")
        
    return "\n".join(lines)

def import_from_txt(content):
    data = {"users": {}, "stroyka": [], "laboratoriya": [], "archive": []}
    current_section = None
    in_upload_zone = False
    now_str = datetime.now().isoformat()
    
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
            if " " in line:
                parts = line.rsplit(" ", 1)
                user_name = parts[0].strip()
                duration_str = parts[1].strip()
                
                if duration_str.isdigit():
                    duration_days = int(duration_str)
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

