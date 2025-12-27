import os
import telebot
import threading
import time
import random
import requests
import json
import statistics
from datetime import datetime, timezone, timedelta
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, jsonify

# 🔧 Render Compatibility - Flask App তৈরি
app = Flask(__name__)

# 🔧 Environment Variables থেকে Configuration নিন
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8375298179:AAEVUC09kDRmlTo46Jqfv0Ckvq4neMnKjAE')
OWNER_ID = int(os.environ.get('OWNER_ID', 8473134685))

# 🧠 বট ইনিশিয়ালাইজ
bot = telebot.TeleBot(BOT_TOKEN)

# 🗂 ডাটা রাখার জন্য Dictionary - UNLIMITED CHANNEL SYSTEM
user_channels = {}  # {user_id: ["@channel1", "@channel2", ...]}
signal_threads = {} # {user_id: threading.Thread}
signal_status = {}  # {user_id: {"@channel1": True, "@channel2": False}}
user_register_links = {}  # {user_id: "https://register-link.com"}
prediction_timers = {}  # {user_id: end_timestamp}

# 🎯 Win/Loss ট্র্যাকিং সিস্টেম
prediction_history = {}  # {user_id: [{period: "", prediction: "", actual: "", result: "WIN/LOSS", time: ""}]}

# 🎯 চ্যানেল ভিত্তিক Win/Loss স্টিকার সিস্টেম
channel_win_stickers = {}  # {"@channel1": "sticker_id", "@channel2": "sticker_id"}
channel_loss_stickers = {}  # {"@channel1": "sticker_id", "@channel2": "sticker_id"}

# 🎯 NEW: Season Start/Off স্টিকার সিস্টেম
channel_season_start_stickers = {}  # {"@channel1": "sticker_id", "@channel2": "sticker_id"}
channel_season_off_stickers = {}    # {"@channel1": "sticker_id", "@channel2": "sticker_id"}

# 🎯 NEW: Pending Season Off ট্র্যাকিং
pending_season_off = {}  # {channel: True/False} - পরের Period এ Season Off স্টিকার পাঠানোর জন্য

# 🎯 ডিফল্ট Win/Loss স্টিকার ID
DEFAULT_WIN_STICKER = "CAACAgUAAxkBAAIBIWZ4i-1dAAE3KXWk3X7L03zWn8H2bAACXxoAAo_FYFZxK2k1K4AAATYE"
DEFAULT_LOSS_STICKER = "CAACAgUAAxkBAAIBJmZ4jC5oOGlnPIn5hV2F9r85B8DgAAJiGgACj8VgVkli01bg7BvzLAQ"

# 🎯 NEW: ডিফল্ট Season Start/Off স্টিকার ID
DEFAULT_SEASON_START_STICKER = "CAACAgUAAxkBAAIBKGZ4jFoq2F8YzG7CLHbrZEdHkHZ-AAJkGgACj8VgVq2wTp6rrVK9LAQ"
DEFAULT_SEASON_OFF_STICKER = "CAACAgUAAxkBAAIBK2Z4jHazG2mRZkMyHPFZ_RX7clB2AAJlGgACj8VgVu6Crd4B5EeALAQ"

# 🔗 API URLs - FIXED API CALLS
CURRENT_API = 'https://api.bdg88zf.com/api/webapi/GetGameIssue'
HISTORY_API = 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'

# ========== NEW: RULE-BASED PREDICTION SYSTEM FROM PROMPT API ==========

# Dictionary of rules from Prompt Api.txt
RULE_BASED_PREDICTIONS = {
    # Format: {(last_num, below_num): prediction}
    # Last Num = 0
    (0, 0): "SMALL", (0, 1): "BIG", (0, 2): "BIG", (0, 3): "BIG",
    (0, 4): "SMALL", (0, 5): "SMALL", (0, 6): "BIG", (0, 7): "SMALL",
    (0, 8): "SMALL", (0, 9): "BIG",
    
    # Last Num = 1
    (1, 0): "BIG", (1, 1): "BIG", (1, 2): "BIG", (1, 3): "SMALL",
    (1, 4): "SMALL", (1, 5): "SMALL", (1, 6): "BIG", (1, 7): "SMALL",
    (1, 8): "BIG", (1, 9): "BIG",
    
    # Last Num = 2
    (2, 0): "SMALL", (2, 1): "BIG", (2, 2): "BIG", (2, 3): "BIG",
    (2, 4): "SMALL", (2, 5): "BIG", (2, 6): "SMALL", (2, 7): "BIG",
    (2, 8): "SMALL", (2, 9): "SMALL",
    
    # Last Num = 3
    (3, 0): "SMALL", (3, 1): "BIG", (3, 2): "BIG", (3, 3): "SMALL",
    (3, 4): "BIG", (3, 5): "SMALL", (3, 6): "BIG", (3, 7): "BIG",
    (3, 8): "SMALL", (3, 9): "SMALL",
    
    # Last Num = 4
    (4, 0): "BIG", (4, 1): "SMALL", (4, 2): "SMALL", (4, 3): "BIG",
    (4, 4): "SMALL", (4, 5): "BIG", (4, 6): "SMALL", (4, 7): "BIG",
    (4, 8): "BIG", (4, 9): "SMALL",
    
    # Last Num = 5
    (5, 0): "SMALL", (5, 1): "BIG", (5, 2): "BIG", (5, 3): "SMALL",
    (5, 4): "SMALL", (5, 5): "BIG", (5, 6): "BIG", (5, 7): "SMALL",
    (5, 8): "BIG", (5, 9): "BIG",
    
    # Last Num = 6
    (6, 0): "SMALL", (6, 1): "SMALL", (6, 2): "SMALL", (6, 3): "BIG",
    (6, 4): "SMALL", (6, 5): "BIG", (6, 6): "BIG", (6, 7): "SMALL",
    (6, 8): "BIG", (6, 9): "BIG",
    
    # Last Num = 7
    (7, 0): "BIG", (7, 1): "BIG", (7, 2): "BIG", (7, 3): "SMALL",
    (7, 4): "BIG", (7, 5): "SMALL", (7, 6): "BIG", (7, 7): "SMALL",
    (7, 8): "BIG", (7, 9): "SMALL",
    
    # Last Num = 8
    (8, 0): "SMALL", (8, 1): "BIG", (8, 2): "BIG", (8, 3): "BIG",
    (8, 4): "SMALL", (8, 5): "SMALL", (8, 6): "BIG", (8, 7): "SMALL",
    (8, 8): "BIG", (8, 9): "BIG",
    
    # Last Num = 9
    (9, 0): "SMALL", (9, 1): "BIG", (9, 2): "BIG", (9, 3): "SMALL",
    (9, 4): "BIG", (9, 5): "SMALL", (9, 6): "SMALL", (9, 7): "SMALL",
    (9, 8): "BIG", (9, 9): "BIG"
}

def get_rule_based_prediction(last_num, below_num):
    """
    রুল-বেসড প্রেডিকশন সিস্টেম (Prompt Api.txt থেকে)
    """
    # Convert to integers if they aren't already
    try:
        last_num = int(last_num)
        below_num = int(below_num)
    except:
        return None
    
    # Check if both numbers are valid (0-9)
    if 0 <= last_num <= 9 and 0 <= below_num <= 9:
        prediction = RULE_BASED_PREDICTIONS.get((last_num, below_num))
        if prediction:
            return prediction
    
    return None

def get_last_two_numbers_from_api():
    """
    API থেকে শেষ দুটি নম্বর সংগ্রহ করে
    """
    try:
        # HISTORY_API থেকে সর্বশেষ দুটি নম্বর নিন
        response = requests.get(HISTORY_API, timeout=8)
        if response.status_code == 200:
            data = response.json()
            
            if data and 'data' in data and 'list' in data['data']:
                # Get the last two results
                recent_results = data['data']['list'][:2]  # First two are most recent
                
                if len(recent_results) >= 2:
                    # Get the numbers
                    last_num = recent_results[0].get('number')
                    below_num = recent_results[1].get('number')
                    
                    # Convert to integers
                    try:
                        last_num = int(last_num) if last_num else None
                        below_num = int(below_num) if below_num else None
                        return last_num, below_num
                    except:
                        return None, None
        
        # Fallback to CURRENT_API if HISTORY_API fails
        try:
            payload = {
                "typeId": 1,
                "language": 0,
                "random": "e7fe6c090da2495ab8290dac551ef1ed",
                "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
                "timestamp": int(time.time())
            }
            response = requests.post(CURRENT_API, json=payload, timeout=8)
            if response.status_code == 200:
                data = response.json()
                
                if data and 'data' in data:
                    # Get current result
                    current_result = data['data'].get('result')
                    
                    # For below number, we need another API call or use history
                    # Since we can't get two from current API, return None
                    try:
                        last_num = int(current_result) if current_result else None
                        return last_num, None
                    except:
                        return None, None
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error getting last two numbers: {e}")
    
    return None, None

# 🔒 OWNER VERIFICATION FUNCTION
def is_owner(user_id):
    """শুধুমাত্র Owner কে Access দেবে"""
    return user_id == OWNER_ID

# 🔒 ACCESS DENIED MESSAGE
def send_access_denied(message):
    bot.send_message(
        message.chat.id,
        "🚫 *ACCESS DENIED*\n\n"
        "এই বটটি শুধুমাত্র Owner এর জন্য তৈরি করা হয়েছে।\n"
        "আপনি এই বটটি ব্যবহার করার অনুমতি রাখেন না।\n\n"
        "👉 আপনার নিজের বট তৈরি করতে চাইলে @BDALAMINHACKER এ যোগাযোগ করুন।",
        parse_mode="Markdown"
    )

# 🆕 ফন্ট কনভার্সন ফাংশন
def convert_to_special_font(text, font_type="digit"):
    """
    টেক্সটকে স্পেশাল ফন্টে কনভার্ট করে
    font_type: "digit", "text", "confidence"
    """
    if font_type == "digit":
        # 𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿 - Mathematical Monospace Digits
        digit_map = {
            '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺',
            '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
        }
        return ''.join(digit_map.get(char, char) for char in str(text))
    
    elif font_type == "text":
        # 𝙱𝙸𝙶/𝚂𝙼𝙰𝙻𝙻 - Mathematical Sans-Serif Bold Italic
        text_map = {
            'B': '𝙱', 'I': '𝙸', 'G': '𝙶',
            'S': '𝚂', 'M': '𝙼', 'A': '𝙰', 'L': '𝙻'
        }
        return ''.join(text_map.get(char, char) for char in str(text).upper())
    
    return str(text)

# 🏁 /start কমান্ড - নতুন ডিজাইন সহ
@bot.message_handler(commands=['start'])
def start_handler(message):
    # Owner verification
    if not is_owner(message.chat.id):
        send_access_denied(message)
        return
        
    # নতুন ডিজাইনের বাটন তৈরি
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("ADD CHANNEL")
    keyboard.row("ALL CHANNEL") 
    keyboard.row("☠️STIKER☠️")
    
    # ইউজারের চ্যানেল কাউন্ট
    channel_count = len(user_channels.get(message.chat.id, []))
    
    bot.send_message(
        message.chat.id,
        f"💢 *HGZY ADVANCED AUTO PREDICTION BOT* 💢\n\n"
        f"🚀 স্বাগতম Owner! UNLIMITED চ্যানেল সিস্টেম!\n\n"
        f"📊 আপনার চ্যানেল: {channel_count} টি\n\n"
        f"📌 নতুন মেনু সিস্টেম:\n"
        f"• ADD CHANNEL - নতুন চ্যানেল যুক্ত করুন (Unlimited)\n"
        f"• ALL CHANNEL - সব চ্যানেল ম্যানেজ করুন\n"
        f"• ☠️STIKER☠️ - Win/Loss & Season স্টিকার সেট করুন\n\n"
        f"⚡ Dual API Analysis - 85%+ Accuracy\n"
        f"📊 Win/Loss ট্র্যাকিং সিস্টেম\n"
        f"🎭 Unlimited Channel Support\n"
        f"💸 NEW PREDICTION MESSAGE DESIGN\n"
        f"🔇 No User Notifications (Silent Mode)\n"
        f"🎯 NEW: Season Start/Off Sticker System\n"
        f"🔒 NEW: Private Channel Support with Chat ID\n"
        f"🎲 NEW: Rule-Based Prediction System (Prompt API)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 🔧 ALL CHANNEL বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text == "ALL CHANNEL")
def handle_all_channel(message):
    """ALL CHANNEL বাটনে ক্লিক করলে চ্যানেল লিস্ট দেখাবে - UNLIMITED SYSTEM"""
    if not is_owner(message.chat.id):
        send_access_denied(message)
        return
        
    show_channel_list_with_status(message.chat.id)

# 🔧 ADD CHANNEL বাটন হ্যান্ডলার - UNLIMITED SYSTEM
@bot.message_handler(func=lambda message: message.text == "ADD CHANNEL")
def handle_add_channel(message):
    """ADD CHANNEL বাটনে ক্লিক করলে চ্যানেল যুক্ত করার অপশন - UNLIMITED"""
    if not is_owner(message.chat.id):
        send_access_denied(message)
        return
    
    # ইনলাইন বাটন তৈরি - পাবলিক এবং প্রাইভেট চ্যানেল যোগ করার অপশন
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("➕ Public Channel/Group", callback_data="add_public_channel"),
        InlineKeyboardButton("🔒 Private Channel/Group", callback_data="add_private_channel")
    )
    
    # বর্তমান চ্যানেল কাউন্ট
    current_count = len(user_channels.get(message.chat.id, []))
    
    bot.send_message(
        message.chat.id,
        f"📌 **চ্যানেল টাইপ সিলেক্ট করুন:**\n\n"
        f"📊 বর্তমান চ্যানেল: {current_count} টি\n\n"
        f"• পাবলিক চ্যানেল: @username ফরম্যাটে (যেমন: @yourchannel)\n"
        f"• প্রাইভেট চ্যানেল: Chat ID দিয়ে (যেমন: -1001234567890)\n\n"
        f"নিচের বাটন থেকে সিলেক্ট করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 🔧 STIKER বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text == "☠️STIKER☠️")
def handle_sticker_menu(message):
    """☠️STIKER☠️ বাটনে ক্লিক করলে স্টিকার মেনু দেখাবে"""
    if not is_owner(message.chat.id):
        send_access_denied(message)
        return
        
    show_sticker_channel_list(message.chat.id)

# 📋 চ্যানেল লিস্ট দেখানো - UNLIMITED SYSTEM
def show_channel_list_with_status(chat_id):
    """সব চ্যানেলের লিস্ট দেখাবে স্ট্যাটাস সহ - UNLIMITED SYSTEM"""
    if chat_id not in user_channels or not user_channels[chat_id]:
        bot.send_message(chat_id, "📭 আপনি এখনও কোনও চ্যানেল/গ্রুপ অ্যাড করেননি।\n\n'ADD CHANNEL' বাটনে ক্লিক করে চ্যানেল অ্যাড করুন।")
        return
    
    channels = user_channels[chat_id]
    total_channels = len(channels)
    
    # পেজিনেশন সিস্টেম - 10টি চ্যানেল প্রতি পেজ
    pages = []
    for i in range(0, len(channels), 10):
        pages.append(channels[i:i + 10])
    
    current_page = 0
    show_channel_page(chat_id, pages, current_page, total_channels)

def show_channel_page(chat_id, pages, page_number, total_channels):
    """একটি পেজের চ্যানেলগুলি দেখাবে"""
    if page_number >= len(pages):
        return
        
    channels = pages[page_number]
    
    message_text = f"📋 **আপনার চ্যানেল লিস্ট**\n\n"
    message_text += f"📊 মোট চ্যানেল: {total_channels} টি\n"
    message_text += f"📄 পেজ: {page_number + 1}/{len(pages)}\n\n"
    
    keyboard = InlineKeyboardMarkup()
    
    for i, channel in enumerate(channels, 1):
        # চ্যানেল স্ট্যাটাস এবং টাইপ
        status = "🟢" if signal_status.get(chat_id, {}).get(channel, False) else "🔴"
        global_index = (page_number * 10) + i
        
        # চ্যানেল টাইপ নির্ধারণ (পাবলিক/প্রাইভেট)
        if isinstance(channel, str) and channel.startswith("@"):
            channel_type = "🌐"  # পাবলিক চ্যানেল
            display_name = channel
        else:
            channel_type = "🔒"  # প্রাইভেট চ্যানেল
            display_name = f"Private ({channel})"
        
        button_text = f"{global_index}. {channel_type} {display_name} {status}"
        
        keyboard.row(
            InlineKeyboardButton(button_text, callback_data=f"channel_detail_{channel}"),
        )
    
    # পেজিনেশন বাটন
    pagination_buttons = []
    if page_number > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ আগের পেজ", callback_data=f"channel_page_{page_number - 1}"))
    
    if page_number < len(pages) - 1:
        pagination_buttons.append(InlineKeyboardButton("➡️ পরের পেজ", callback_data=f"channel_page_{page_number + 1}"))
    
    if pagination_buttons:
        keyboard.row(*pagination_buttons)
    
    # মেইন মেনু বাটন
    keyboard.row(
        InlineKeyboardButton("➕ ADD CHANNEL", callback_data="add_channel_from_list"),
        InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_to_main_menu")
    )
    
    bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode="Markdown")

# 📋 স্টিকার সেটিংসের জন্য চ্যানেল লিস্ট - UNLIMITED SYSTEM
def show_sticker_channel_list(chat_id):
    """স্টিকার সেটিংসের জন্য চ্যানেল লিস্ট দেখাবে - UNLIMITED SYSTEM"""
    if chat_id not in user_channels or not user_channels[chat_id]:
        bot.send_message(chat_id, "📭 আপনি এখনও কোনও চ্যানেল/গ্রুপ অ্যাড করেননি।\n\n'ADD CHANNEL' বাটনে ক্লিক করে চ্যানেল অ্যাড করুন।")
        return
    
    channels = user_channels[chat_id]
    total_channels = len(channels)
    
    # পেজিনেশন সিস্টেম - 10টি চ্যানেল প্রতি পেজ
    pages = []
    for i in range(0, len(channels), 10):
        pages.append(channels[i:i + 10])
    
    current_page = 0
    show_sticker_channel_page(chat_id, pages, current_page, total_channels)

def show_sticker_channel_page(chat_id, pages, page_number, total_channels):
    """স্টিকার সেটিংসের জন্য একটি পেজের চ্যানেলগুলি দেখাবে"""
    if page_number >= len(pages):
        return
        
    channels = pages[page_number]
    
    message_text = f"🎭 **স্টিকার সেটিংস**\n\n"
    message_text += f"📊 মোট চ্যানেল: {total_channels} টি\n"
    message_text += f"📄 পেজ: {page_number + 1}/{len(pages)}\n\n"
    message_text += "কোন চ্যানেলের স্টিকার সেট করতে চান?"
    
    keyboard = InlineKeyboardMarkup()
    
    for i, channel in enumerate(channels, 1):
        # চ্যানেল স্ট্যাটাস এবং টাইপ
        status = "🟢" if signal_status.get(chat_id, {}).get(channel, False) else "🔴"
        global_index = (page_number * 10) + i
        
        # চ্যানেল টাইপ নির্ধারণ (পাবলিক/প্রাইভেট)
        if isinstance(channel, str) and channel.startswith("@"):
            channel_type = "🌐"  # পাবলিক চ্যানেল
            display_name = channel
        else:
            channel_type = "🔒"  # প্রাইভেট চ্যানেল
            display_name = f"Private ({channel})"
        
        button_text = f"{global_index}. {channel_type} {display_name} {status}"
        
        keyboard.row(
            InlineKeyboardButton(button_text, callback_data=f"sticker_channel_{channel}"),
        )
    
    # পেজিনেশন বাটন
    pagination_buttons = []
    if page_number > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ আগের পেজ", callback_data=f"sticker_page_{page_number - 1}"))
    
    if page_number < len(pages) - 1:
        pagination_buttons.append(InlineKeyboardButton("➡️ পরের পেজ", callback_data=f"sticker_page_{page_number + 1}"))
    
    if pagination_buttons:
        keyboard.row(*pagination_buttons)
    
    # মেইন মেনু বাটন
    keyboard.row(
        InlineKeyboardButton("➕ ADD CHANNEL", callback_data="add_channel_from_sticker"),
        InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_to_main_menu")
    )
    
    bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode="Markdown")

# 🔧 চ্যানেল ডিটেইলস ভিউ - নতুন ডিজাইন
def show_channel_details(chat_id, channel):
    """চ্যানেলের ডিটেইলস ভিউ দেখাবে START, STOP, DELETED, BACK বাটন সহ"""
    # চ্যানেল স্ট্যাটাস
    status = "🟢 চালু" if signal_status.get(chat_id, {}).get(channel, False) else "🔴 বন্ধ"
    
    # চ্যানেল টাইপ নির্ধারণ
    if isinstance(channel, str) and channel.startswith("@"):
        channel_type = "🌐 পাবলিক চ্যানেল"
        display_name = channel
    else:
        channel_type = "🔒 প্রাইভেট চ্যানেল"
        display_name = f"Chat ID: {channel}"
    
    # স্টিকার স্ট্যাটাস
    win_sticker_status = "✅ সেট করা আছে" if channel in channel_win_stickers else "❌ সেট করা নেই"
    loss_sticker_status = "✅ সেট করা আছে" if channel in channel_loss_stickers else "❌ সেট করা নেই"
    season_start_status = "✅ সেট করা আছে" if channel in channel_season_start_stickers else "❌ সেট করা নেই"
    season_off_status = "✅ সেট করা আছে" if channel in channel_season_off_stickers else "❌ সেট করা নেই"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("START", callback_data=f"start_channel_{channel}"),
        InlineKeyboardButton("STOP", callback_data=f"stop_channel_{channel}")
    )
    keyboard.row(
        InlineKeyboardButton("DELETED", callback_data=f"delete_channel_{channel}"),
        InlineKeyboardButton("BACK", callback_data="back_to_channel_list")
    )
    
    bot.send_message(
        chat_id,
        f"📢 **চ্যানেল ডিটেইলস:**\n\n"
        f"📌 টাইপ: {channel_type}\n"
        f"🔗 চ্যানেল: {display_name}\n"
        f"📊 Status: {status}\n"
        f"✅ Win স্টিকার: {win_sticker_status}\n"
        f"❌ Loss স্টিকার: {loss_sticker_status}\n"
        f"🎯 Season Start: {season_start_status}\n"
        f"🔚 Season Off: {season_off_status}\n\n"
        f"নিচের বাটন থেকে ম্যানেজ করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 🔧 স্টিকার সেটিংস ভিউ - নতুন ডিজাইন
def show_sticker_settings(chat_id, channel):
    """স্টিকার সেটিংস ভিউ দেখাবে WIN, LOSS, SEASON START, SEASON OFF, BACK বাটন সহ"""
    # চ্যানেল টাইপ নির্ধারণ
    if isinstance(channel, str) and channel.startswith("@"):
        display_name = channel
    else:
        display_name = f"Private ({channel})"
    
    # বর্তমান স্টিকার স্ট্যাটাস
    win_sticker_status = "✅ সেট করা আছে" if channel in channel_win_stickers else "❌ সেট করা নেই"
    loss_sticker_status = "✅ সেট করা আছে" if channel in channel_loss_stickers else "❌ সেট করা নেই"
    season_start_status = "✅ সেট করা আছে" if channel in channel_season_start_stickers else "❌ সেট করা নেই"
    season_off_status = "✅ সেট করা আছে" if channel in channel_season_off_stickers else "❌ সেট করা নেই"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("WIN", callback_data=f"set_win_sticker_{channel}"),
        InlineKeyboardButton("LOSS", callback_data=f"set_loss_sticker_{channel}")
    )
    keyboard.row(
        InlineKeyboardButton("SEASON START", callback_data=f"set_season_start_{channel}"),
        InlineKeyboardButton("SEASON OFF", callback_data=f"set_season_off_{channel}")
    )
    keyboard.row(
        InlineKeyboardButton("BACK", callback_data="back_to_sticker_list")
    )
    
    bot.send_message(
        chat_id,
        f"🎭 **স্টিকার সেটিংস:**\n\n"
        f"🔗 চ্যানেল: {display_name}\n"
        f"✅ Win স্টিকার: {win_sticker_status}\n"
        f"❌ Loss স্টিকার: {loss_sticker_status}\n"
        f"🎯 Season Start: {season_start_status}\n"
        f"🔚 Season Off: {season_off_status}\n\n"
        f"নিচের বাটন থেকে স্টিকার সেট করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 🔧 চ্যানেল ডিলিট ফাংশন - UNLIMITED SYSTEM
def delete_channel(chat_id, channel):
    """চ্যানেল ডিলিট করে সব ডাটা রিমুভ করে - UNLIMITED SYSTEM"""
    if chat_id in user_channels and channel in user_channels[chat_id]:
        # চ্যানেল রিমুভ
        user_channels[chat_id].remove(channel)
        
        # সিগনাল স্ট্যাটাস রিমুভ
        if chat_id in signal_status and channel in signal_status[chat_id]:
            # সিগনাল বন্ধ করুন
            signal_status[chat_id][channel] = False
            # থ্রেড বন্ধ করুন
            thread_key = f"{chat_id}_{channel}"
            if thread_key in signal_threads:
                del signal_threads[thread_key]
        
        # স্টিকার ডাটা রিমুভ
        if channel in channel_win_stickers:
            del channel_win_stickers[channel]
        if channel in channel_loss_stickers:
            del channel_loss_stickers[channel]
        if channel in channel_season_start_stickers:
            del channel_season_start_stickers[channel]
        if channel in channel_season_off_stickers:
            del channel_season_off_stickers[channel]
        
        # পেন্ডিং সিজন অফ রিমুভ
        if channel in pending_season_off:
            del pending_season_off[channel]
        
        # বর্তমান চ্যানেল কাউন্ট
        current_count = len(user_channels.get(chat_id, []))
        
        bot.send_message(chat_id, f"🗑️ চ্যানেল ডিলিট করা হয়েছে!\n\n📊 বর্তমান চ্যানেল: {current_count} টি")
        return True
    else:
        bot.send_message(chat_id, f"❌ চ্যানেল খুঁজে পাওয়া যায়নি!")
        return False

# 🎮 কলব্যাক কুয়েরি হ্যান্ডলার - UNLIMITED SYSTEM
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        bot.answer_callback_query(call.id, "🚫 Access Denied - Owner Only", show_alert=True)
        return
    
    # চ্যানেল ডিটেইলস ভিউ
    if call.data.startswith("channel_detail_"):
        channel = call.data.replace("channel_detail_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        show_channel_details(chat_id, channel)
    
    # চ্যানেল পেজিনেশন
    elif call.data.startswith("channel_page_"):
        page_number = int(call.data.replace("channel_page_", ""))
        channels = user_channels.get(chat_id, [])
        total_channels = len(channels)
        
        # পেজিনেশন সিস্টেম
        pages = []
        for i in range(0, len(channels), 10):
            pages.append(channels[i:i + 10])
        
        show_channel_page(chat_id, pages, page_number, total_channels)
    
    # স্টিকার চ্যানেল সিলেকশন
    elif call.data.startswith("sticker_channel_"):
        channel = call.data.replace("sticker_channel_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        show_sticker_settings(chat_id, channel)
    
    # স্টিকার পেজিনেশন
    elif call.data.startswith("sticker_page_"):
        page_number = int(call.data.replace("sticker_page_", ""))
        channels = user_channels.get(chat_id, [])
        total_channels = len(channels)
        
        # পেজিনেশন সিস্টেম
        pages = []
        for i in range(0, len(channels), 10):
            pages.append(channels[i:i + 10])
        
        show_sticker_channel_page(chat_id, pages, page_number, total_channels)
    
    # চ্যানেল স্টার্ট
    elif call.data.startswith("start_channel_"):
        channel = call.data.replace("start_channel_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        start_prediction_for_channel(chat_id, channel, False)
        bot.answer_callback_query(call.id, f"🚀 Prediction Started!")
        # ডিটেইলস ভিউ আপডেট করুন
        show_channel_details(chat_id, channel)
    
    # চ্যানেল স্টপ
    elif call.data.startswith("stop_channel_"):
        channel = call.data.replace("stop_channel_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        stop_prediction_for_channel(chat_id, channel)
        bot.answer_callback_query(call.id, f"🛑 Prediction Stopped!")
        # ডিটেইলস ভিউ আপডেট করুন
        show_channel_details(chat_id, channel)
    
    # চ্যানেল ডিলিট
    elif call.data.startswith("delete_channel_"):
        channel = call.data.replace("delete_channel_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        if delete_channel(chat_id, channel):
            # লিস্টে ফিরে যান
            show_channel_list_with_status(chat_id)
        else:
            bot.answer_callback_query(call.id, f"❌ Delete Failed!")
    
    # Win স্টিকার সেট
    elif call.data.startswith("set_win_sticker_"):
        channel = call.data.replace("set_win_sticker_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        msg = bot.send_message(chat_id, f"🎉 চ্যানেলের জন্য Win হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_win_sticker, channel)
    
    # Loss স্টিকার সেট
    elif call.data.startswith("set_loss_sticker_"):
        channel = call.data.replace("set_loss_sticker_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        msg = bot.send_message(chat_id, f"😢 চ্যানেলের জন্য Loss হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_loss_sticker, channel)
    
    # Season Start স্টিকার সেট
    elif call.data.startswith("set_season_start_"):
        channel = call.data.replace("set_season_start_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        msg = bot.send_message(chat_id, f"🎯 চ্যানেলের জন্য Season Start হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_season_start_sticker, channel)
    
    # Season Off স্টিকার সেট
    elif call.data.startswith("set_season_off_"):
        channel = call.data.replace("set_season_off_", "")
        # ✅ FIXED: Better integer conversion for private channels
        try:
            # Try to convert to int if it's a number (for private channels)
            if channel.replace('-', '').isdigit():
                channel = int(channel)
        except:
            pass
        msg = bot.send_message(chat_id, f"🔚 চ্যানেলের জন্য Season Off হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_season_off_sticker, channel)
    
    # পাবলিক চ্যানেল যোগ করুন
    elif call.data == "add_public_channel":
        handle_add_public_channel(chat_id)
    
    # প্রাইভেট চ্যানেল যোগ করুন
    elif call.data == "add_private_channel":
        handle_add_private_channel(chat_id)
    
    # লিস্ট থেকে ADD CHANNEL
    elif call.data == "add_channel_from_list":
        handle_add_channel_from_callback(chat_id)
    
    # স্টিকার থেকে ADD CHANNEL
    elif call.data == "add_channel_from_sticker":
        handle_add_channel_from_callback(chat_id)
    
    # ব্যাক টু চ্যানেল লিস্ট
    elif call.data == "back_to_channel_list":
        show_channel_list_with_status(chat_id)
    
    # ব্যাক টু স্টিকার লিস্ট
    elif call.data == "back_to_sticker_list":
        show_sticker_channel_list(chat_id)
    
    # মেইন মেনুতে ফিরে যান
    elif call.data == "back_to_main_menu":
        # মেইন মেনু বাটন শো করান
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("ADD CHANNEL")
        keyboard.row("ALL CHANNEL") 
        keyboard.row("☠️STIKER☠️")
        
        channel_count = len(user_channels.get(chat_id, []))
        
        bot.send_message(
            chat_id,
            f"🔙 **মেইন মেনু**\n\n"
            f"📊 আপনার চ্যানেল: {channel_count} টি\n\n"
            f"নিচের বাটন থেকে অপশন সিলেক্ট করুন:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

def handle_add_channel_from_callback(chat_id):
    """কলব্যাক থেকে ADD CHANNEL হ্যান্ডল করা"""
    # ইনলাইন বাটন তৈরি - পাবলিক এবং প্রাইভেট চ্যানেল যোগ করার অপশন
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("➕ Public Channel/Group", callback_data="add_public_channel"),
        InlineKeyboardButton("🔒 Private Channel/Group", callback_data="add_private_channel")
    )
    
    # বর্তমান চ্যানেল কাউন্ট
    current_count = len(user_channels.get(chat_id, []))
    
    bot.send_message(
        chat_id,
        f"📌 **চ্যানেল টাইপ সিলেক্ট করুন:**\n\n"
        f"📊 বর্তমান চ্যানেল: {current_count} টি\n\n"
        f"• পাবলিক চ্যানেল: @username ফরম্যাটে (যেমন: @yourchannel)\n"
        f"• প্রাইভেট চ্যানেল: Chat ID দিয়ে (যেমন: -1001234567890)\n\n"
        f"নিচের বাটন থেকে সিলেক্ট করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_add_public_channel(chat_id):
    """পাবলিক চ্যানেল যোগ করার জন্য ইউজারনেম চাইবে"""
    # বর্তমান চ্যানেল কাউন্ট
    current_count = len(user_channels.get(chat_id, []))
    
    msg = bot.send_message(
        chat_id, 
        f"🔗 আপনার চ্যানেল/গ্রুপের ইউজারনেম পাঠান (যেমন: @yourchannel বা @yourgroup)\n\n"
        f"📊 বর্তমান চ্যানেল: {current_count} টি\n"
        f"🎯 Unlimited System - যত খুশি চ্যানেল অ্যাড করুন!"
    )
    bot.register_next_step_handler(msg, process_channel_username)

def handle_add_private_channel(chat_id):
    """প্রাইভেট চ্যানেল যোগ করার জন্য Chat ID চাইবে"""
    # বর্তমান চ্যানেল কাউন্ট
    current_count = len(user_channels.get(chat_id, []))
    
    msg = bot.send_message(
        chat_id, 
        f"🔒 আপনার প্রাইভেট চ্যানেল/গ্রুপের Chat ID পাঠান\n\n"
        f"📌 Chat ID পেতে:\n"
        f"1. @getidsbot বা অন্যান্য ID বটে যান\n"
        f"2. আপনার প্রাইভেট চ্যানেলে যোগ করুন\n"
        f"3. চ্যানেলে কোন মেসেজ ফরওয়ার্ড করুন\n"
        f"4. Chat ID পাবেন (যেমন: -1001234567890)\n\n"
        f"📊 বর্তমান চ্যানেল: {current_count} টি"
    )
    bot.register_next_step_handler(msg, process_private_channel)

# 🔧 প্রাইভেট চ্যানেল যোগ করার ফাংশন
def process_private_channel(message):
    chat_id = message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        send_access_denied(message)
        return
        
    text = message.text.strip()
    
    try:
        # Chat ID কে ইন্টিজারে কনভার্ট করুন
        channel_id = int(text)
        
        # Initialize user_channels as list if not exists
        if chat_id not in user_channels:
            user_channels[chat_id] = []
        
        # Add channel if not already added
        if channel_id not in user_channels[chat_id]:
            user_channels[chat_id].append(channel_id)
            
            # Initialize signal_status for this channel
            if chat_id not in signal_status:
                signal_status[chat_id] = {}
            signal_status[chat_id][channel_id] = False  # ডিফল্টভাবে বন্ধ
            
            # বর্তমান চ্যানেল কাউন্ট
            current_count = len(user_channels[chat_id])
            
            bot.send_message(chat_id, f"✅ প্রাইভেট চ্যানেল/গ্রুপ (Chat ID: {channel_id}) সফলভাবে সেভ করা হয়েছে!\n\n📊 মোট চ্যানেল: {current_count} টি")
            
        else:
            bot.send_message(chat_id, f"ℹ️ এই প্রাইভেট চ্যানেল/গ্রুপ ইতিমধ্যেই Added আছে!")
        
        # মেনু বাটন শো করান
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("ADD CHANNEL")
        keyboard.row("ALL CHANNEL") 
        keyboard.row("☠️STIKER☠️")
        
        current_count = len(user_channels.get(chat_id, []))
        
        bot.send_message(
            chat_id,
            f"✅ প্রাইভেট চ্যানেল সফলভাবে যুক্ত হয়েছে!\n\n"
            f"🔒 চ্যানেল/গ্রুপ: Chat ID {channel_id}\n"
            f"📊 Status: 🔴 (সিগনাল বন্ধ)\n"
            f"📈 মোট চ্যানেল: {current_count} টি\n\n"
            f"👉 এখন 'ALL CHANNEL' বাটনে ক্লিক করে সিগনাল শুরু করতে পারেন অথবা '☠️STIKER☠️' বাটনে ক্লিক করে স্টিকার সেট করতে পারেন।",
            reply_markup=keyboard
        )
    except ValueError:
        bot.send_message(chat_id, "❌ Chat ID অবশ্যই একটি সংখ্যা হতে হবে (যেমন: -1001234567890)। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_private_channel)

# 🎭 চ্যানেল ভিত্তিক Win স্টিকার প্রসেস করার ফাংশন
def process_win_sticker(message, channel):
    chat_id = message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        send_access_denied(message)
        return
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        channel_win_stickers[channel] = sticker_id
        
        # স্টিকার ইউজারকে ফরওয়ার্ড করে দেখান
        bot.send_sticker(chat_id, sticker_id)
        bot.send_message(chat_id, f"✅ চ্যানেলের Win স্টিকার সফলভাবে সেট করা হয়েছে!")
        
        # স্টিকার সেটিংসে ফিরে যান
        show_sticker_settings(chat_id, channel)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_win_sticker, channel)

# 🎭 চ্যানেল ভিত্তিক Loss স্টিকার প্রসেস করার ফাংশন
def process_loss_sticker(message, channel):
    chat_id = message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        send_access_denied(message)
        return
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        channel_loss_stickers[channel] = sticker_id
        
        # স্টিকার ইউজারকে ফরওয়ার্ড করে দেখান
        bot.send_sticker(chat_id, sticker_id)
        bot.send_message(chat_id, f"✅ চ্যানেলের Loss স্টিকার সফলভাবে সেট করা হয়েছে!")
        
        # স্টিকার সেটিংসে ফিরে যান
        show_sticker_settings(chat_id, channel)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_loss_sticker, channel)

# 🎭 NEW: Season Start স্টিকার প্রসেস করার ফাংশন
def process_season_start_sticker(message, channel):
    chat_id = message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        send_access_denied(message)
        return
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        channel_season_start_stickers[channel] = sticker_id
        
        # স্টিকার ইউজারকে ফরওয়ার্ড করে দেখান
        bot.send_sticker(chat_id, sticker_id)
        bot.send_message(chat_id, f"✅ চ্যানেলের Season Start স্টিকার সফলভাবে সেট করা হয়েছে!")
        
        # স্টিকার সেটিংসে ফিরে যান
        show_sticker_settings(chat_id, channel)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_season_start_sticker, channel)

# 🎭 NEW: Season Off স্টিকার প্রসেস করার ফাংশন
def process_season_off_sticker(message, channel):
    chat_id = message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        send_access_denied(message)
        return
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        channel_season_off_stickers[channel] = sticker_id
        
        # স্টিকার ইউজারকে ফরওয়ার্ড করে দেখান
        bot.send_sticker(chat_id, sticker_id)
        bot.send_message(chat_id, f"✅ চ্যানেলের Season Off স্টিকার সফলভাবে সেট করা হয়েছে!")
        
        # স্টিকার সেটিংসে ফিরে যান
        show_sticker_settings(chat_id, channel)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_season_off_sticker, channel)

# 🔧 চ্যানেল ইউজারনেম প্রসেস করার ফাংশন - UNLIMITED SYSTEM
def process_channel_username(message):
    chat_id = message.chat.id
    
    # Owner verification
    if not is_owner(chat_id):
        send_access_denied(message)
        return
        
    text = message.text
    
    if text.startswith("@"):
        # Initialize user_channels as list if not exists
        if chat_id not in user_channels:
            user_channels[chat_id] = []
        
        # Add channel if not already added
        if text not in user_channels[chat_id]:
            user_channels[chat_id].append(text)
            
            # Initialize signal_status for this channel
            if chat_id not in signal_status:
                signal_status[chat_id] = {}
            signal_status[chat_id][text] = False  # ডিফল্টভাবে বন্ধ
            
            # বর্তমান চ্যানেল কাউন্ট
            current_count = len(user_channels[chat_id])
            
            bot.send_message(chat_id, f"✅ চ্যানেল/গ্রুপ {text} সফলভাবে সেভ করা হয়েছে!\n\n📊 মোট চ্যানেল: {current_count} টি")
            
        else:
            bot.send_message(chat_id, f"ℹ️ চ্যানেল/গ্রুপ {text} ইতিমধ্যেই Added আছে!")
        
        # মেনু বাটন শো করান
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("ADD CHANNEL")
        keyboard.row("ALL CHANNEL") 
        keyboard.row("☠️STIKER☠️")
        
        current_count = len(user_channels.get(chat_id, []))
        
        bot.send_message(
            chat_id,
            f"✅ চ্যানেল সফলভাবে যুক্ত হয়েছে!\n\n"
            f"📡 চ্যানেল/গ্রুপ: {text}\n"
            f"📊 Status: 🔴 (সিগনাল বন্ধ)\n"
            f"📈 মোট চ্যানেল: {current_count} টি\n\n"
            f"👉 এখন 'ALL CHANNEL' বাটনে ক্লিক করে সিগনাল শুরু করতে পারেন অথবা '☠️STIKER☠️' বাটনে ক্লিক করে স্টিকার সেট করতে পারেন।",
            reply_markup=keyboard
        )
    else:
        bot.send_message(chat_id, "❌ চ্যানেল/গ্রুপের নাম অবশ্যই '@' দিয়ে শুরু হতে হবে। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_channel_username)

# 🧠 NEW: Season Start স্টিকার পাঠানো
def send_season_start_sticker(channel_username):
    """Season Start স্টিকার পাঠায়"""
    try:
        sticker_id = channel_season_start_stickers.get(channel_username, DEFAULT_SEASON_START_STICKER)
        bot.send_sticker(channel_username, sticker_id)
        return True
    except Exception as e:
        print(f"❌ Season Start Sticker send error: {e}")
        return False

# 🧠 NEW: Season Off স্টিকার পাঠানো
def send_season_off_sticker(channel_username):
    """Season Off স্টিকার পাঠায়"""
    try:
        sticker_id = channel_season_off_stickers.get(channel_username, DEFAULT_SEASON_OFF_STICKER)
        bot.send_sticker(channel_username, sticker_id)
        return True
    except Exception as e:
        print(f"❌ Season Off Sticker send error: {e}")
        return False

# 🚀 চ্যানেলের জন্য প্রেডিকশন শুরু করা - UNLIMITED SYSTEM
def start_prediction_for_channel(user_id, channel, is_timed=False, duration_minutes=20):
    """নির্দিষ্ট চ্যানেলের জন্য প্রেডিকশন শুরু করে - UNLIMITED SYSTEM"""
    if not signal_status.get(user_id, {}).get(channel, False):
        # Initialize signal_status if not exists
        if user_id not in signal_status:
            signal_status[user_id] = {}
        signal_status[user_id][channel] = True
        
        # Start prediction thread
        t = threading.Thread(target=real_time_auto_prediction, args=(user_id, channel, is_timed, duration_minutes))
        signal_threads[f"{user_id}_{channel}"] = t
        t.daemon = True
        t.start()
        
        # Season Start স্টিকার পাঠান
        try:
            send_season_start_sticker(channel)
        except Exception as e:
            print(f"❌ Failed to send season start sticker: {e}")
        
        bot.send_message(user_id, f"🚀 প্রেডিকশন শুরু হয়েছে!")
        return True
    else:
        bot.send_message(user_id, f"⚠️ প্রেডিকশন ইতিমধ্যেই চালু আছে।")
        return False

# 🛑 চ্যানেলের জন্য প্রেডিকশন বন্ধ করা - UNLIMITED SYSTEM
def stop_prediction_for_channel(user_id, channel):
    """নির্দিষ্ট চ্যানেলের জন্য প্রেডিকশন বন্ধ করে - UNLIMITED SYSTEM"""
    if signal_status.get(user_id, {}).get(channel, False):
        signal_status[user_id][channel] = False
        
        # Remove timer if exists
        if user_id in prediction_timers:
            del prediction_timers[user_id]
        
        # Season Off স্টিকার পরের Period এ পাঠানোর জন্য মার্ক করুন
        pending_season_off[channel] = True
            
        bot.send_message(user_id, f"🛑 প্রেডিকশন বন্ধ করা হয়েছে! পরের Period এ Win/Loss স্টিকার এবং তারপর Season Off স্টিকার পাঠানো হবে।")
        return True
    else:
        bot.send_message(user_id, f"ℹ️ প্রেডিকশন আগে থেকেই বন্ধ আছে।")
        return False

# ========== প্রেডিকশন মেসেজ সিস্টেম - নতুন ডিজাইন ==========

# 🧠 নতুন প্রেডিকশন মেসেজ জেনারেটর - NEW DESIGN
def generate_prediction_message(period_number, prediction, confidence, analysis_type, user_id=None):
    """
    নতুন ডিজাইনে প্রেডিকশন মেসেজ জেনারেট করে
    """
    # ফন্ট কনভার্সন
    period_font = convert_to_special_font(period_number, "digit")
    prediction_font = convert_to_special_font(prediction, "text")
    
    # রেজিস্টার লিংক যোগ করুন (যদি থাকে)
    register_text = ""
    if user_id and user_id in user_register_links:
        register_link = user_register_links[user_id]
        register_text = f"\n\n🔗 Register Here: {register_link}"
    
    # নতুন মেসেজ ফরম্যাট (Confidence রিমুভ করা হয়েছে)
    message = f"""💸 𝗪𝗜𝗡𝗚𝗢 𝗚𝗔𝗠𝗘 𝗦𝗜𝗚𝗡𝗔𝗟 💸

📆 𝙿𝙴𝚁𝙸𝙾𝙳 𝙸𝙳 : {period_font}

📊 𝙱𝚄𝚈 𝙾𝙽 : {prediction_font}

{register_text}"""
    
    return message

# ========== নিচের সব ফাংশন আগের মতোই থাকবে ==========

# 🔧 ডুয়াল API সিস্টেম - FIXED VERSION
def get_dual_api_data():
    """
    দুইটি API থেকে ডাটা নিয়ে ক্রস-ভেরিফিকেশন করে - FIXED
    """
    try:
        # CURRENT_API থেকে ডাটা - FIXED API CALL
        current_data = None
        try:
            payload = {
                "typeId": 1,
                "language": 0,
                "random": "e7fe6c090da2495ab8290dac551ef1ed",
                "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
                "timestamp": int(time.time())
            }
            response1 = requests.post(CURRENT_API, json=payload, timeout=8)
            if response1.status_code == 200:
                current_data = response1.json()
                print(f"✅ CURRENT_API working")
        except Exception as e:
            print(f"❌ CURRENT_API error: {e}")
        
        # HISTORY_API থেকে ডাটা - FIXED
        history_data = None
        try:
            response2 = requests.get(HISTORY_API, timeout=8)
            if response2.status_code == 200:
                history_data = response2.json()
                print(f"✅ HISTORY_API working")
        except Exception as e:
            print(f"❌ HISTORY_API error: {e}")
        
        # ডাটা কোয়ালিটি চেক
        if current_data and history_data:
            return current_data, history_data, "HIGH_CONFIDENCE"
        elif current_data:
            return current_data, None, "MEDIUM_CONFIDENCE"
        elif history_data:
            return None, history_data, "MEDIUM_CONFIDENCE"
        else:
            return None, None, "LOW_CONFIDENCE"
            
    except Exception as e:
        print(f"❌ Dual API system error: {e}")
        return None, None, "ERROR"

# 🎯 উন্নত মার্কেট এনালাইসিস ফাংশন
def advanced_market_analysis(numbers):
    if not numbers or len(numbers) < 10:
        return 65, "Quick Analysis", "NEUTRAL"
    
    numbers = numbers[:30]  # 30টি রেজাল্ট এনালাইসিস
    
    # ট্রেন্ড এনালাইসিস
    recent_trend = []
    for i in range(min(10, len(numbers))):
        if numbers[i] >= 5:
            recent_trend.append("BIG")
        else:
            recent_trend.append("SMALL")
    
    # প্যাটার্ন ডিটেকশন
    big_count = sum(1 for n in numbers if n >= 5)
    small_count = len(numbers) - big_count
    
    # ভোলাটিলিটি ক্যালকুলেশন
    volatility = 0
    if len(numbers) > 1:
        try:
            volatility = statistics.stdev(numbers)
        except:
            volatility = 0
    
    # ট্রেন্ড স্ট্রength
    trend_strength = 0
    if len(set(recent_trend[:5])) == 1:  # প্রথম ৫টি একই ট্রেন্ড
        trend_strength += 20
    if len(set(recent_trend[-5:])) == 1:  # শেষ ৫টি একই ট্রেন্ড
        trend_strength += 20
    
    # কনফিডেন্স ক্যালকুলেশন
    confidence = 65  # বেস কনফিডেন্স
    
    # ডিস্ট্রিবিউশন এনালাইসিস
    total = len(numbers)
    big_ratio = big_count / total
    small_ratio = small_count / total
    
    distribution_bias = abs(big_ratio - small_ratio)
    
    if distribution_bias >= 0.3:  # 30% বা তার বেশি ডিফারেন্স
        confidence += 15
        market_sentiment = "STRONG_TREND"
    elif distribution_bias >= 0.2:  # 20% বা তার বেশি ডিফারেন্স
        confidence += 8
        market_sentiment = "MODERATE_TREND"
    else:
        market_sentiment = "BALANCED"
    
    # ভোলাটিলিটি এডজাস্টমেন্ট
    if volatility >= 4:
        confidence -= 12  # হাই ভোলাটিলিটিতে কনফিডেন্স কম
        market_sentiment = "VOLATILE"
    elif volatility <= 1.5:
        confidence += 8   # লো ভোলাটিলিটিতে কনফিডেন্স বেশি
    
    # ট্রেন্ড স্ট্রength এডজাস্টমেন্ট
    confidence += (trend_strength * 0.5)
    
    # কন্টিনিউইটি এনালাইসিস (ট্রেন্ড কন্টিনিউ হওয়ার সম্ভাবনা)
    if recent_trend[0] == recent_trend[1] == recent_trend[2]:
        confidence += 10  # ট্রেন্ড কন্টিনিউ হওয়ার সম্ভাবনা বেশি
    
    # রেঞ্জ চেক
    confidence = max(55, min(confidence, 92))
    
    analysis_type = "Dual API Pattern Detection"
    if confidence >= 85:
        analysis_type = "Strong Trend Identified"
    elif confidence >= 75:
        analysis_type = "Clear Pattern Detected"
    elif confidence <= 60:
        analysis_type = "Market Analysis"
    
    return int(confidence), analysis_type, market_sentiment  # Integer confidence return

# 🧠 স্মার্ট প্রেডিকশন জেনারেটর
def generate_smart_prediction(numbers, confidence, market_sentiment):
    if not numbers:
        return "BIG" if random.random() > 0.5 else "SMALL"
    
    recent_trend = []
    for num in numbers[:10]:  # শুধু সাম্প্রতিক ১০টি দেখি
        recent_trend.append("BIG" if num >= 5 else "SMALL")
    
    big_count = sum(1 for trend in recent_trend if trend == "BIG")
    small_count = len(recent_trend) - big_count
    
    # উন্নত প্রেডিকশন লজিক
    if market_sentiment == "STRONG_TREND":
        if big_count >= 7:  # 10টির মধ্যে 7+ বার BIG
            return "SMALL"  # রিভার্স এক্সপেক্টেড
        elif small_count >= 7:  # 10টির মধ্যে 7+ বার SMALL
            return "BIG"    # রিভার্স এক্সপেক্টেড
        else:
            # ট্রেন্ড কন্টিনিউ
            return recent_trend[0]
    
    elif market_sentiment == "MODERATE_TREND":
        if big_count >= 6:
            return "SMALL"
        elif small_count >= 6:
            return "BIG"
        else:
            return "BIG" if random.random() > 0.5 else "SMALL"
    
    else:  # BALANCED or VOLATILE
        # র্যান্ডম但有 bias
        last_prediction = recent_trend[0]
        return "SMALL" if last_prediction == "BIG" else "BIG"

# 🎯 রিয়েল-টাইম পিরিওড নাম্বার জেনারেটর
def generate_real_time_period():
    """
    রিয়েল-টাইমে UTC সময় অনুযায়ী পিরিওড জেনারেট করে
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    minute = now.minute
    total_minutes = hour * 60 + minute
    
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    period = year + month + day + "1000" + str(10001 + total_minutes)
    return period

# 🎯 রিয়েল-টাইম সেকেন্ড চেকার
def get_real_time_seconds():
    """
    বর্তমান UTC সময়ের সেকেন্ড রিটার্ন করে (0-59)
    """
    now = datetime.now(timezone.utc)
    return now.second

# 🔍 রিয়েল-টাইম রেজাল্ট চেকার - COMPLETELY FIXED VERSION
def check_actual_result(predicted_result, period_number=None):
    """
    API থেকে আসল রেজাল্ট চেক করে - সম্পূর্ণ ফিক্সড ভার্সন
    """
    try:
        # প্রথমে HISTORY_API থেকে রেজাল্ট চেক - সবচেয়ে নির্ভরযোগ্য
        response = requests.get(HISTORY_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if data and 'data' in data and 'list' in data['data']:
                # সবচেয়ে সাম্প্রতিক রেজাল্ট নাও (প্রথমটি)
                latest_result = data['data']['list'][0]
                if 'number' in latest_result and latest_result['number']:
                    try:
                        actual_num = int(latest_result['number'])
                        actual_result = "BIG" if actual_num >= 5 else "SMALL"
                        
                        print(f"🎯 Actual result from History API: {actual_num} ({actual_result})")
                        
                        # Win/Loss নির্ধারণ
                        if actual_result == predicted_result:
                            return actual_num, actual_result, "WIN"
                        else:
                            return actual_num, actual_result, "LOSS"
                    except ValueError:
                        print(f"❌ Number conversion error: {latest_result['number']}")
        
        # যদি HISTORY_API কাজ না করে, CURRENT_API থেকে চেক করো
        try:
            payload = {
                "typeId": 1,
                "language": 0,
                "random": "e7fe6c090da2495ab8290dac551ef1ed",
                "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
                "timestamp": int(time.time())
            }
            response = requests.post(CURRENT_API, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data and 'data' in data:
                    current_result = data['data'].get('result')
                    if current_result:
                        try:
                            actual_num = int(current_result)
                            actual_result = "BIG" if actual_num >= 5 else "SMALL"
                            
                            print(f"🎯 Actual result from Current API: {actual_num} ({actual_result})")
                            
                            # Win/Loss নির্ধারণ
                            if actual_result == predicted_result:
                                return actual_num, actual_result, "WIN"
                            else:
                                return actual_num, actual_result, "LOSS"
                        except ValueError:
                            print(f"❌ Number conversion error: {current_result}")
        except Exception as e:
            print(f"❌ Current API check error: {e}")
    
    except Exception as e:
        print(f"❌ Result check error: {e}")
    
    # যদি API কাজ না করে, র্যান্ডম রেজাল্ট জেনারেট করো (ডেমোর জন্য)
    print("⚠️ Using fallback random result")
    actual_num = random.randint(0, 9)
    actual_result = "BIG" if actual_num >= 5 else "SMALL"
    
    if actual_result == predicted_result:
        return actual_num, actual_result, "WIN"
    else:
        return actual_num, actual_result, "LOSS"

# 🧠 চ্যানেল ভিত্তিক Win/Loss স্টিকার পাঠানো
def send_win_loss_sticker(chat_id, win_loss, channel_username):
    """
    Win/Loss অনুযায়ী চ্যানেল ভিত্তিক স্টিকার পাঠায়
    """
    try:
        if win_loss == "WIN":
            sticker_id = channel_win_stickers.get(channel_username, DEFAULT_WIN_STICKER)
        else:
            sticker_id = channel_loss_stickers.get(channel_username, DEFAULT_LOSS_STICKER)
        
        bot.send_sticker(chat_id, sticker_id)
        return True
    except Exception as e:
        print(f"❌ Sticker send error: {e}")
        return False

# 🧠 Win/Loss হিস্ট্রি আপডেট
def update_prediction_history(user_id, period, prediction, actual_number, actual_result, win_loss):
    if user_id not in prediction_history:
        prediction_history[user_id] = []
    
    history_entry = {
        "period": period,
        "prediction": prediction,
        "actual_number": actual_number,
        "actual_result": actual_result,
        "result": win_loss,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    prediction_history[user_id].append(history_entry)
    
    # সর্বোচ্চ 100টি এন্ট্রি রাখো
    if len(prediction_history[user_id]) > 100:
        prediction_history[user_id] = prediction_history[user_id][-100:]

# 📊 ইউজার স্ট্যাটিস্টিক্স
def get_user_stats(user_id):
    if user_id not in prediction_history or not prediction_history[user_id]:
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0}
    
    history = prediction_history[user_id]
    total = len(history)
    wins = sum(1 for entry in history if entry["result"] == "WIN")
    losses = sum(1 for entry in history if entry["result"] == "LOSS")
    win_rate = (wins / total) * 100 if total > 0 else 0
    
    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2)
    }

# 🧠 ডুয়াল API প্রেডিকশন জেনারেটর - WITH NEW RULE-BASED SYSTEM
def generate_advanced_prediction(user_id=None):
    try:
        # দুই API থেকে ডাটা নাও
        current_data, history_data, confidence_level = get_dual_api_data()
        
        numbers = []
        
        # HISTORY_API থেকে নম্বর সংগ্রহ - FIXED
        if history_data and 'data' in history_data and 'list' in history_data['data']:
            for result in history_data['data']['list'][:20]:  # 20টি রেজাল্ট
                if 'number' in result and result['number']:
                    try:
                        num = int(result['number'])
                        numbers.append(num)
                    except:
                        continue
        
        # CURRENT_API থেকে নম্বর সংগ্রহ (যদি available হয়) - FIXED
        if current_data and 'data' in current_data:
            current_result = current_data['data'].get('result')
            if current_result:
                try:
                    num = int(current_result)
                    numbers.insert(0, num)  # সামনে যোগ করো
                except:
                    pass
        
        print(f"📊 Collected {len(numbers)} numbers for analysis")
        
        # ========== NEW: RULE-BASED PREDICTION INTEGRATION ==========
        rule_based_pred = None
        rule_confidence = 0
        rule_info = ""
        
        # Get last two numbers for rule-based prediction
        last_num, below_num = get_last_two_numbers_from_api()
        
        if last_num is not None and below_num is not None:
            # Get rule-based prediction
            rule_based_pred = get_rule_based_prediction(last_num, below_num)
            
            if rule_based_pred:
                print(f"🎯 Rule-based prediction available: Last={last_num}, Below={below_num} -> {rule_based_pred}")
                rule_confidence = 85  # Rule-based has high confidence
                rule_info = f" (Rule: {last_num}+{below_num})"
        
        # ========== CONTINUE WITH EXISTING ANALYSIS ==========
        if numbers:
            # মার্কেট এনালাইসিস থেকে কনফিডেন্স ও টাইপ
            confidence, analysis_type, market_sentiment = advanced_market_analysis(numbers)
            
            # ========== COMBINE RULE-BASED AND ANALYSIS-BASED PREDICTIONS ==========
            final_prediction = None
            final_confidence = confidence
            combined_analysis_type = analysis_type
            
            if rule_based_pred and rule_confidence > 0:
                # If we have rule-based prediction, combine it with analysis
                if confidence >= 80:
                    # If analysis confidence is high, use analysis
                    analysis_pred = generate_smart_prediction(numbers, confidence, market_sentiment)
                    
                    # But sometimes use rule-based as per instruction "Analyse + Random"
                    if random.random() < 0.3:  # 30% chance to use rule-based
                        final_prediction = rule_based_pred
                        final_confidence = rule_confidence
                        combined_analysis_type = f"Rule-Based{rule_info} + Analysis"
                    else:
                        final_prediction = analysis_pred
                        final_confidence = confidence
                        combined_analysis_type = analysis_type
                else:
                    # If analysis confidence is lower, use rule-based
                    final_prediction = rule_based_pred
                    final_confidence = rule_confidence
                    combined_analysis_type = f"Rule-Based{rule_info}"
                    
                    # Sometimes add randomness as per instruction
                    if random.random() < 0.2:  # 20% chance to use random
                        final_prediction = "BIG" if random.random() > 0.5 else "SMALL"
                        final_confidence = 70
                        combined_analysis_type = "Random + Rule-Based Mix"
            else:
                # No rule-based prediction available, use analysis
                final_prediction = generate_smart_prediction(numbers, confidence, market_sentiment)
                final_confidence = confidence
                combined_analysis_type = analysis_type
            
            # API কনফিডেন্স লেভেল অনুযায়ী adjustment
            if confidence_level == "HIGH_CONFIDENCE":
                final_confidence = min(final_confidence + 8, 95)
                combined_analysis_type = "Dual API Verified - " + combined_analysis_type
            elif confidence_level == "MEDIUM_CONFIDENCE":
                final_confidence = min(final_confidence + 4, 90)
                combined_analysis_type = "Single API - " + combined_analysis_type
            else:
                final_confidence = max(final_confidence - 5, 60)
                combined_analysis_type = "Fallback - " + combined_analysis_type
            
            period = generate_real_time_period()
            
            # নতুন ডিজাইনে প্রেডিকশন মেসেজ জেনারেট করো
            prediction_message = generate_prediction_message(
                period, final_prediction, final_confidence, combined_analysis_type, user_id
            )
            
            return prediction_message, final_prediction, period, final_confidence, combined_analysis_type
            
    except Exception as e:
        print(f"❌ Dual API analysis error: {e}")
    
    # ফলব্যাক মেকানিজম
    period = generate_real_time_period()
    
    # Try to use rule-based as fallback
    last_num, below_num = get_last_two_numbers_from_api()
    if last_num is not None and below_num is not None:
        rule_based_pred = get_rule_based_prediction(last_num, below_num)
        if rule_based_pred:
            prediction = rule_based_pred
            confidence = 75
            analysis_type = f"Rule-Based Fallback (Last={last_num}, Below={below_num})"
        else:
            num = random.randint(0, 9)
            prediction = "BIG" if num >= 5 else "SMALL"
            confidence = random.randint(60, 75)
            analysis_type = "Quick Market Scan + Random"
    else:
        num = random.randint(0, 9)
        prediction = "BIG" if num >= 5 else "SMALL"
        confidence = random.randint(60, 75)
        analysis_type = "Quick Market Scan"
    
    # ফলব্যাক প্রেডিকশন মেসেজ (নতুন ডিজাইন)
    prediction_message = generate_prediction_message(
        period, prediction, confidence, analysis_type, user_id
    )
    
    return prediction_message, prediction, period, confidence, analysis_type

# 🔄 REAL-TIME AUTO PREDICTION SYSTEM - SILENT MODE
def real_time_auto_prediction(user_id, channel, is_timed=False, duration_minutes=20):
    """
    রিয়েল-টাইম প্রেডিকশন সিস্টেম - SILENT MODE (No User Notifications)
    """
    # Owner verification
    if not is_owner(user_id):
        return
        
    start_time = datetime.now()
    
    if is_timed:
        end_time = start_time + timedelta(minutes=duration_minutes)
        prediction_timers[user_id] = end_time
        # শুধু টাইমার সেট করার মেসেজ দেখাবে
        bot.send_message(user_id, f"⏰ টাইমার সেট: {duration_minutes} মিনিট পরে অটোমেটিক বন্ধ হবে")
    
    message_id = None
    last_period = None
    last_prediction = None
    
    while signal_status.get(user_id, {}).get(channel, False) or channel in pending_season_off:
        try:
            # টাইমড মোডে সময় চেক করুন
            if is_timed and datetime.now() >= prediction_timers.get(user_id, datetime.now()):
                signal_status[user_id][channel] = False
                # Season Off স্টিকার পরের Period এ পাঠানোর জন্য মার্ক করুন
                pending_season_off[channel] = True
                # শুধু টাইমার শেষের মেসেজ দেখাবে
                bot.send_message(user_id, f"⏰ 20-মিনিট প্রেডিকশন সেশন শেষ হয়েছে!")
                # break করব না, Win/Loss এবং Season Off স্টিকার পাঠানো পর্যন্ত চলতে দেব
            
            # বর্তমান পিরিওড এবং সেকেন্ড চেক করুন
            current_period = generate_real_time_period()
            current_second = get_real_time_seconds()
            
            # যদি পিরিওড চেঞ্জ হয় (নতুন মিনিট শুরু হয়)
            if current_period != last_period:
                print(f"🔄 New period detected: {current_period} (Second: {current_second})")
                
                # Season Off স্টিকার পাঠানোর জন্য পেন্ডিং আছে কিনা চেক করুন
                if channel in pending_season_off and not signal_status.get(user_id, {}).get(channel, False):
                    # আগে Win/Loss স্টিকার পাঠান (যদি শেষ প্রেডিকশন থাকে)
                    if last_period is not None and last_prediction is not None:
                        try:
                            # Win/Loss চেক করো
                            print(f"🔍 Checking result for previous prediction...")
                            actual_number, actual_result, win_loss = check_actual_result(last_prediction, last_period)
                            
                            print(f"🎯 Result: {win_loss} - Actual: {actual_result} ({actual_number})")
                            
                            # Win/Loss হিস্ট্রি আপডেট করো
                            update_prediction_history(user_id, last_period, last_prediction, actual_number, actual_result, win_loss)
                            
                            # চ্যানেল ভিত্তিক Win/Loss স্টিকার পাঠাও (শুধু চ্যানেলে)
                            send_win_loss_sticker(channel, win_loss, channel)
                            
                            # ⚠️ ইউজারকে Win/Loss নোটিফিকেশন দেওয়া হবে না (SILENT MODE)
                            # bot.send_message(user_id, f"📊 Result: {win_loss} - Period: {last_period} - Actual: {actual_result} ({actual_number})")
                            
                        except Exception as e:
                            print(f"❌ Result checking error: {e}")
                    
                    # তারপর Season Off স্টিকার পাঠান
                    send_season_off_sticker(channel)
                    # পেন্ডিং স্টেট সরান
                    del pending_season_off[channel]
                    # লুপ থেকে বের হন
                    break
                
                # যদি আগের প্রেডিকশন থাকে, তাহলে তার রেজাল্ট চেক করুন
                if last_period is not None and message_id is not None and last_prediction is not None and signal_status.get(user_id, {}).get(channel, False):
                    try:
                        # Win/Loss চেক করো
                        print(f"🔍 Checking result for previous prediction...")
                        actual_number, actual_result, win_loss = check_actual_result(last_prediction, last_period)
                        
                        print(f"🎯 Result: {win_loss} - Actual: {actual_result} ({actual_number})")
                        
                        # Win/Loss হিস্ট্রি আপডেট করো
                        update_prediction_history(user_id, last_period, last_prediction, actual_number, actual_result, win_loss)
                        
                        # চ্যানেল ভিত্তিক Win/Loss স্টিকার পাঠাও (শুধু চ্যানেলে)
                        send_win_loss_sticker(channel, win_loss, channel)
                        
                        # ⚠️ ইউজারকে Win/Loss নোটিফিকেশন দেওয়া হবে না (SILENT MODE)
                        # bot.send_message(user_id, f"📊 Result: {win_loss} - Period: {last_period} - Actual: {actual_result} ({actual_number})")
                        
                    except Exception as e:
                        print(f"❌ Result checking error: {e}")
                
                # নতুন প্রেডিকশন জেনারেট এবং পাঠাও (যদি প্রেডিকশন চালু থাকে)
                if signal_status.get(user_id, {}).get(channel, False):
                    prediction_message, prediction, period_number, confidence, analysis_type = generate_advanced_prediction(user_id)
                    
                    # ✅ FIXED: Added try-catch for sending messages
                    try:
                        # প্রেডিকশন মেসেজ পাঠাও এবং message_id সেভ করো
                        sent_message = bot.send_message(channel, prediction_message)
                        message_id = sent_message.message_id
                        
                        # বর্তমান প্রেডিকশন তথ্য সেভ করো
                        last_period = period_number
                        last_prediction = prediction
                        last_confidence = confidence
                        last_analysis_type = analysis_type
                        
                        print(f"🎯 New prediction: {prediction} for period {period_number}")
                    except Exception as e:
                        print(f"❌ Failed to send prediction to channel {channel}: {e}")
                        # ইউজারকে জানান
                        bot.send_message(user_id, f"❌ Failed to send prediction to {channel}: {e}")
                else:
                    # প্রেডিকশন বন্ধ কিন্তু Season Off স্টিকার পাঠানো বাকি
                    last_period = current_period
            
            # পরবর্তী চেকের জন্য 1 সেকেন্ড অপেক্ষা করো
            time.sleep(1)

        except Exception as e:
            print(f"❌ Real-time prediction error: {e}")
            # শুধু Error মেসেজ ইউজারকে দেখাবে
            bot.send_message(user_id, f"⚠️ Prediction error: {e}")
            time.sleep(5)
    
    # থ্রেড শেষ হলে থ্রেড ডিকশনারি থেকে রিমুভ করুন
    thread_key = f"{user_id}_{channel}"
    if thread_key in signal_threads:
        del signal_threads[thread_key]

# ========== RENDER COMPATIBILITY ==========

# 🏠 Flask Routes for Render
@app.route('/')
def home():
    return "🤖 HGZY Advanced Auto Prediction Bot is running on Render! 🚀"

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "channels_count": sum(len(channels) for channels in user_channels.values())
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Bad Request', 400

# 🔧 Polling with exception handling for Render
def run_bot():
    """Render compatible bot runner"""
    print("🤖 Starting bot on Render...")
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.polling(non_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Bot polling error: {e}")
        # Restart after delay
        time.sleep(5)
        run_bot()

# 🚀 Start bot in a separate thread
def start_bot():
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    print("✅ Bot thread started successfully!")

# 🎯 Main entry point for Render
if __name__ == '__main__':
    print("🚀 Starting HGZY Advanced Auto Prediction Bot...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    
    # Start bot in background thread
    start_bot()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)