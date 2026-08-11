import asyncio
import logging
import time
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7344257430:AAFgBLSeVOzLl0IYr1xWD3FY-2lRyz9g5OU"
ADMIN_ID = 6037220399
RENDER_URL = "https://tiktok-bot-1-qesh.onrender.com"

db_path = "bot_database.db"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- واجهة التطبيق المصغر (Mini App) للتعدين ---
async def mini_app_page(request):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>منصة التعدين</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{ background: #0b0f19; color: #fff; text-align: center; font-family: sans-serif; padding: 20px; }}
            .card {{ background: #161e2e; padding: 20px; border-radius: 20px; max-width: 350px; margin: auto; border: 1px solid #2d3748; }}
            .balance {{ font-size: 32px; color: #38bdf8; font-weight: bold; margin: 20px 0; }}
            .btn-claim {{ background: #22c55e; color: white; border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>⛏️ التعدين المباشر</h2>
            <div class="balance" id="mined">0.0000</div>
            <button class="btn-claim" onclick="alert('تم تجميع الأرباح بنجاح!')">💰 جمع الأرباح</button>
        </div>
        <script>
            let mined = 0;
            setInterval(() => {{ mined += 0.001; document.getElementById('mined').innerText = mined.toFixed(4); }}, 100);
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- خادم الويب ---
async def web_server():
    app = web.Application()
    app.add_routes([web.get("/app", mini_app_page)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

# --- القائمة الرئيسية النظيفة ---
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⛏️ فتح منصة التعدين الحية (Mini App)", web_app=types.WebAppInfo(url=f"{RENDER_URL}/app"))
    builder.button(text="💰 محفظتي", callback_data="my_balance")
    builder.button(text="🚀 زيادة السرعة (الإحالات)", callback_data="get_ref_link")
    builder.button(text="📋 المهام اليومية", callback_data="daily_tasks")
    builder.button(text="🏆 المتصدرين", callback_data="top_users")
    builder.adjust(1, 2, 2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(f"🌟 أهلاً بك يا {message.from_user.first_name} في منصة التعدين الذكية.\n\nاستخدم الأزرار أدناه للتحكم في حسابك وإدارته.", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    await callback.message.edit_text("🎛️ القائمة الرئيسية:", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    await callback.message.edit_text("💰 رصيدك الحالي: 0 نقطة.\nاستمر في التعدين لزيادة أرباحك!", reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup())

@dp.callback_query(F.data == "get_ref_link")
async def get_ref_link(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    await callback.message.edit_text(f"🔗 رابط دعوتك لزيادة السرعة:\n`https://t.me/{bot_info.username}?start={callback.from_user.id}`", parse_mode="Markdown", reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup())

@dp.callback_query(F.data == "daily_tasks")
async def daily_tasks(callback: types.CallbackQuery):
    tasks_text = (
        "📋 **قائمة المهام المتاحة:**\n\n"
        "1️⃣ انضم إلى قناة التليجرام الرسمية `[+500 نقطة]`\n"
        "2️⃣ تابع حساب المنصة `[+300 نقطة]`\n\n"
        "💡 اضغط على المهمة لتنفيذها وجمع مكافأتك!"
    )
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(tasks_text, parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "top_users")
async def top_users(callback: types.CallbackQuery):
    await callback.message.edit_text("🏆 قائمة المتصدرين قيد التحديث...", reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup())

async def main():
    await asyncio.gather(web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
