import asyncio
import logging
import random
import time
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7344257430:AAFgBLSeVOzLl0IYr1xWD3FY-2lRyz9g5OU"
ADMIN_ID = 6037220399
RENDER_URL = "https://tiktok-bot-1-qesh.onrender.com"

db_path = "bot_database.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- تصميم واجهة التطبيق المصغر الحية مع نظام التعدين الديناميكي ---
async def mini_app_page(request):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>منصة التعدين والعملات</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {{
                background-color: #0b0f19;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                margin: 0;
                padding: 20px;
            }}
            .card {{
                background: #161e2e;
                border: 1px solid #2d3748;
                padding: 20px;
                border-radius: 20px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                max-width: 380px;
                margin: auto;
            }}
            .balance {{
                font-size: 32px;
                font-weight: bold;
                color: #38bdf8;
                margin: 15px 0;
            }}
            .speed-tag {{
                background: #1e293b;
                color: #4ade80;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 14px;
                display: inline-block;
                margin-bottom: 20px;
                border: 1px solid #334155;
            }}
            .btn-claim {{
                background: linear-gradient(135deg, #22c55e, #16a34a);
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 18px;
                border-radius: 12px;
                cursor: pointer;
                width: 100%;
                font-weight: bold;
                box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
                transition: transform 0.1s;
            }}
            .btn-claim:active {{
                transform: scale(0.96);
            }}
            .info-text {{
                font-size: 12px;
                color: #94a3b8;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>⛏️ تعدين النقاط</h2>
            <div class="speed-tag">🚀 السرعة: <span id="speed">0.010</span> نقطة/ثانية</div>
            
            <div style="font-size: 14px; color: #cbd5e1;">الرصيد المُعدَّن حالياً:</div>
            <div class="balance" id="mined">0.0000</div>

            <button class="btn-claim" onclick="claimTokens()">💰 جمع الأرباح إلى الحساب</button>
            
            <p class="info-text">💡 كل صديق تدعوه يزيد من سرعة تعدينك بنسبة +0.005 نقطة/ثانية بشكل دائم!</p>
        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let mined = 0.0000;
            let baseSpeed = 0.010; // السرعة الأساسية

            // تحديث العداد المباشر في الشاشة
            setInterval(() => {{
                mined += baseSpeed / 10;
                document.getElementById('mined').innerText = mined.toFixed(4);
            }}, 100);

            function claimTokens() {{
                if (mined < 0.1) {{
                    alert("⏳ انتظر حتى تتراكم بعض النقاط لتتمكن من جمعها!");
                    return;
                }}
                alert("✅ تم نقل " + mined.toFixed(2) + " نقطة إلى رصيدك الرئيسي بنجاح!");
                mined = 0;
            }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def web_server():
    app = web.Application()
    app.add_routes([
        web.get("/", lambda r: web.Response(text="Bot is running!")),
        web.get("/app", mini_app_page)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                balance INTEGER DEFAULT 0,
                referrals_count INTEGER DEFAULT 0,
                last_daily TEXT DEFAULT '0',
                last_spin TEXT DEFAULT '0',
                last_claim INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                code TEXT PRIMARY KEY,
                reward INTEGER
            )
        """)
        await db.commit()

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⛏️ فتح منصة التعدين الحية (Mini App)", web_app=types.WebAppInfo(url=f"{RENDER_URL}/app"))
    builder.button(text="👤 حسابي وسرعة التعدين", callback_data="my_balance")
    builder.button(text="🔗 زيادة السرعة (رابط الدعوة)", callback_data="get_ref_link")
    builder.button(text="🎡 عجلة الحظ", callback_data="spin_wheel")
    builder.button(text="🎁 الهدية اليومية", callback_data="daily_bonus")
    builder.button(text="🎯 لعبة التخمين", callback_data="guess_game")
    builder.button(text="🏆 المتصدرين", callback_data="top_users")
    builder.button(text="🎟️ كوبون هدية", callback_data="enter_coupon")
    builder.button(text="💸 سحب الأرباح", callback_data="request_withdraw")
    builder.button(text="📞 تواصل مع الدعم", callback_data="contact_support")
    builder.adjust(1, 2, 2, 2, 2, 1)
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
            await db.execute("INSERT INTO users (user_id, name, balance, referrals_count, last_claim) VALUES (?, ?, 0, 0, ?)", (user_id, name, int(time.time())))
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
                                    f"🔥 **انضم عضو جديد عبر رابطك ({name})!**\n⚡️ زادت سرعة التعدين لديك بمقدار `+0.005 نقطة/ثانية` وتلقيت 100 نقطة هدية!",
                                    parse_mode="Markdown"
                                )
                            except: pass
                except ValueError: pass
        else:
            await db.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
            await db.commit()

    welcome_msg = (
        f"🌟 **أهلاً بك يا {name} في بوت التعدين والأرباح**\n\n"
        "⚡️ اضغط على زر **(فتح منصة التعدين الحية)** لمشاهدة عداد التعدين بالوقت الفعلي وجمع أرباحك!"
    )
    
    await message.answer(welcome_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    home_msg = "🎛️ **القائمة الرئيسية للبوت:**"
    await callback.message.edit_text(home_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance, referrals_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance, refs = row if row else (0, 0)
            
    speed = 0.010 + (refs * 0.005)
    hourly_rate = speed * 3600
    
    balance_msg = (
        f"📊 **تفاصيل حسابك والتعدين:**\n\n"
        f"💰 الرصيد الحالي: `{balance}` نقطة\n"
        f"👥 عدد الدعوات (الإحالات): `{refs}` صديق\n"
        f"⚡️ سرعة التعدين: `{speed:.3f}` نقطة/ثانية\n"
        f"📈 الإنتاج اليومي التقريبي: `{hourly_rate * 24:.0f}` نقطة/يوم\n\n"
        "💡 **نصيحة:** قم بدعوة المزيد من الأصدقاء لرفع السرعة ومضاعفة الأرباح!"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(balance_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "get_ref_link")
async def get_ref_link(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    link_msg = (
        f"🚀 **رابط زيادة سرعة التعدين:**\n\n"
        f"`{ref_link}`\n\n"
        "📌 **مميزات الإحالة:**\n"
        "1️⃣ تحصل على +100 نقطة فورية.\n"
        "2️⃣ تزداد سرعة تعدينك بمقدار **+0.005 نقطة/ثانية** لكل صديق ينضم!"
    )
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(link_msg, parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "spin_wheel")
async def spin_wheel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    today = time.strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT last_spin FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_spin = row[0] if row else '0'
            
        if last_spin == today:
            await callback.answer("⏳ استخدمت عجلة الحظ اليوم، عد غداً!", show_alert=True)
            return
            
        reward = random.choice([10, 25, 50, 100])
        await db.execute("UPDATE users SET balance = balance + ?, last_spin = ? WHERE user_id = ?", (reward, today, user_id))
        await db.commit()
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(f"🎡 **عجلة الحظ:**\n\n🎉 حصلت على: `+{reward} نقطة`!", parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    today = time.strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_daily = row[0] if row else '0'
            
        if last_daily == today:
            await callback.answer("⏳ استلمت الهدية اليومية بالفعل!", show_alert=True)
            return
            
        await db.execute("UPDATE users SET balance = balance + 20, last_daily = ? WHERE user_id = ?", (today, user_id))
        await db.commit()
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text("🎁 **الهدية اليومية:**\n\n✨ تم إضافة `+20 نقطة` لحسابك!", parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "guess_game")
async def guess_game_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"🔢 {i}", callback_data=f"guess_{i}")
    builder.button(text="🔙 رجوع", callback_data="back_home")
    builder.adjust(3, 2, 1)
    
    await callback.message.edit_text(
        "🎯 **لعبة التخمين:**\nاختر رقماً من 1 إلى 5 (الفوز +100 / الخسارة -50)",
        parse_mode="Markdown", reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("guess_"))
async def process_guess(callback: types.CallbackQuery):
    user_choice = int(callback.data.split("_")[1])
    winning_number = random.randint(1, 5)
    user_id = callback.from_user.id
    
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🎮 إعادة المحاولة", callback_data="guess_game")
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            current_balance = row[0] if row else 0

        if user_choice == winning_number:
            await db.execute("UPDATE users SET balance = balance + 100 WHERE user_id = ?", (user_id,))
            await db.commit()
            await callback.message.edit_text(f"🏆 **إجابة صحيحة ({winning_number})!**\n🎉 ربحت `+100 نقطة`!", parse_mode="Markdown", reply_markup=back_btn.as_markup())
        else:
            new_balance = max(0, current_balance - 50)
            await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            await db.commit()
            await callback.message.edit_text(f"❌ **إجابة خاطئة!** الرقم الصحيح كان `{winning_number}`.\n🔴 تم خصم 50 نقطة.", parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "top_users")
async def top_users(callback: types.CallbackQuery):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT name, referrals_count, balance FROM users ORDER BY referrals_count DESC LIMIT 5") as cursor:
            rows = await cursor.fetchall()
            
    top_text = "🏆 **أبطال الإحالات والسرعة:**\n\n"
    for idx, row in enumerate(rows, 1):
        username = row[0] if row[0] else "مستخدم"
        top_text += f"#{idx} **{username}** ⟸ دعوات: `{row[1]}` | الرصيد: `{row[2]}`\n"
        
    back_btn = InlineKeyboardBuilder()
    back_btn.button(text="🔙 رجوع", callback_data="back_home")
    await callback.message.edit_text(top_text, parse_mode="Markdown", reply_markup=back_btn.as_markup())

@dp.callback_query(F.data == "contact_support")
async def contact_support(callback: types.CallbackQuery):
    await callback.message.edit_text("📞 **الدعم الفني:** أرسل رسالتك وسيتواصل معك المطور.", parse_mode="Markdown", reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup())

@dp.callback_query(F.data == "enter_coupon")
async def enter_coupon_prompt(callback: types.CallbackQuery):
    await callback.message.edit_text("🎟️ **أرسل كود الكوبون الآن في الرسائل:**", parse_mode="Markdown", reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup())

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_messages(message: types.Message):
    text = message.text.strip()
    user_id = message.from_user.id
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT reward FROM coupons WHERE code = ?", (text,)) as cursor:
            coupon = await cursor.fetchone()
        if coupon:
            reward = coupon[0]
            await db.execute("DELETE FROM coupons WHERE code = ?", (text,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            await db.commit()
            await message.answer(f"🎉 **تم تفعيل الكوبون!** حصلت على `+{reward} نقطة`.")
            return

    try:
        await bot.send_message(ADMIN_ID, f"📩 **رسالة دعم من {message.from_user.first_name}:**\n{text}")
        await message.answer("✅ تم إرسال رسالتك للادارة.")
    except: pass

@dp.message(Command("addcoupon"))
async def add_coupon(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3: return
    code, reward = args[1], int(args[2])
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT OR REPLACE INTO coupons (code, reward) VALUES (?, ?)", (code, reward))
        await db.commit()
    await message.reply(f"✅ تم إنشاء الكوبون `{code}` بقيمة `{reward}` نقطة.")

@dp.callback_query(F.data == "request_withdraw")
async def request_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT balance, name FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0
            name = row[1] if row else "مستخدم"
            
    if balance < 10000:
        await callback.answer("❌ الرصيد الأقل للسحب هو 10,000 نقطة.", show_alert=True)
    else:
        await callback.message.edit_text("✅ تم تقديم طلب السحب بنجاح!", reply_markup=InlineKeyboardBuilder().button(text="🔙 رجوع", callback_data="back_home").as_markup())
        await bot.send_message(ADMIN_ID, f"🔔 **طلب سحب:** {name} (`{user_id}`) - الرصيد: `{balance}`")

async def main():
    await init_db()
    await asyncio.gather(web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
