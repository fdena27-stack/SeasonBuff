import streamlit as st
from datetime import datetime, timedelta
import storage
import logic
import backup

# Настройка страницы сайта
st.set_page_config(page_title="SeasonBuff_bot Web", layout="centered")

# Безопасный триггер сессии для очистки при первом входе
if "initialized" not in st.session_state:
    logic.clean_expired_buffs()
    st.session_state["initialized"] = True

# Инициализация переменных авторизации в сессии
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_id" not in st.session_state:
    st.session_state["user_id"] = 0
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

data = storage.load_lists()

st.title("SeasonBuff_bot - Панель управления")

# КНОПКА АКТУАЛИЗАЦИИ: обновляет данные без сброса авторизации
if st.button("Обновить списки"):
    logic.clean_expired_buffs()
    st.success("Данные успешно синхронизированы!")
    st.rerun()

# --- БЛОК 1: ВЕБ-АВТОРИЗАЦИЯ С ГЕНЕРАЦИЕЙ ID ---
st.subheader("Авторизация")

if not st.session_state["logged_in"]:
    input_user = st.text_input("Ведите ваш Ник персонажа:").strip()
    input_pass = st.text_input("Введите пароль:", type="password").strip()
    
    if st.button("Войти / Зарегистрироваться"):
        if len(input_user) < 2 or len(input_pass) < 4:
            st.error("Ошибка: Ник должен быть от 2 символов, пароль от 4 символов!")
        else:
            result = logic.verify_or_register_user(input_user, input_pass)
            
            if result in ["reg_success", "auth_success"]:
                generated_id = logic.generate_web_user_id(input_user, input_pass)
                
                if input_user.lower() == "fda2876" or generated_id == 368060674:
                    st.session_state["user_id"] = 368060674
                    st.session_state["username"] = "FDA2876"
                    st.session_state["is_admin"] = True
                    st.success("Успешный вход! Вы авторизованы как Администратор.")
                else:
                    st.session_state["user_id"] = generated_id
                    st.session_state["username"] = input_user
                    st.session_state["is_admin"] = False
                    st.success(f"Успешный вход! С возвращением, {input_user} (Ваш ID: {generated_id}).")
                
                st.session_state["logged_in"] = True
                st.rerun()
            elif result == "wrong_password":
                st.error("Ошибка: Данный ник зарезервирован! Введен неверный пароль.")
else:
    col_user, col_logout = st.columns(2)
    with col_user:
        if st.session_state["is_admin"]:
            st.success(f"Администратор: {st.session_state['username']} (ID: {st.session_state['user_id']})")
        else:
            st.success(f"Персонаж: {st.session_state['username']} (ID: {st.session_state['user_id']})")
    with col_logout:
        if st.button("Выйти"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["user_id"] = 0
            st.session_state["is_admin"] = False
            st.rerun()

current_user_name = st.session_state["username"]
current_user_id = st.session_state["user_id"]
is_admin_mode = st.session_state["is_admin"]

# --- БЛОК 2: АКТУАЛЬНЫЙ СПИСОК БАФФОВ ---
st.write("---")
st.subheader("Актуальный список")

now = datetime.now()
col1, col2 = st.columns(2)

with col1:
    st.markdown("### СТРОЙКА")
    if data["stroyka"]:
        for item in data["stroyka"]:
            end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
            days_left = (end_date - now).days + 1
            st.write(f"• **{item['user_name']}** — {days_left} дн.")
    else:
        st.write("*Пусто*")

with col2:
    st.markdown("### ЛАБОРАТОРИЯ")
    if data["laboratoriya"]:
        for item in data["laboratoriya"]:
            end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
            days_left = (end_date - now).days + 1
            st.write(f"• **{item['user_name']}** — {days_left} дн.")
    else:
        st.write("*Пусто*")
# --- БЛОК 3: ДЕЙСТВИЯ С ЗАПРОСАМИ ---
if st.session_state["logged_in"] and current_user_name:
    st.write("---")
    st.subheader("Управление запросами")
    
    tab1, col_action_sep, tab2 = st.tabs(["Создать / Удалить запрос", " ", "Дать бафф (Ускорение)"])
    
    with tab1:
        cat_choice = st.radio("Выберите категорию:", ["Стройка", "Лаборатория"], key="add_del_radio")
        category_key = "stroyka" if cat_choice == "Стройка" else "laboratoriya"
        
        has_active_request = False
        for item in data[category_key]:
            if item["user_id"] == current_user_id or item["user_name"].lower().strip() == current_user_name.lower().strip():
                has_active_request = True
                break
                
        if not has_active_request:
            st.write("**Создать запрос:**")
            duration_input = st.number_input("Введите срок действия баффа в днях (строго больше 7):", min_value=1, value=90, step=1)
            if st.button("Создать запрос"):
                success = logic.add_buff_request(category_key, current_user_id, current_user_name, f"Запрос баффа на {cat_choice}", duration_input)
                if success:
                    st.success("Запрос успешно добавлен!")
                    st.rerun()
                else:
                    st.error("Ошибка: Срок должен быть строго больше 7 дней!")
        else:
            st.write("**У вас есть активный запрос в этой категории:**")
            if st.button("Удалить мой запрос"):
                removed = logic.remove_user_buff(category_key, current_user_id)
                if removed:
                    st.success("Ваш запрос успешно удален!")
                    st.rerun()
                else:
                    st.error("Ошибка удаления.")

    with tab2:
        st.write("**Какой бафф вы хотите выдать?**")
        give_cat_choice = st.radio("Выберите категорию для выдачи:", ["Стройка", "Лаборатория"], key="give_radio")
        give_category_key = "stroyka" if give_cat_choice == "Стройка" else "laboratoriya"
        
        active_items = data[give_category_key]
        
        if not active_items:
            st.info(f"В категории {give_cat_choice} сейчас нет active-запросов.")
        else:
            options = []
            for idx, item in enumerate(active_items):
                end_date = datetime.fromisoformat(item["created_at"]) + timedelta(days=item["duration_days"])
                days_left = (end_date - now).days + 1
                options.append(f"{item['user_name']} ({days_left} дн.)")
                
            selected_target = st.selectbox("Кому выдать бафф?", options=options)
            selected_index = options.index(selected_target)
            
            percent_choice = st.selectbox("На сколько ускорить?", options=["5%", "10%", "15%"])
            
            if st.button("Применить ускорение"):
                buff_result = logic.process_give_buff(give_category_key, selected_index, percent_choice, current_user_id, current_user_name)
                if buff_result:
                    st.success(f"Результат: {buff_result}")
                    st.rerun()
                else:
                    st.error("Ошибка проведения ускорения.")

# --- БЛОК 4: АДМИНИСТРИРОВАНИЕ И БЭКАПЫ (ДЛЯ АДМИНА) ---
st.write("---")
st.subheader("Административный раздел")

fake_admin_id = 368060674 if is_admin_mode else 0
txt_content = backup.export_to_txt(logic.clean_expired_buffs, fake_admin_id)

st.download_button(
    label="Выгрузить базу в .TXT",
    data=txt_content,
    file_name="database.txt",
    mime="text/plain"
)

if is_admin_mode:
    st.write("---")
    st.write("**Управление аккаунтами пользователей:**")
    
    user_list = list(data["users"].keys())
    if "FDA2876" in user_list: user_list.remove("FDA2876")
    
    if not user_list:
        st.info("В системе пока нет других зарегистрированных пользователей.")
    else:
        selected_user = st.selectbox("Выберите пользователя для изменения пароля:", options=user_list)
        new_pass_input = st.text_input("Введите новый пароль для этого пользователя:", type="password", key="admin_new_pass").strip()
        
        if st.button("Обновить пароль пользователя"):
            if len(new_pass_input) < 4:
                st.error("Ошибка: Пароль должен быть не короче 4 символов!")
            else:
                success_reset = logic.admin_reset_user_password(selected_user, new_pass_input)
                if success_reset:
                    st.success(f"Пароль для пользователя [{selected_user}] успешно изменен!")
                    st.rerun()
                else:
                    st.error("Не удалось сменить пароль.")
                    
    st.write("---")
    st.write("**Загрузка базы данных:**")
    uploaded_file = st.file_uploader("Пожалуйста, отправьте мне файл .TXT для импорта:", type=["txt"])
    if uploaded_file is not None:
        string_data = uploaded_file.read().decode("utf-8")
        try:
            backup.import_from_txt(string_data)
            st.success("Данные успешно импортированы! Пожалуйста, перезайдите в систему.")
            st.session_state["logged_in"] = False
            st.rerun()
        except Exception:
            st.error("Ошибка при разборе файла бэкапа.")
else:
    if st.button("Загрузка в .TXT (Техническая зона)"):
        st.error("What раздел на реконструкции, архитектор забухал, бюджет кончился!")
