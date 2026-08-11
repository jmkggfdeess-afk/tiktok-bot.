import os
import requests
import telebot
from flask import Flask
from threading import Thread

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
    bot.reply_to(message, "👋 أهلاً بك! أرسل لي أي رابط فيديو من تيك توك وسأقوم بتحميله لك فوراً وبدون علامة مائية 🎬")

@bot.message_handler(func=lambda message: True)
def download_tiktok(message):
    url_text = message.text.strip()
    
    if "tiktok.com" not in url_text:
        bot.reply_to(message, "⚠️ من فضلك أرسل رابط تيك توك صحيح.")
        return

    msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو بدون علامة مائية...")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })

    try:
        # جلب رابط الفيديو المباشر عن طريق POST لتجاوز القيود
        response = session.post(
            "https://www.tikwm.com/api/",
            data={'url': url_text, 'count': 12, 'cursor': 0, 'web': 1, 'hd': 1},
            timeout=20
        ).json()

        if response.get("code") == 0 and "data" in response:
            video_data = response["data"]
            play_url = video_data.get("hdplay") or video_data.get("play") or video_data.get("wmplay")
            
            if play_url:
                if not play_url.startswith("http"):
                    play_url = "https://www.tikwm.com" + play_url

                bot.send_video(
                    message.chat.id, 
                    play_url, 
                    caption="✅ تم التحميل بنجاح بدون علامة مائية!"
                )
                bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
                return

        bot.edit_message_text(
            "❌ تعذر استخراج الفيديو. تأكد من أن الرابط يعمل والحساب ليس خاصاً.", 
            chat_id=message.chat.id, 
            message_id=msg.message_id
        )

    except Exception:
        bot.edit_message_text(
            "❌ تعذر الاتصال بالسيرفر حالياً، يرجى المحاولة مرة أخرى.", 
            chat_id=message.chat.id, 
            message_id=msg.message_id
        )

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
