# handlers/admin_handlers.py

import sqlite3
import asyncio
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError

from keyboards import (
    get_main_keyboard_by_role, get_users_keyboard, user_management_keyboard,
    get_users_for_configs_keyboard, get_user_configs_management_keyboard,
    get_tutorials_admin_keyboard, get_skip_media_keyboard, get_confirm_send_keyboard
)
from localization import get_text

router = Router()

# --- Helper function to get admin's language ---
def get_admin_lang(user_id: int) -> str:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language_code FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'en'

# --- FSM States ---
class AdminStates(StatesGroup):
    add_user_id = State()
    add_config_type = State()
    add_config_data = State()
    add_tutorial_title = State()
    add_tutorial_text = State()
    add_tutorial_media = State()
    mass_send_message = State()
    mass_send_confirm = State()

# --- Main Menu Handler ---
@router.callback_query(F.data == "admin_menu")
async def process_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear() # Clear any active state
    lang = get_admin_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('welcome_admin', lang),
        reply_markup=get_main_keyboard_by_role(is_admin=True, lang=lang)
    )
    await callback.answer()

# --- User Management Section ---

@router.callback_query(F.data.startswith("admin_users_page_"))
async def process_users_list(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('users_list', lang),
        reply_markup=get_users_keyboard(page, lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("manage_user_"))
async def process_manage_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    username = user[0] if user and user[0] else "N/A"
    
    text = get_text('manage_user_title', lang).format(user_id=user_id, username=username)
    await callback.message.edit_text(
        text,
        reply_markup=user_management_keyboard(user_id, lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_user_"))
async def process_delete_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
    # Configs will be deleted automatically due to "ON DELETE CASCADE" in the new DB schema
    conn.commit()
    conn.close()

    await callback.answer(get_text('user_deleted_ok', lang))
    await callback.message.edit_text(
        get_text('users_list', lang),
        reply_markup=get_users_keyboard(0, lang)
    )

@router.callback_query(F.data == "add_user")
async def process_add_user_start(callback: types.CallbackQuery, state: FSMContext):
    lang = get_admin_lang(callback.from_user.id)
    await callback.message.edit_text(get_text('ask_for_user_id', lang))
    await state.set_state(AdminStates.add_user_id)
    await callback.answer()

@router.message(AdminStates.add_user_id)
async def process_add_user_id(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    try:
        user_id = int(message.text)
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_id,))
        if cursor.fetchone():
            await message.answer(get_text('user_already_exists', lang))
        else:
            # Add user with default language 'en'
            cursor.execute("INSERT INTO users (telegram_id, language_code) VALUES (?, ?)", (user_id, 'en'))
            conn.commit()
            await message.answer(get_text('user_added_ok', lang))
        conn.close()
        
        await state.clear()
        await message.answer(
            get_text('users_list', lang),
            reply_markup=get_users_keyboard(0, lang)
        )
    except (ValueError, TypeError):
        await message.answer(get_text('invalid_id_format', lang))

# --- Config Management Section ---
# (This section is also refactored to use the lang parameter)

@router.callback_query(F.data.startswith("admin_configs_page_"))
async def process_config_users_list(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('choose_user_for_config', lang),
        reply_markup=get_users_for_configs_keyboard(page, lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("user_configs_manage_"))
async def process_user_configs_manage(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('user_configs_title', lang),
        reply_markup=get_user_configs_management_keyboard(user_id, lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_config:"))
async def process_delete_config(callback: types.CallbackQuery):
    _, config_id, user_id = callback.data.split(":")
    config_id, user_id = int(config_id), int(user_id)
    lang = get_admin_lang(callback.from_user.id)
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM configs WHERE id = ?", (config_id,))
    conn.commit()
    conn.close()

    await callback.answer(get_text('config_deleted_ok', lang))
    await callback.message.edit_text(
        get_text('user_configs_title', lang),
        reply_markup=get_user_configs_management_keyboard(user_id, lang)
    )

# ... (Add Config FSM flow refactored for localization)
@router.callback_query(F.data.startswith("add_config_"))
async def process_add_config_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    await state.update_data(current_user_id=user_id)
    await state.set_state(AdminStates.add_config_type)
    await callback.message.edit_text(get_text('add_config_step1', lang))
    await callback.answer()

@router.message(AdminStates.add_config_type)
async def process_add_config_type(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    await state.update_data(config_type=message.text)
    await state.set_state(AdminStates.add_config_data)
    await message.answer(get_text('add_config_step2', lang))

@router.message(AdminStates.add_config_data, F.content_type.in_({ContentType.TEXT, ContentType.DOCUMENT}))
async def process_add_config_data(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    data = await state.get_data()
    user_id = data['current_user_id']
    
    # ... (logic for handling file/text remains the same)
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        config_type = f"file:{file_name}"
        config_data = file_id
    else:
        config_type = data['config_type']
        config_data = message.text

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO configs (user_id, config_type, config_data) VALUES (?, ?, ?)",
                   (user_id, config_type, config_data))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(get_text('config_added_ok', lang))
    await message.answer(
        get_text('user_configs_title', lang),
        reply_markup=get_user_configs_management_keyboard(user_id, lang)
    )

# --- Tutorial Management Section ---
@router.callback_query(F.data == "admin_tutorials_menu")
async def process_tutorials_menu(callback: types.CallbackQuery):
    lang = get_admin_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('tutorials_menu_title', lang),
        reply_markup=get_tutorials_admin_keyboard(lang)
    )
    await callback.answer()
# ... (rest of the tutorial management refactored similarly)

@router.callback_query(F.data.startswith("delete_tutorial_"))
async def process_delete_tutorial(callback: types.CallbackQuery):
    tutorial_id = int(callback.data.split("_")[-1])
    lang = get_admin_lang(callback.from_user.id)
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tutorials WHERE id = ?", (tutorial_id,))
    conn.commit()
    conn.close()
    await callback.answer(get_text('tutorial_deleted_ok', lang))
    await callback.message.edit_text(
        get_text('tutorials_menu_title', lang),
        reply_markup=get_tutorials_admin_keyboard(lang)
    )

@router.callback_query(F.data == "add_tutorial")
async def process_add_tutorial_start(callback: types.CallbackQuery, state: FSMContext):
    lang = get_admin_lang(callback.from_user.id)
    await state.set_state(AdminStates.add_tutorial_title)
    await callback.message.edit_text(get_text('add_tutorial_step1', lang))
    await callback.answer()

@router.message(AdminStates.add_tutorial_title)
async def process_add_tutorial_title(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    await state.update_data(title=message.text)
    await state.set_state(AdminStates.add_tutorial_text)
    await message.answer(get_text('add_tutorial_step2', lang))

@router.message(AdminStates.add_tutorial_text)
async def process_add_tutorial_text(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    await state.update_data(text=message.text)
    await state.set_state(AdminStates.add_tutorial_media)
    await message.answer(
        get_text('add_tutorial_step3', lang),
        reply_markup=get_skip_media_keyboard(lang)
    )

@router.callback_query(F.data == "skip_media", AdminStates.add_tutorial_media)
async def process_skip_media(callback: types.CallbackQuery, state: FSMContext):
    lang = get_admin_lang(callback.from_user.id)
    data = await state.get_data()
    # ... (DB logic is the same)
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tutorials (title, content_text) VALUES (?, ?)", (data['title'], data['text']))
    conn.commit()
    conn.close()
    await state.clear()
    await callback.message.edit_text(get_text('tutorial_added_ok_no_media', lang))
    await callback.message.answer(
        get_text('tutorials_menu_title', lang),
        reply_markup=get_tutorials_admin_keyboard(lang)
    )
    await callback.answer()

@router.message(AdminStates.add_tutorial_media, F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}))
async def process_add_tutorial_media(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    # ... (DB and file_id logic is the same)
    file_id = ""
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
    data = await state.get_data()
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tutorials (title, content_text, file_id) VALUES (?, ?, ?)",
                   (data['title'], data['text'], file_id))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer(get_text('tutorial_added_ok_with_media', lang))
    await message.answer(
        get_text('tutorials_menu_title', lang),
        reply_markup=get_tutorials_admin_keyboard(lang)
    )

# --- Mass Messaging Section ---
@router.callback_query(F.data == "mass_send_start")
async def process_mass_send_start(callback: types.CallbackQuery, state: FSMContext):
    lang = get_admin_lang(callback.from_user.id)
    await state.set_state(AdminStates.mass_send_message)
    await callback.message.edit_text(get_text('mass_send_ask_message', lang))
    await callback.answer()

@router.message(AdminStates.mass_send_message)
async def process_mass_send_message(message: types.Message, state: FSMContext):
    lang = get_admin_lang(message.from_user.id)
    await state.update_data(message_to_send=message)
    await state.set_state(AdminStates.mass_send_confirm)
    await message.answer(
        get_text('mass_send_confirm_message', lang),
        reply_markup=get_confirm_send_keyboard(lang)
    )

@router.callback_query(F.data == "send_cancelled", AdminStates.mass_send_confirm)
async def process_send_cancelled(callback: types.CallbackQuery, state: FSMContext):
    lang = get_admin_lang(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        get_text('mass_send_cancelled', lang),
        reply_markup=get_main_keyboard_by_role(is_admin=True, lang=lang)
    )
    await callback.answer()

@router.callback_query(F.data == "send_confirmed", AdminStates.mass_send_confirm)
async def process_send_confirmed(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    lang = get_admin_lang(callback.from_user.id)
    data = await state.get_data()
    message_to_send = data['message_to_send']
    await state.clear()

    await callback.message.edit_text(get_text('mass_send_started', lang), reply_markup=None)
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE is_admin = 0")
    user_ids = cursor.fetchall()
    conn.close()

    success_count = 0
    fail_count = 0
    for (user_id,) in user_ids:
        try:
            await message_to_send.copy_to(chat_id=user_id)
            success_count += 1
        except TelegramAPIError as e:
            print(f"Failed to send to {user_id}: {e}")
            fail_count += 1
        await asyncio.sleep(0.1)

    result_text = get_text('mass_send_finished', lang).format(
        success_count=success_count,
        fail_count=fail_count
    )
    await callback.message.answer(
        result_text,
        reply_markup=get_main_keyboard_by_role(is_admin=True, lang=lang)
    )
