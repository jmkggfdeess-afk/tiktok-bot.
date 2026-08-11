import os
import requests
import telebot
from flask import Flask
from threading import Thread

# سيرفر وهمي لإرضاء Render وفتح المنفذ
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# إعدادات البوت والـ API
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

    msg = bot.reply_to(message, "⏳ جاري جلب الفيديو بدون علامة مائية...")

    try:
        # فك الرابط المختصر للحصول على الرابط الكامل
        res = requests.head(url_text, allow_redirects=True, timeout=5)
        full_url = res.url

        api_url = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/index"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com"
        }
        querystring = {"url": full_url}

        response = requests.get(api_url, headers=headers, params=querystring, timeout=12)
        data = response.json()

        # استخراج رابط الفيديو المباشر بمختلف صيغ الاستجابة المحتملة
        video_url = None
        if isinstance(data, dict):
            video_url = data.get("video") or data.get("download_url") or data.get("no_watermark")
            if isinstance(video_url, list) and len(video_url) > 0:
                video_url = video_url[0]

        if video_url and str(video_url).startswith("http"):
            bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل بنجاح بدون علامة مائية!")
        else:
            bot.edit_message_text("❌ تعذر استخراج الفيديو، تأكد من صحة الرابط أو جرب رابطاً آخر.", chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        bot.edit_message_text("⚠️ حدث خطأ أثناء الاتصال بالخادم، حاول مجدداً لاحقاً.", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
