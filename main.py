import os
import telebot
import requests
import random
from threading import Thread
from flask import Flask

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- НАСТРОЙКА БОТА ---
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Заголовки, чтобы сервера ИИ не блокировали нас как бота
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🤖 **Бот-художник готов!**\nНапиши `/draw` и текст на английском.\nПример: `/draw magic forest, cinematic light`", parse_mode='Markdown')

@bot.message_handler(commands=['draw'])
def draw_image(message):
    prompt = message.text.replace('/draw', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Введите описание!")
        return

    status_msg = bot.reply_to(message, "🎨 Рисую... Пожалуйста, подожди.")
    
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 1000000)

    # Список разных ссылок-зеркал для надежности
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux",
        f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=turbo&nologo=true",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true"
    ]

    success = False
    for url in urls:
        try:
            # Пытаемся получить изображение
            response = requests.get(url, headers=HEADERS, timeout=40)
            
            if response.status_code == 200 and len(response.content) > 15000:
                bot.send_photo(
                    message.chat.id, 
                    response.content, 
                    caption=f"✅ Запрос: {prompt}"
                )
                bot.delete_message(message.chat.id, status_msg.message_id)
                success = True
                break # Если получилось, выходим из цикла
            else:
                continue # Если этот сервер не ответил, пробуем следующий
        except Exception as e:
            print(f"Ошибка сервера: {e}")
            continue

    if not success:
        bot.edit_message_text("❌ Все серверы ИИ сейчас перегружены. Попробуй через минуту или используй другой запрос.", message.chat.id, status_msg.message_id)

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запуск веб-сервера в фоне
    Thread(target=run_web_server).start()
    
    print("--- Бот запущен ---")
    bot.infinity_polling(skip_pending=True)
