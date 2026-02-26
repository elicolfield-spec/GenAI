import os
import telebot
import requests
import random
import time
from threading import Thread
from flask import Flask

# --- ВЕБ-ЗАГЛУШКА ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- БОТ ---
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Привет! Напиши `/draw что-то на английском`", parse_mode='Markdown')

@bot.message_handler(commands=['draw'])
def draw(message):
    prompt = message.text.replace('/draw', '').strip()
    if not prompt:
        bot.reply_to(message, "Введите описание!")
        return

    status = bot.reply_to(message, "🎨 Машина думает... (10-15 сек)")

    # Генерируем случайный seed для уникальности
    seed = random.randint(1, 999999)
    
    # Кодируем запрос, чтобы не было ошибок в ссылке
    clean_prompt = requests.utils.quote(prompt)
    
    # ФОРМАТ ССЫЛКИ (самый простой и надежный)
    image_url = f"https://pollinations.ai/p/{clean_prompt}?width=1024&height=1024&seed={seed}&nologo=true"

    try:
        # Делаем запрос с увеличенным временем ожидания (60 сек)
        response = requests.get(image_url, timeout=60)
        
        # Проверяем: если картинка пришла (обычно картинки > 30 Кб)
        if response.status_code == 200 and len(response.content) > 10000:
            bot.send_photo(message.chat.id, response.content, caption=f"✨ Готово! Запрос: {prompt}")
            bot.delete_message(message.chat.id, status.message_id)
        else:
            # Если вернулась пустышка, пробуем еще один формат ссылки как запасной
            fallback_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?nologo=1"
            res2 = requests.get(fallback_url, timeout=30)
            if res2.status_code == 200:
                bot.send_photo(message.chat.id, res2.content, caption=f"✅ (Запасной канал) Запрос: {prompt}")
                bot.delete_message(message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ Сервер перегружен. Попробуй через минуту.", message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка соединения: {e}", message.chat.id, status.message_id)

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    bot.infinity_polling(skip_pending=True)
