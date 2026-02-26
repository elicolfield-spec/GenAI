import os
import telebot
import requests
import random
from threading import Thread
from flask import Flask

# --- БЛОК ВЕБ-СЕРВЕРА ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    # Render передает порт в переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- БЛОК БОТА ---
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Я ИИ-Художник!**\n\n"
        "Напиши `/draw` и описание картинки.\n"
        "**Пример:** `/draw giant robot in forest`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['draw'])
def draw_image(message):
    prompt = message.text.replace('/draw', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Введи описание после команды /draw")
        return

    status_msg = bot.reply_to(message, "🎨 Рисую... Это займет около 15 секунд.")
    
    # Кодируем текст и создаем ссылку
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 999999)
    
    # Ссылка на генератор (используем Flux модель без логотипа)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"

    try:
        response = requests.get(image_url, timeout=60)
        
        if response.status_code == 200 and len(response.content) > 5000:
            bot.send_photo(
                message.chat.id, 
                response.content, 
                caption=f"✅ Запрос: {prompt}"
            )
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ Ошибка: Сервер вернул пустой файл. Попробуй другой запрос.", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка генерации: {e}", message.chat.id, status_msg.message_id)

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запускаем веб-сервер в фоновом потоке
    server_thread = Thread(target=run_web_server)
    server_thread.start()
    
    print("--- Бот запущен ---")
    bot.infinity_polling(skip_pending=True)
