import os
import requests
import telebot
from flask import Flask
from threading import Thread
from yt_dlp import YoutubeDL

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is online!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = "7344257430:AAGnlTxGH_AZ0B9S7bNX6ZRg8H02XU4lSuM"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك! أرسل لي أي رابط فيديو من تيك توك وسأقوم بتحميله لك فوراً 🎬")

@bot.message_handler(func=lambda message: True)
def download_tiktok(message):
    url_text = message.text.strip()
    
    if "tiktok.com" not in url_text:
        bot.reply_to(message, "⚠️ من فضلك أرسل رابط تيك توك صحيح.")
        return

    msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو...")

    # الطرق المعتمدة للتحميل لتفادي حظر السيرفرات
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    try:
        # المحاولة الأولى: yt-dlp محاكي للمتصفح
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_text])

        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video, caption="✅ تم التحميل بنجاح!")
            os.remove('video.mp4')
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            return
    except Exception:
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')

    # المحاولة الثانية (الخيار الاحتياطي في حال حظر تيك توك للسيرفر):
    try:
        api_res = requests.get(f"https://api.tiklydown.eu.org/api/download?url={url_text}", timeout=10).json()
        video_url = api_res.get("video", {}).get("noWatermark") or api_res.get("video", {}).get("watermark")
        
        if video_url:
            bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل بنجاح!")
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            return
    except Exception:
        pass

    bot.edit_message_text("❌ تعذر تحميل هذا الفيديو حالياً، جرب إرسال الرابط مرة أخرى.", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
