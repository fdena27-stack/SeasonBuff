def export_to_txt(data):
    """Превращает JSON-данные в читаемый текст"""
    lines = []
    
    for category in ["stroyka", "laboratoriya"]:
        # Создаем заголовок секции в файле
        lines.append(f"=== {category.upper()} ===") 
        
        for item in data.get(category, []):
            # Записываем данные игрока через разделитель |
            line = f"{item['user_name']} | {item['duration_days']} | {item['created_at']} | {item['last_updated']}"
            lines.append(line)
            
        lines.append("") # Пустая строка для разделения секций
        
    return "\n".join(lines)
