💧 "Lesnoy Istochnik" — Water Delivery Bot

This Telegram bot streamlines water delivery management. It provides a conversational interface for clients to place new orders or repeat past ones, while providing managers with a centralized dashboard in Google Sheets and real-time order notifications.

✨ Key Features
Order Automation: A user-friendly, state-driven (FSM) flow for collecting delivery details.
Google Sheets Integration: Automatically logs all orders into a cloud-based spreadsheet for accounting and tracking.
Quick Reorder: Allows returning customers to repeat their last order in a single click.
Manager Dashboard: Management receives detailed Telegram notifications for new orders and can assign delivery dates using a specific command (/assign_delivery_date).
Automated Updates: Clients are automatically notified via Telegram once their delivery date has been assigned.

🛠 Technologies
Python 3.9+
Aiogram 2.x: Asynchronous Telegram Bot API framework.
Gspread: Google Sheets API integration.
Python-dotenv: Secure configuration management.

🚀 Setup & Deployment
1. Installation
Clone the repository and install the dependencies:

pip install -r requirements.txt

2. Configuration (Secure)
Create a .env file in the root directory to store your sensitive keys. Do not commit this file to GitHub.

BOT_TOKEN=your_bot_token_here
MANAGER_ID=your_telegram_id_here
Create a config.py file to handle your settings securely:

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_ID = os.getenv("MANAGER_ID")
MANAGER_PHONE = "+79260148460"
MANAGER_USERNAME = "@dostavkavody01"
SHEET_NAME = "LesnoyIstochnikOrders"

3. Google Sheets Setup
Create a Service Account via Google Cloud Console.
Download the credentials.json file and place it in the project root.
Share your target Google Sheet with the email address found inside credentials.json (the client_email).

4. Running the Bot

python bot.py

📋 Spreadsheet Structure
The bot expects the following columns in the first sheet of your Google Spreadsheet:
Timestamp
Client Type
Address
Bottle Count
Unit Price
Total
Phone Number
Comment
Delivery Date
Confirmation Status
Telegram User ID

Developed for efficient water delivery operations.
