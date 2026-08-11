import os
import requests
import telebot
from flask import Flask
from threading import Thread

# سيرفر وهمي لإبقاء الخدمة نشطة على Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# توكن البوت
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

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # استخدام TikWM API لتخطي حماية وسيرفرات تيك توك مباشرة
        api_url = f"https://www.tikwm.com/api/?url={url_text}"
        response = requests.get(api_url, headers=headers, timeout=15).json()

        if response.get("code") == 0 and "data" in response:
            video_data = response["data"]
            # رابط الفيديو بدون علامة مائية
            play_url = video_data.get("play") or video_data.get("wmplay")
            
            if play_url:
                # إضافة السيرفر كمصدر للرابط عند الحاجة
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
            "❌ تعذر تحميل الفيديو. تأكد من أن الرابط صحيح وأن الحساب ليس خاصاً.", 
            chat_id=message.chat.id, 
            message_id=msg.message_id
        )

    except Exception as e:
        bot.edit_message_text(
            "⚠️ حدث خطأ في الاتصال، يرجى إعادة محاولة إرسال الرابط مرة أخرى.", 
            chat_id=message.chat.id, 
            message_id=msg.message_id
        )

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
