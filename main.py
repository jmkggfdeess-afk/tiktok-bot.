import os
import requests
import telebot
from flask import Flask
from threading import Thread

# إنشاء سيرفر وهمي لفتح المنفذ المطلوب على Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# إعداد البوت
TELEGRAM_TOKEN = "7344257430:AAGnlTxGH_AZ0B9S7bNX6ZRg8H02XU4lSuM"
RAPIDAPI_KEY = "30481209aamsh58e0e818f3fa36ep17b90djsnc143a17a1931"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك! أرسل لي أي رابط فيديو من تيك توك وسأقوم بتحميله لك بدون علامة مائية فوراً 🎬")

@bot.message_handler(func=lambda message: True)
def download_tiktok(message):
    url_text = message.text.strip()
    
    if "tiktok.com" not in url_text:
        bot.reply_to(message, "⚠️ من فضلك أرسل رابط تيك توك صحيح.")
        return

    bot.reply_to(message, "⏳ جاري جلب الفيديو بدون علامة مائية...")

    api_url = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/index"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com"
    }
    querystring = {"url": url_text}

    try:
        response = requests.get(api_url, headers=headers, params=querystring, timeout=10)
        data = response.json()
        
        video_url = data.get("video", [None])[0] or data.get("download_url")

        if video_url:
            bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل بنجاح بدون علامة مائية!")
        else:
            bot.reply_to(message, "❌ تعذر جلب الفيديو، تأكد من أن الحساب ليس خاصاً.")
    except Exception as e:
        bot.reply_to(message, "⚠️ حدث خطأ أثناء الاتصال بالسيرفر، حاول مجدداً.")

# تشغيل السيرفر والبوت معاً
if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
