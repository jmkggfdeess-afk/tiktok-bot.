import os
import telebot
from flask import Flask
from threading import Thread
from yt_dlp import YoutubeDL

# سيرفر وهمي لإبقاء الخدمة نشطة على Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# توكن البوت الخاص بك
TELEGRAM_TOKEN = "7344257430:AAGnlTxGH_AZ0B9S7bNX6ZRg8H02XU4lSuM"
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

    msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو بدون علامة مائية...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # تحميل الفيديو إلى السيرفر مؤقتاً
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_text])

        # إرسال الفيديو للمستخدم
        with open('video.mp4', 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ تم التحميل بنجاح بدون علامة مائية!")

        # مسح الملف من السيرفر بعد الإرسال
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')
            
        bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')
        bot.edit_message_text("❌ تعذر تحميل الفيديو، تأكد من أن الرابط يعمل والحساب ليس خاصاً.", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
