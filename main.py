import os
import telebot
import requests
import random
from telebot import types

# 1. Настройка токена (берется из настроек Render)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Я бот-генератор изображений!**\n\n"
        "Чтобы я нарисовал что-то, используй команду /draw.\n"
        "**Пример:** `/draw futuristic city, sunset, 4k`\n\n"
        "⚠️ *Совет: Лучше писать запросы на английском для более точного результата.*"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['draw'])
def draw_image(message):
    # Извлекаем текст после команды /draw
    prompt = message.text.replace('/draw', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Ты не ввел описание! Напиши что-то после команды /draw.")
        return

    # Отправляем сообщение о начале работы
    status_msg = bot.reply_to(message, "🎨 Нейросеть начала работу... Пожалуйста, подожди 10-20 секунд.")
    
    # 2. ПОДГОТОВКА ССЫЛКИ
    # Кодируем текст, чтобы он корректно передавался в URL (заменяем пробелы и спецсимволы)
    encoded_prompt = requests.utils.quote(prompt)
    
    # Генерируем случайное число (seed), чтобы каждая картинка была уникальной
    seed = random.randint(1, 999999)
    
    # Используем самое стабильное зеркало Pollinations с моделью FLUX
    # nologo=true убирает логотип, model=flux дает лучшее качество
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true&enhance=false"

    try:
        # 3. ПОЛУЧЕНИЕ КАРТИНКИ
        response = requests.get(image_url, timeout=60)
        
        if response.status_code == 200:
            # Проверяем, не слишком ли маленький файл (иногда ошибки весят мало)
            if len(response.content) < 5000:
                raise Exception("Сервер вернул пустую картинку или логотип.")

            # Отправляем фото пользователю
            bot.send_photo(
                message.chat.id, 
                response.content, 
                caption=f"✅ **Результат по запросу:**\n_{prompt}_",
                parse_mode='Markdown'
            )
            # Удаляем сообщение о загрузке
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ Сервер нейросети ответил ошибкой: {response.status_code}", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.edit_message_text("❌ Произошла ошибка при генерации. Попробуй изменить запрос или повторить позже.", message.chat.id, status_msg.message_id)

# 4. ЗАПУСК БОТА
if __name__ == "__main__":
    print("--- Бот запущен и готов к работе ---")
    # Параметр skip_pending=True позволяет боту игнорировать сообщения, присланные, пока он был выключен
    bot.infinity_polling(skip_pending=True)
