import asyncio
import logging
import random
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7344257430:AAFgBLSeVOzLl0IYr1xWD3FY-2lRyz9g5OU"
ADMIN_ID = 6037220399

db_path = "bot_database.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# خادم ويب لإرضاء موقع Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                referrals_count INTEGER DEFAULT 0,
                last_daily TEXT DEFAULT '0',
                last_spin TEXT DEFAULT '0'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                code TEXT PRIMARY KEY,
                reward INTEGER
            )
        """)
        await db.commit()

# واجهة رئيسية مرتبة بشكل أنيق غير مزدحم (شبكية)
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 حسابي", callback_data="my_balance")
    builder.button(text="🔗 رابط الدعوة", callback_data="get_ref_link")
    builder.button(text="🎡 عجلة الحظ", callback_data="spin_wheel")
    builder.button(text="🎁 الهدية اليومية", callback_data="daily_bonus")
    builder.button(text="🎯 لعبة التخمين", callback_data="guess_game")
    builder.button(text="🏆 المتصدرين", callback_data="top_users")
    builder.button(text="🎟️ كوبون هدية", callback_data="enter_coupon")
    builder.button(text="💸 سحب الأرباح", callback_data="request_withdraw")
    builder.adjust(2, 2, 2, 2) # ترتيب كل زرين بجانب بعضهما لعدم وجود تلوث بصري
    return builder.as_markup()

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
                                    "🔥 **انضم شخص جديد عبر رابط الدعوة الخاص بك!**\n💰 تم إضافة 100 نقطة إلى رصيدك.",
                                    parse_mode="Markdown"
                                )
                            except: pass
                except ValueError: pass

    welcome_msg = (
        f"🌟 **أهلاً بك عزيزي {name}**\n\n"
        "🤖 منصتك الذكية لجمع النقاط والأرباح بسهولة.\n"
        "اختر ما تحب فعله من القائمة أدناه بكل مرتب وجذاب:"
    )
    
    await message.answer(welcome_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    home_msg = "🎛️ **القائمة الرئيسية:**\nاختر أحد الخيارات أدناه:"
    await callback.message.edit_text(home_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance, referrals_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance, refs = row if row else (0, 0)
            
    remaining = max(0, 10000 - balance)
    
    balance_msg = (
        f"📊 **حسابك والإحصائيات:**\n\n"
        f"💰 رصيدك الحالي: `{balance}` نقطة\n"
        f"👥 عدد الدعوات: `{refs}` شخص\n"
        f"🎯 المتبقي للسحب (10,000): `{remaining}` نقطة"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(balance_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "get_ref_link")
async def get_ref_link(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    link_msg = (
        f"🔗 **رابط الدعوة الخاص بك:**\n\n"
        f"`{ref_link}`\n\n"
        "انسخه وشاركْه مع أصدقائك واربح 100 نقطة عن كل عضو حقيقي!"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(link_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

# --- عجلة الحظ الاحترافية ---
@dp.callback_query(F.data == "spin_wheel")
async def spin_wheel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    import time
    today = time.strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT last_spin FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_spin = row[0] if row else '0'
            
        if last_spin == today:
            await callback.answer("⏳ لقد استخدمت عجلة الحظ اليوم! عد غداً.", show_alert=True)
            return
            
        # خيارات حقيقية لعجلة الحظ
        rewards = [10, 25, 50, 100]
        reward = random.choice(rewards)
        
        await db.execute("UPDATE users SET balance = balance + ?, last_spin = ? WHERE user_id = ?", (reward, today, user_id))
        await db.commit()
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    
    await callback.message.edit_text(
        f"🎡 **تم دوران عجلة الحظ بنجاح!**\n\n"
        f"🎉 توقفت العجلة عند الفائز وحصلت على: `+{reward} نقطة` أضيفت لرصيدك.",
        parse_mode="Markdown", reply_markup=back_btn.as_markup()
    )

# --- الهدية اليومية (ثابتة 20 نقطة) ---
@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    import time
    today = time.strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_daily = row[0] if row else '0'
            
        if last_daily == today:
            await callback.answer("⏳ لقد استلمت هدديتك اليومية مسبقاً (20 نقطة)، انتظر غداً!", show_alert=True)
            return
            
        reward = 20  # القيمة الثابتة كما طلبته
        await db.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (reward, today, user_id))
        await db.commit()
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    
    await callback.message.edit_text(
        f"🎁 **هدية اليوم المجانية!**\n\n"
        f"✨ حصلت على `+{reward} نقطة` لليوم بنجاح.",
        parse_mode="Markdown", reply_markup=back_btn.as_markup()
    )

# --- لعبة تخمين الرقم الحقيقية والتفاعلية ---
@dp.callback_query(F.data == "guess_game")
async def guess_game_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣ 1", callback_data="guess_1")
    builder.button(text="2️⃣ 2", callback_data="guess_2")
    builder.button(text="3️⃣ 3", callback_data="guess_3")
    builder.button(text="4️⃣ 4", callback_data="guess_4")
    builder.button(text="5️⃣ 5", callback_data="guess_5")
    builder.button(text="🔙 رجوع", callback_data="back_home")
    builder.adjust(3, 2, 1)
    
    await callback.message.edit_text(
        "🎯 **لعبة تخمين الرقم الذكية:**\n\n"
        "اختر رقماً صحيحاً من `1` إلى `5`.\n"
        "إذا اخترت الرقم الرابح ستربح **50 نقطة** فوراً!",
        parse_mode="Markdown", reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("guess_"))
async def process_guess(callback: types.CallbackQuery):
    user_choice = int(callback.data.split("_")[1])
    winning_number = random.randint(1, 5) # رقم عشوائي حقيقي يخمنه النظام
    user_id = callback.from_user.id
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🎮 حاول مجدداً", callback_data="guess_game")
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    back_btn.adjust(1)
    
    if user_choice == winning_number:
        reward = 50
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            await db.commit()
        await callback.message.edit_text(
            f"🏆 **ممتاز جداً! اخترت الرقم الصحيح ({winning_number})**\n\n"
            f"🎁 مبروك، لقد ربحت `+{reward} نقطة`!",
            parse_mode="Markdown", reply_markup=back_btn.as_markup()
        )
    else:
        await callback.message.edit_text(
            f"❌ **للأسف خطأ!**\n\n"
            f"• اختيارك: `{user_choice}`\n"
            f"• الرقم الفائز كان: `{winning_number}`\n\n"
            "حاول مرة أخرى لتحظى بفرصة الفوز!",
            parse_mode="Markdown", reply_markup=back_btn.as_markup()
        )

@dp.callback_query(F.data == "top_users")
async def top_users(callback: types.CallbackQuery):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT user_id, referrals_count, balance FROM users ORDER BY referrals_count DESC LIMIT 5") as cursor:
            rows = await cursor.fetchall()
            
    top_text = "🏆 **قائمة أبطال الدعوات:**\n\n"
    for idx, row in enumerate(rows, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
        top_text += f"{medal} العضو `...{str(row[0])[-4:]}` ⟸ الدعوات: **{row[1]}** | الرصيد: **{row[2]}**\n"
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(top_text, parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "enter_coupon")
async def enter_coupon_prompt(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎟️ **أرسل الكوبون الآن:**\n\n"
        "قم بإرسال كود الهدية في رسالة جديدة لكي تتم إضافة المكافأة لرصيدك.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup()
    )

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_messages(message: types.Message):
    code = message.text.strip()
    user_id = message.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT reward FROM coupons WHERE code = ?", (code,)) as cursor:
            coupon = await cursor.fetchone()
        if coupon:
            reward = coupon[0]
            await db.execute("DELETE FROM coupons WHERE code = ?", (code,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            await db.commit()
            await message.answer(f"🎉 **مبروك! تم تفعيل الكوبون بنجاح**\n🎁 حصلت على `+{reward} نقطة` لرصيدك.")

@dp.message(Command("addcoupon"))
async def add_coupon(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.reply("استخدم الأمر هكذا:\n`/addcoupon الكود القيمة`", parse_mode="Markdown")
        return
    code, reward = args[1], int(args[2])
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT OR REPLACE INTO coupons (code, reward) VALUES (?, ?)", (code, reward))
        await db.commit()
    await message.reply(f"✅ تم إنشاء الكوبون `{code}` بقيمة `{reward}` نقطة بنجاح!", parse_mode="Markdown")

@dp.callback_query(F.data == "request_withdraw")
async def request_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0
            
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")

    if balance < 10000:
        await callback.answer("❌ عذراً، رصيدك لم يبلغ الحد الأدنى للسحب (10,000 نقطة).", show_alert=True)
    else:
        success_msg = "✅ **تم تقديم طلب السحب بنجاح!** سيتم مراجعة طلبك وتحويل الأرباح قريباً."
        await callback.message.edit_text(success_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())
        await bot.send_message(ADMIN_ID, f"🔔 **طلب سحب جديد!**\n- آيدي المستخدم: `{user_id}`\n- الرصيد: `{balance}` نقطة", parse_mode="Markdown")

async def main():
    await init_db()
    await asyncio.gather(web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
