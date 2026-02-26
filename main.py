import os
import telebot
import requests
import time
import random
from threading import Thread
from flask import Flask
from deep_translator import GoogleTranslator

# --- ВЕБ-СЕРВЕР ---
app = Flask('')
@app.route('/')
def home(): return "Kevin V3.1 is Online"

def run_web_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Быстрая модель SDXL-Lightning
API_URL = "https://api-inference.huggingface.co/models/ByteDance/SDXL-Lightning-4step"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 **Кевин V3.1 (с переводчиком)!**\nПиши на русском или английском: `/draw космонавт на лошади`", parse_mode='Markdown')

@bot.message_handler(commands=['draw'])
def draw(message):
    user_prompt = message.text.replace('/draw', '').strip()
    if not user_prompt:
        bot.reply_to(message, "⚠️ Опиши картинку!")
        return

    msg = bot.reply_to(message, "⚙️ Перевожу и готовлю холст...")

    try:
        # 1. АВТОПЕРЕВОД на английский
        translated_prompt = GoogleTranslator(source='auto', target='en').translate(user_prompt)
        bot.edit_message_text(f"🎨 Рисую: _{translated_prompt}_", message.chat.id, msg.message_id, parse_mode='Markdown')
        
        # 2. ГЕНЕРАЦИЯ
        for attempt in range(3):
            # Добавляем случайный шум в запрос для уникальности
            payload = {"inputs": f"{translated_prompt}, seed={random.randint(1,1000)}"}
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                bot.send_photo(message.chat.id, response.content, caption=f"✨ Готово!\n📝 Запрос: {user_prompt}")
                bot.delete_message(message.chat.id, msg.message_id)
                return
            
            elif response.status_code == 503:
                time.sleep(10) # Подождем прогрева
                continue
            
            else:
                bot.edit_message_text(f"❌ Ошибка ИИ ({response.status_code}). Попробуй еще раз.", message.chat.id, msg.message_id)
                return

    except Exception as e:
        bot.edit_message_text(f"❌ Произошла ошибка: {e}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    bot.infinity_polling(skip_pending=True)
