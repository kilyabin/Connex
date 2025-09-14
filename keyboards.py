# keyboards.py

import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from localization import get_text

USERS_PER_PAGE = 5

# --- ОСНОВНЫЕ КЛАВИАТУРЫ ---

def get_main_keyboard_by_role(is_admin: bool, lang: str) -> InlineKeyboardMarkup:
    """Возвращает админскую или пользовательскую клавиатуру на нужном языке."""
    buttons = []
    if is_admin:
        buttons = [
            [InlineKeyboardButton(text=get_text('manage_users_btn', lang), callback_data="admin_users_page_0")],
            [InlineKeyboardButton(text=get_text('manage_configs_btn', lang), callback_data="admin_configs_page_0")],
            [InlineKeyboardButton(text=get_text('manage_tutorials_btn', lang), callback_data="admin_tutorials_menu")],
            [InlineKeyboardButton(text=get_text('mass_send_btn', lang), callback_data="mass_send_start")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text=get_text('my_configs_btn', lang), callback_data="user_configs")],
            [InlineKeyboardButton(text=get_text('help_btn', lang), callback_data="user_help")]
        ]
    # Добавляем кнопку настроек для всех
    buttons.append([InlineKeyboardButton(text=get_text('settings', lang), callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('back_to_menu', lang), callback_data="admin_menu")]
    ])

# --- НАСТРОЙКИ ЯЗЫКА ---

def get_language_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="set_lang_en")],
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="set_lang_ru")]
    ])

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ---

def get_users_keyboard(page: int, lang: str) -> InlineKeyboardMarkup:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
    total_users = cursor.fetchone()[0]
    offset = page * USERS_PER_PAGE
    cursor.execute("SELECT telegram_id, username FROM users WHERE is_admin = 0 LIMIT ? OFFSET ?", (USERS_PER_PAGE, offset))
    users = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for user_id, username in users:
        button_text = f"@{username}" if username else f"ID: {user_id}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"manage_user_{user_id}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text=get_text('prev_btn', lang), callback_data=f"admin_users_page_{page-1}"))
    if (page + 1) * USERS_PER_PAGE < total_users:
        nav_buttons.append(InlineKeyboardButton(text=get_text('next_btn', lang), callback_data=f"admin_users_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
        
    keyboard.append([InlineKeyboardButton(text=get_text('add_user_btn', lang), callback_data="add_user")])
    keyboard.append([InlineKeyboardButton(text=get_text('back_to_menu', lang), callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def user_management_keyboard(user_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('delete_user_btn', lang), callback_data=f"delete_user_{user_id}")],
        [InlineKeyboardButton(text=get_text('back_to_list_btn', lang), callback_data="admin_users_page_0")]
    ])

# --- УПРАВЛЕНИЕ КОНФИГУРАЦИЯМИ ---

def get_users_for_configs_keyboard(page: int, lang: str) -> InlineKeyboardMarkup:
    # Эта функция дублирует get_users_keyboard, но с другими callback_data
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
    total_users = cursor.fetchone()[0]
    offset = page * USERS_PER_PAGE
    cursor.execute("SELECT telegram_id, username FROM users WHERE is_admin = 0 LIMIT ? OFFSET ?", (USERS_PER_PAGE, offset))
    users = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for user_id, username in users:
        button_text = f"@{username}" if username else f"ID: {user_id}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"user_configs_manage_{user_id}")])
        
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text=get_text('prev_btn', lang), callback_data=f"admin_configs_page_{page-1}"))
    if (page + 1) * USERS_PER_PAGE < total_users:
        nav_buttons.append(InlineKeyboardButton(text=get_text('next_btn', lang), callback_data=f"admin_configs_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
        
    keyboard.append([InlineKeyboardButton(text=get_text('back_to_menu', lang), callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_user_configs_management_keyboard(user_id: int, lang: str) -> InlineKeyboardMarkup:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, config_type, config_data FROM configs WHERE user_id = ?", (user_id,))
    configs = cursor.fetchall()
    conn.close()

    keyboard = []
    for config_id, config_type, config_data in configs:
        if config_type.startswith("file:"):
            display_text = f"{get_text('file_prefix', lang)}: {config_type.split(':', 1)[1]}"
        else:
            short_data = config_data[:20] + '...' if len(config_data) > 20 else config_data
            display_text = f"{config_type}: {short_data}"
        
        button_text = f"{get_text('delete_config_prefix', lang)} {display_text}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"delete_config:{config_id}:{user_id}")])
    
    keyboard.append([InlineKeyboardButton(text=get_text('add_config_btn', lang), callback_data=f"add_config_{user_id}")])
    keyboard.append([InlineKeyboardButton(text=get_text('back_to_users_list_btn', lang), callback_data="admin_configs_page_0")])
    keyboard.append([InlineKeyboardButton(text=get_text('main_menu', lang), callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- УПРАВЛЕНИЕ ТУТОРИАЛАМИ ---

def get_tutorials_admin_keyboard(lang: str) -> InlineKeyboardMarkup:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM tutorials")
    tutorials = cursor.fetchall()
    conn.close()

    keyboard = []
    for tutorial_id, title in tutorials:
        keyboard.append([InlineKeyboardButton(text=f"{get_text('delete_tutorial_prefix', lang)} {title}", callback_data=f"delete_tutorial_{tutorial_id}")])
    
    keyboard.append([InlineKeyboardButton(text=get_text('add_tutorial_btn', lang), callback_data="add_tutorial")])
    keyboard.append([InlineKeyboardButton(text=get_text('back_to_menu', lang), callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_tutorials_user_keyboard(lang: str) -> InlineKeyboardMarkup:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM tutorials")
    tutorials = cursor.fetchall()
    conn.close()

    keyboard = []
    if not tutorials:
        keyboard.append([InlineKeyboardButton(text=get_text('no_tutorials_yet', lang), callback_data="no_op")])
    else:
        for tutorial_id, title in tutorials:
            keyboard.append([InlineKeyboardButton(text=f"📖 {title}", callback_data=f"view_tutorial_{tutorial_id}")])
            
    # Добавляем кнопку "Назад", которая вернет пользователя в главное меню
    # Для этого нам нужна информация о его роли
    # Проще всего будет, если обработчик этой кнопки сам вернет главное меню
    # Поэтому здесь просто ставим callback_data, который поймает user_handler
    keyboard.append([InlineKeyboardButton(text=get_text('back_to_menu', 'ru' if lang=='ru' else 'en'), callback_data="user_main_menu")])


    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- РАССЫЛКА И ПРОЧЕЕ ---

def get_confirm_send_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('send_btn', lang), callback_data="send_confirmed")],
        [InlineKeyboardButton(text=get_text('cancel_btn', lang), callback_data="send_cancelled")]
    ])

def get_skip_media_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('skip_btn', lang), callback_data="skip_media")]
    ])
