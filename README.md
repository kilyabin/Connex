# Connex
A Telegram bot that eases sharing VPN configurations with users

### How to get started

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    ```
2.  **Activate the virtual environment:**
    * **On macOS / Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **On Windows:**
        ```bash
        venv\Scripts\activate
        ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the bot:**
    ```bash
    python3 main.py
    ```
5.  **For convenience, you can create a systemd service to run the bot in the background.**

## Key Features
- Admin panel for managing users and configurations.
- Add and edit tutorials for users to help them understand how to use client applications.
- Send notifications to all bot users
## Tech Stack
- **Programming language:** Python
- **Database:** SQLite

## Dependencies
- **aiogram** — for interacting with the Telegram API.
- **aiosqlite3** — for database operations.
- **asyncio**
