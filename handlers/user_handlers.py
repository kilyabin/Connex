# handlers/user_handlers.py

import sqlite3
from aiogram import Router, F, types, Bot
from keyboards import get_main_keyboard_by_role, get_tutorials_user_keyboard
from localization import get_text

router = Router()

# Вспомогательная функция для получения языка пользователя
def get_user_lang(user_id: int) -> str:
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language_code FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'en'

# Новый обработчик для кнопки "Назад в меню" из раздела помощи
@router.callback_query(F.data == "user_main_menu")
async def process_back_to_main_menu(callback: types.CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('welcome', lang),
        reply_markup=get_main_keyboard_by_role(is_admin=False, lang=lang)
    )
    await callback.answer()

@router.callback_query(F.data == "user_configs")
async def process_user_configs(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT config_type, config_data FROM configs WHERE user_id = ?", (user_id,))
    user_configs = cursor.fetchall()
    conn.close()

    if not user_configs:
        await callback.message.answer(get_text('no_configs_yet', lang))
    else:
        await callback.message.answer(get_text('your_configs', lang))
        for config_type, config_data in user_configs:
            if config_type.startswith("file:"):
                file_id = config_data
                caption = f"{get_text('config_type', lang)}: {config_type.split(':', 1)[1]}"
                await bot.send_document(chat_id=user_id, document=file_id, caption=caption)
            else:
                await callback.message.answer(f"{get_text('config_type', lang)}: `{config_type}`\n\n`{config_data}`", parse_mode="Markdown")
    
    await callback.message.answer(
        get_text('next_action', lang),
        reply_markup=get_main_keyboard_by_role(is_admin=False, lang=lang)
    )
    await callback.answer()

@router.callback_query(F.data == "user_help")
async def process_user_help(callback: types.CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    await callback.message.edit_text(
        get_text('choose_tutorial', lang),
        reply_markup=get_tutorials_user_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_tutorial_"))
async def process_view_tutorial(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    tutorial_id = int(callback.data.split("_")[-1])
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT content_text, file_id FROM tutorials WHERE id = ?", (tutorial_id,))
    tutorial = cursor.fetchone()
    conn.close()

    if tutorial:
        content_text, file_id = tutorial
        # Сначала удаляем предыдущее сообщение с кнопками
        await callback.message.delete()
        if file_id:
            try:
                await bot.send_photo(chat_id=user_id, photo=file_id, caption=content_text)
            except:
                await bot.send_video(chat_id=user_id, video=file_id, caption=content_text)
        else:
            await callback.message.answer(content_text)
        
        await callback.message.answer(
            get_text('next_action', lang),
            reply_markup=get_main_keyboard_by_role(is_admin=False, lang=lang)
        )
    else:
        await callback.answer(get_text('error_not_found', lang), show_alert=True)
    
    await callback.answer()
