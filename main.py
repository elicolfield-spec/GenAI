import os
import telebot
import requests
from telebot import types

# Берем токен из переменных окружения (настроим в Render)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот-художник. Напиши /draw и свой запрос (на английском), чтобы я что-то нарисовал.\nПример: /draw cyberpunk cat")

@bot.message_handler(commands=['draw'])
def draw_image(message):
    # Извлекаем запрос пользователя
    prompt = message.text.replace('/draw', '').strip()
    
    if not prompt:
        bot.reply_to(message, "Ты не ввел описание! Напиши, например: /draw space landscape")
        return

    msg = bot.reply_to(message, "🎨 Рисую... Это займет около 10-20 секунд.")
    
    # Формируем ссылку для Pollinations.ai
    # Заменяем пробелы на %20 для корректной ссылки
    encoded_prompt = requests.utils.quote(prompt)
    image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&nologo=true"

    try:
        # Отправляем фото напрямую через URL
        bot.send_photo(message.chat.id, image_url, caption=f"Вот твой результат по запросу: {prompt}")
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"Произошла ошибка при генерации: {e}", message.chat.id, msg.message_id)

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
