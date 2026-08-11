import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7344257430:AAFgBLSeVOzLl0IYr1xWD3FY-2lRyz9g5OU"
ADMIN_ID = 6037220399

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
    name = message.from_user.first_name
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
                            try: 
                                await bot.send_message(
                                    referrer_id, 
                                    "<b>🔥 انضم شخص جديد عبر رابط الدعوة الخاص بك!</b>\n\n"
                                    "🎁 تم إضافة <b>+100 نقطة</b> إلى رصيدك بنجاح.",
                                    parse_mode="HTML"
                                )
                            except: pass
                except ValueError: pass

    builder = InlineKeyboardBuilder()
    builder.button(text="👤 ⟸ لـوحـة الحـسـاب والـإحـصـائـيـات", callback_data="my_balance")
    builder.button(text="🔗 ⟸ الحـصـول عـلـى رابـط الـدعـوة", callback_data="get_ref_link")
    builder.button(text="💸 ⟸ طـلـب سـحـب الـأربـاح", callback_data="request_withdraw")
    builder.adjust(1)
    
    welcome_msg = (
        f"<b>✨ أهلاً بك يا {name} في بوت الأرباح الرقمية!</b>\n\n"
        "<i>🤖 منصتك الذكية لجمع النقاط وتحويلها إلى أرباح حقيقية بكل سهولة.</i>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>طريقة العمل:</b>\n"
        "• قم بنسخ رابط الدعوة الخاص بك.\n"
        "• انشره بين أصدقائك وفي المجموعات.\n"
        "• اربح <b>100 نقطة</b> عن كل شخص ينضم عبر رابطك!\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    await message.answer(welcome_msg, parse_mode="HTML", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance, referrals_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance, refs = row if row else (0, 0)
            
    remaining = max(0, 10000 - balance)
    
    balance_msg = (
        "📊 <b>إحصائيات حسـابك الشخصي:</b>\n\n"
        f"💰 <b>الرصيد الحالي:</b> <code>{balance}</code> نقطة\n"
        f"👥 <b>الأصدقاء المدعوون:</b> <code>{refs}</code> شخص\n"
        f"🎯 <b>المتبقي للحد الأدنى (10,000):</b> <code>{remaining}</code> نقطة\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>استمر في دعوة أصدقائك للوصول إلى هدف السحب سريعاً!</i>"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 ⟸ العـودة للقـائـمة الـرئيـسـيـة", callback_data="back_home")
    
    await callback.message.edit_text(balance_msg, parse_mode="HTML", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "get_ref_link")
async def get_ref_link(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    link_msg = (
        "🔗 <b>رابط الدعوة الخاص بك:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        "📋 <i>قم بالضغط على الرابط أعلاه لنسخه تلقائياً، ثم شاركه مع أصدقائك واكسب المكافآت فوراً!</i>"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 ⟸ العـودة للقـائـمة الـرئيـسـيـة", callback_data="back_home")
    
    await callback.message.edit_text(link_msg, parse_mode="HTML", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "request_withdraw")
async def request_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0
            
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 ⟸ العـودة للقـائـمة الـرئيـسـيـة", callback_data="back_home")

    if balance < 10000:
        await callback.answer("❌ عذراً، رصيدك لم يبلغ الحد الأدنى للسحب (10,000 نقطة).", show_alert=True)
    else:
        success_msg = (
            "✅ <b>تم تقديم طلب السحب بنجاح!</b>\n\n"
            "⏳ <i>جاري مراجعة حسابك من قبل الإدارة وتحويل الأرباح في أقرب وقت. شكراً لثقتك بنا.</i>"
        )
        await callback.message.edit_text(success_msg, parse_mode="HTML", reply_markup=back_btn.as_מברوك if hasattr(back_btn, 'as_מברوك') else back_btn.as_markup())
        await bot.send_message(ADMIN_ID, f"🔔 <b>طلب سحب جديد!</b>\n👤 الآيدي: <code>{user_id}</code>\n💰 الرصيد: <code>{balance}</code> نقطة", parse_mode="HTML")

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 ⟸ لـوحـة الحـسـاب والـإحـصـائـيـات", callback_data="my_balance")
    builder.button(text="🔗 ⟸ الحـصـول عـلـى رابـط الـدعـوة", callback_data="get_ref_link")
    builder.button(text="💸 ⟸ طـلـب سـحـب الـأربـاح", callback_data="request_withdraw")
    builder.adjust(1)
    
    home_msg = "<b>✨ القائمة الرئيسية للبوت:</b>\n\n<i>اختر أحد الخيارات أدناه للمتابعة:</i>"
    await callback.message.edit_text(home_msg, parse_mode="HTML", reply_markup=builder.as_markup())

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
