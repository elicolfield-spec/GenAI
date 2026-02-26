import os
import telebot
import requests
import time
import random
from threading import Thread
from flask import Flask
from deep_translator import GoogleTranslator

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы не засыпал) ---
app = Flask('')
@app.route('/')
def home(): 
    return "Третий Бот: Статус LIVE"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- НАСТРОЙКИ БОТА ---
TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ВАРИАНТ А: Самая стабильная база SDXL
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@bot.message_handler(commands=['start', 'help'])
def start(message):
    welcome_text = (
        "👋 **Я твой Третий Бот!**\n\n"
        "Я рисую картинки по твоему описанию.\n"
        "Можешь писать на **русском** — я сам переведу.\n\n"
        "Команда: `/draw ваш запрос`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['draw'])
def draw(message):
    # Убираем команду /draw из текста
    user_prompt = message.text.replace('/draw', '').strip()
    
    if not user_prompt:
        bot.reply_to(message, "⚠️ Пожалуйста, напиши описание после команды /draw\nПример: `/draw рыжий кот в очках`", parse_mode='Markdown')
        return

    # Информируем пользователя о начале работы
    msg = bot.reply_to(message, "⚙️ Обрабатываю запрос...")

    try:
        # 1. АВТОПЕРЕВОД (с любого языка на английский)
        translated = GoogleTranslator(source='auto', target='en').translate(user_prompt)
        bot.edit_message_text(f"🎨 **Перевод:** _{translated}_\n⏳ Генерирую картинку...", 
                              message.chat.id, msg.message_id, parse_mode='Markdown')

        # 2. ПОДГОТОВКА ДАННЫХ ДЛЯ ИИ
        payload = {
            "inputs": translated,
            "options": {"wait_for_model": True} # Ждать, если модель не загружена
        }
        
        # 3. ЗАПРОС К HUGGING FACE
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            # Если всё успешно, отправляем фото
            bot.send_photo(
                message.chat.id, 
                response.content, 
                caption=f"✅ **Готово!**\n📝 Запрос: {user_prompt}",
                parse_mode='Markdown'
            )
            bot.delete_message(message.chat.id, msg.message_id)
        
        elif response.status_code == 503:
            # Если модель только просыпается
            bot.edit_message_text("⌛ Модель прогревается на сервере. Попробуй повторить через 20-30 секунд.", 
                                  message.chat.id, msg.message_id)
        
        else:
            # Другие ошибки (например, 410, 401 и т.д.)
            bot.edit_message_text(f"❌ Ошибка ИИ (Код: {response.status_code}).\nПопробуй изменить запрос или повторить позже.", 
                                  message.chat.id, msg.message_id)

    except Exception as e:
        print(f"Ошибка в блоке draw: {e}")
        bot.edit_message_text(f"❌ Произошла ошибка: {e}", message.chat.id, msg.message_id)

# --- ЗАПУСК ВСЕЙ СИСТЕМЫ ---
if __name__ == "__main__":
    # Запуск Flask в отдельном потоке
    Thread(target=run_web_server).start()
    
    print("--- ТРЕТИЙ БОТ ЗАПУЩЕН ---")
    # Infinity polling с игнорированием старых сообщений
    bot.infinity_polling(skip_pending=True)
