import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# التوكن والرقم الخاص بك
TOKEN = "7344257430:AAFgBLSeVOzLl0IYr1xWD3FY-2lRyz9g5OU"
ADMIN_ID = 6037220399  # تم وضع الآيدي الخاص بك هنا

db_path = "bot_database.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                referrals_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
        if not user:
            await db.execute("INSERT INTO users (user_id, balance, referrals_count) VALUES (?, 0, 0)", (user_id,))
            await db.commit()
            if len(args) > 1:
                try:
                    referrer_id = int(args[1])
                    if referrer_id != user_id:
                        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,)) as cursor:
                            ref_exists = await cursor.fetchone()
                        if ref_exists:
                            await db.execute("UPDATE users SET balance = balance + 100, referrals_count = referrals_count + 1 WHERE user_id = ?", (referrer_id,))
                            await db.commit()
                            try: await bot.send_message(referrer_id, "🎉 انضم شخص جديد عبر رابط الدعوة الخاص بك! تم إضافة 100 نقطة إلى رصيدك.")
                            except: pass
                except ValueError: pass

    builder = InlineKeyboardBuilder()
    builder.button(text="👤 رصيدي وإحصائياتي", callback_data="my_balance")
    builder.button(text="🔗 رابط الدعوة الخاص بي", callback_data="get_ref_link")
    builder.button(text="💸 طلب سحب الأرباح", callback_data="request_withdraw")
    builder.adjust(1)
    await message.answer("مرحباً بك في بوت الأرباح! قم بدعوة أصدقائك واربح 100 نقطة عن كل شخص.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance, referrals_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance, refs = row if row else (0, 0)
    await callback.message.edit_text(f"📊 رصيدك: {balance} نقطة\n👥 دعوت: {refs} شخص", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 رجوع", callback_data="back_home")]]))

@dp.callback_query(F.data == "get_ref_link")
async def get_ref_link(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    await callback.message.edit_text(f"🔗 رابط الدعوة الخاص بك:\n`{ref_link}`", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 رجوع", callback_data="back_home")]]))

@dp.callback_query(F.data == "request_withdraw")
async def request_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0
    if balance < 10000:
        await callback.answer("عذراً، يجب أن تصل لـ 10,000 نقطة للسحب.", show_alert=True)
    else:
        await callback.message.edit_text("✅ تم إرسال طلب السحب للإدارة.", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 رجوع", callback_data="back_home")]]))
        await bot.send_message(ADMIN_ID, f"🔔 طلب سحب جديد من: {user_id}")

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 رصيدي وإحصائياتي", callback_data="my_balance")
    builder.button(text="🔗 رابط الدعوة الخاص بي", callback_data="get_ref_link")
    builder.button(text="💸 طلب سحب الأرباح", callback_data="request_withdraw")
    builder.adjust(1)
    await callback.message.edit_text("القائمة الرئيسية:", reply_markup=builder.as_markup())

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
