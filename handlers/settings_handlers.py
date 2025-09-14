# handlers/settings_handlers.py

import sqlite3
from aiogram import Router, F, types

from keyboards import get_language_choice_keyboard, get_main_keyboard_by_role
from localization import get_text

router = Router()

@router.callback_query(F.data == "settings")
async def process_settings(callback: types.CallbackQuery):
    # Получаем язык пользователя для корректного отображения меню
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language_code FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    lang = cursor.fetchone()[0]
    conn.close()

    await callback.message.edit_text(
        get_text('choose_language', lang),
        reply_markup=get_language_choice_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_lang_"))
async def process_set_language(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language_code = ? WHERE telegram_id = ?", (lang_code, user_id))
    cursor.execute("SELECT is_admin FROM users WHERE telegram_id = ?", (user_id,))
    is_admin = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    await callback.message.edit_text(get_text('language_changed', lang_code))
    
    # Показываем главное меню на новом языке
    main_menu_text = get_text('welcome_admin' if is_admin else 'welcome', lang_code)
    await callback.message.answer(
        main_menu_text,
        reply_markup=get_main_keyboard_by_role(is_admin, lang_code)
    )
    await callback.answer()
