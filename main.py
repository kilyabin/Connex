# main.py

import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

# --- Import local modules ---
from keyboards import get_main_keyboard_by_role
from handlers import admin_handlers, user_handlers, settings_handlers # Import new settings handler
from localization import get_text

# --- Settings ---
BOT_TOKEN = "YOUR_BOT_TOKEN" 
ADMIN_IDS = [YOUR_TELEGRAM_ID] 

# --- Initialization ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Database Initialization ---
def init_db():
    """Initializes the database and tables."""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create users table with a new language_code column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        is_admin INTEGER DEFAULT 0,
        language_code TEXT DEFAULT 'en'
    )''')
    
    # Create configs table with ON DELETE CASCADE
    # This automatically deletes a user's configs when the user is deleted
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        config_type TEXT,
        config_data TEXT,
        FOREIGN KEY (user_id) REFERENCES users (telegram_id) ON DELETE CASCADE
    )''')

    # Create tutorials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tutorials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content_text TEXT,
        file_id TEXT
    )''')

    # Add/update admins from the ADMIN_IDS list
    for admin_id in ADMIN_IDS:
        cursor.execute(
            "INSERT INTO users (telegram_id, is_admin, language_code) VALUES (?, 1, 'en') "
            "ON CONFLICT(telegram_id) DO UPDATE SET is_admin = 1",
            (admin_id,)
        )

    conn.commit()
    conn.close()

# --- Register Routers ---
dp.include_router(admin_handlers.router)
dp.include_router(user_handlers.router)
dp.include_router(settings_handlers.router) # Register the new settings router

# --- /start Command Handler ---
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    Handles the /start command.
    Greets the user, adds them to the DB if they are new,
    and shows the appropriate menu in their selected language.
    """
    user_id = message.from_user.id
    username = message.from_user.username
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT is_admin, language_code FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        # User exists, get their role and language
        is_admin, lang = result
    else:
        # New user, add to DB with default language 'en'
        is_admin = 1 if user_id in ADMIN_IDS else 0
        lang = 'en'
        cursor.execute(
            "INSERT INTO users (telegram_id, username, is_admin, language_code) VALUES (?, ?, ?, ?)",
            (user_id, username, is_admin, lang)
        )
        conn.commit()
        
    conn.close()

    # Determine the welcome text based on role and language
    welcome_text_key = 'welcome_admin' if is_admin else 'welcome'
    welcome_text = get_text(welcome_text_key, lang)
    
    # Show the main menu
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard_by_role(is_admin, lang)
    )

# --- Entry Point ---
async def main():
    """Main function to start the bot."""
    logging.basicConfig(level=logging.INFO)
    init_db() # Initialize the database on startup
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
