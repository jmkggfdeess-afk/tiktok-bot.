import asyncio
import logging
import random
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

# لوحة التحكم الرئيسية مع جميع الميزات
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 حسابي وإحصائياتي", callback_data="my_balance")
    builder.button(text="🔗 رابط الدعوة الخاص بي", callback_data="get_ref_link")
    builder.button(text="🎡 عجلة الحظ اليومية", callback_data="spin_wheel")
    builder.button(text="🎁 الهدية اليومية", callback_data="daily_bonus")
    builder.button(text="🎯 لعبة تخمين الرقم", callback_data="guess_game")
    builder.button(text="🏆 لوحة المتصدرين", callback_data="top_users")
    builder.button(text="🎟️ إدخال كوبون هدية", callback_data="enter_coupon")
    builder.button(text="💸 طلب سحب الأرباح", callback_data="request_withdraw")
    builder.adjust(1)
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
        f"🚀 **أهلاً بك عزيزي {name} في منصة الأرباح والألعاب الذكية!**\n\n"
        "⚡️ استمتع بالميزات الجديدة كلياً:\n"
        "• عجلة الحظ والهدية اليومية 🎡🎁\n"
        "• ألعاب حماسية لتضاعف نقاطك 🎯\n"
        "• منافسة الأبطال في لوحة المتصدرين 🏆"
    )
    
    await message.answer(welcome_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    home_msg = "🚀 **القائمة الرئيسية للبوت:**\nاختر ما تحب فعله أدناه:"
    await callback.message.edit_text(home_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- 1. حسابي وإحصائياتي ---
@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance, referrals_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance, refs = row if row else (0, 0)
            
    remaining = max(0, 10000 - balance)
    
    balance_msg = (
        f"📊 **لوحة إحصائياتك الشخصية:**\n\n"
        f"💰 رصيدك الحالي: `{balance}` نقطة\n"
        f"👥 عدد الدعوات: `{refs}` شخص\n"
        f"🎯 المتبقي للسحب (10,000): `{remaining}` نقطة"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")
    await callback.message.edit_text(balance_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

# --- 2. رابط الدعوة ---
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
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")
    await callback.message.edit_text(link_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

# --- 3. عجلة الحظ اليومية ---
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
            await callback.answer("⏳ لقد استخدمت عجلة الحظ اليوم! عد غداً لتجربة حظك من جديد.", show_alert=True)
            return
            
        # جائزة عشوائية
        reward = random.choice([25, 50, 100, 150, 200, 300])
        await db.execute("UPDATE users SET balance = balance + ?, last_spin = ? WHERE user_id = ?", (reward, today, user_id))
        await db.commit()
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")
    
    await callback.message.edit_text(
        f"🎡 **تهانينا! دارت عجلة الحظ بنجاح**\n\n"
        f"🎁 لقد ربحت جائزة قدرها: `+{reward} نقطة` أضيفت لرصيدك فوراً!",
        parse_mode="Markdown", reply_markup=back_btn.as_markup()
    )

# --- 4. الهدية اليومية ---
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
            await callback.answer("⏳ لقد استلمت هدديتك اليومية مسبقاً، انتظر حتى الغد!", show_alert=True)
            return
            
        reward = 50  # هدية ثابتة أو تراكمية يومية
        await db.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (reward, today, user_id))
        await db.commit()
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")
    
    await callback.message.edit_text(
        f"🎁 **تم استلام الهدية اليومية بنجاح!**\n\n"
        f"✨ حصلت على `+{reward} نقطة` مجانية لهذا اليوم.",
        parse_mode="Markdown", reply_markup=back_btn.as_markup()
    )

# --- 5. لعبة تخمين الرقم ---
@dp.callback_query(F.data == "guess_game")
async def guess_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # لعبة سريعة: تخمين رقم بين 1 و 3
    chosen = random.randint(1, 3)
    user_guess = random.randint(1, 3) # محاكاة تخمين أو ربح سريع
    
    if user_guess == chosen:
        win_reward = 150
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (win_reward, user_id))
            await db.commit()
        msg = f"🎯 **حظ رائع!**\nاخترت الرقم الصحيح `{chosen}` وربحت `+{win_reward} نقطة` إضافية!"
    else:
        msg = f"🎯 **حاول مرة أخرى!**\nالرقم الصحيح كان `{chosen}` ولم يحالفك الحظ هذه المرة."
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🎮 العب مجدداً", callback_data="guess_game")
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")
    back_btn.adjust(1)
    
    await callback.message.edit_text(msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

# --- 6. لوحة المتصدرين ---
@dp.callback_query(F.data == "top_users")
async def top_users(callback: types.CallbackQuery):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT user_id, referrals_count, balance FROM users ORDER BY referrals_count DESC LIMIT 5") as cursor:
            rows = await cursor.fetchall()
            
    top_text = "🏆 **قائمة أبطال الدعوات والمتصدرين:**\n\n"
    for idx, row in enumerate(rows, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
        top_text += f"{medal} العضو `...{str(row[0])[-4:]}` ⟸ عدد الدعوات: **{row[1]}** | الرصيد: **{row[2]}**\n"
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")
    await callback.message.edit_text(top_text, parse_mode="Markdown", reply_markup=back_btn.as_markup())

# --- 7. نظام الكوبونات (للزوار والمستخدمين) ---
@dp.callback_query(F.data == "enter_coupon")
async def enter_coupon_prompt(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎟️ **أرسل الكوبون الآن:**\n\n"
        "قم بإرسال كود الهدية في رسالة جديدة (مثلاً `MOHA2026`) لكي تتم إضافة المكافأة إلى رصيدك فوراً.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup()
    )

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_messages(message: types.Message):
    # إذا أرسل المستخدم كود كوبون
    code = message.text.strip()
    user_id = message.from_user.id
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT reward FROM coupons WHERE code = ?", (code,)) as cursor:
            coupon = await cursor.fetchone()
            
        if coupon:
            reward = coupon[0]
            # حذف الكوبون لكي لا يُستعمل مرتين (أو يمكن إبقاؤه حسب رغبتك)
            await db.execute("DELETE FROM coupons WHERE code = ?", (code,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            await db.commit()
            await message.answer(f"🎉 **مبروك! تم تفعيل الكوبون بنجاح**\n🎁 حصلت على `+{reward} نقطة` لرصيدك.")
        else:
            # إذا كتب رسالة عادية وليست كوبون
            pass

# --- أمر خاص للأدمن لإنشاء كوبونات (مثال: /addcoupon MOHA 500) ---
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

# --- 8. سحب الأرباح ---
@dp.callback_query(F.data == "request_withdraw")
async def request_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0
            
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع للقائمة الرئيسية", callback_data="back_home")

    if balance < 10000:
        await callback.answer("❌ عذراً، رصيدك لم يبلغ الحد الأدنى للسحب (10,000 نقطة).", show_alert=True)
    else:
        success_msg = "✅ **تم تقديم طلب السحب بنجاح!** سيتم مراجعة طلبك وتحويل الأرباح قريباً."
        await callback.message.edit_text(success_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())
        await bot.send_message(ADMIN_ID, f"🔔 **طلب سحب جديد!**\n- آيدي المستخدم: `{user_id}`\n- الرصيد: `{balance}` نقطة", parse_mode="Markdown")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
