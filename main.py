import os
import json
import psycopg2

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = ("8997328313:AAFX3RUfdDAvgLf0SqJ4Z7IPWy00cQCYiWE")
ADMIN_IDS = [81469723]
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# PREMIUM EMOJIS (MINIMAL ADD)
# =========================
MSG_EMOJIS = {
    "welcome": {"id": "6316501178368663573", "char": "🦅"},
    "error":   {"id": "5210952531676504517", "char": "❌"},
    "success": {"id": "5337080053119336309", "char": "✅"},
    "rocket":  {"id": "4958725487682650920", "char": "🚀"},
    "active":  {"id": "4956720180337050608", "char": "🟢"},
    "expired": {"id": "4956582500865410174", "char": "🔴"},
    "id_tag":  {"id": "4958686613933655185", "char": "🆔"},
    "box":     {"id": "5409380072291316349", "char": "📦"},
    "time":    {"id": "5350773074578916842", "char": "⏳"},
    "profile": {"id": "5341715473882955310", "char": "👤"},
    "money":   {"id": "5956324890213619515", "char": "💸"},
    "warning": {"id": "5240241223632954241", "char": "❌"},
    "card":    {"id": "5940563313720037057", "char": "🔥"},
    "support": {"id": "5979065840102810733", "char": "👩‍💻"},
    "gift":    {"id": "5206607081334906820", "char": "🎁"},
    "bullet":  {"id": "5350572310627632617", "char": "✔️"},
}

# =========================
# EMOJI RENDER (IMPORTANT)
# =========================
def te(key):
    e = MSG_EMOJIS.get(key)
    if not e:
        return ""
    return f'<tg-emoji emoji-id="{e["id"]}">{e["char"]}</tg-emoji>'

# =========================
# DB
# =========================
def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            got_server BOOLEAN DEFAULT FALSE,
            server TEXT
        )
    """)

    for k in ["channels", "servers"]:
        cur.execute("""
            INSERT INTO settings(key,value)
            VALUES(%s,%s)
            ON CONFLICT DO NOTHING
        """, (k, "[]"))

    con.commit()
    con.close()


def get_setting(key):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE key=%s", (key,))
    r = cur.fetchone()
    con.close()
    return json.loads(r[0]) if r else []


def set_setting(key, val):
    con = db()
    cur = con.cursor()
    cur.execute(
        "UPDATE settings SET value=%s WHERE key=%s",
        (json.dumps(val), key)
    )
    con.commit()
    con.close()

# =========================
# JOIN CHECK
# =========================
async def joined_all(user_id, bot):
    channels = get_setting("channels")

    for ch in channels:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status in ["left", "kicked"]:
                return False
        except:
            return False

    return True

# =========================
# SERVER SYSTEM
# =========================
async def send_server(uid, update, context):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT got_server, server FROM users WHERE user_id=%s", (uid,))
    row = cur.fetchone()

    if row and row[0]:
        msg = (
    f"{te('warning')} <b>شما قبلاً از این ربات سرور دریافت کرده‌اید.</b>\n\n"
    f"{te('profile')} طبق اطلاعات ثبت‌شده، یک سرور قبلاً به حساب شما اختصاص داده شده است و امکان دریافت مجدد وجود ندارد.\n\n"
    f"{te('rocket')} اطلاعات سرور اختصاصی شما:\n\n"
    f"<code>{row[1]}</code>\n\n"
)
    else:
        servers = get_setting("servers")

        if not servers:
            msg = f"{te('error')} سروری موجود نیست"
        else:
            server = servers.pop(0)
            set_setting("servers", servers)

            cur.execute(
                "UPDATE users SET got_server=TRUE, server=%s WHERE user_id=%s",
                (server, uid)
            )
            con.commit()

            msg = (
    f"{te('gift')} <b>تبریک! سرور شما با موفقیت فعال شد.</b>\n\n"
    f"{te('rocket')} مشخصات سرور اختصاصی شما در ادامه نمایش داده شده است:\n\n"
    f"<code>{server}</code>\n\n"
    f"{te('success')} از همراهی شما سپاسگزاریم."
)

    con.close()

    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_text(msg, parse_mode="HTML")

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    con = db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users(user_id,username) VALUES(%s,%s) ON CONFLICT DO NOTHING",
        (u.id, u.username)
    )
    con.commit()
    con.close()

    if not await joined_all(u.id, context.bot):
        channels = get_setting("channels")

        txt = f"{te('warning')} برای ادامه عضو کانال‌ها شوید:\n\n"
        txt += "\n".join([f"• {c}" for c in channels])

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("بررسی عضویت",callback_data="check_join")]
        ])

        await update.message.reply_text(txt, reply_markup=kb)
        return

    await send_server(u.id, update, context)

# =========================
# CHECK JOIN
# =========================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await joined_all(q.from_user.id, context.bot):
        await send_server(q.from_user.id, update, context)
    else:
        await q.message.reply_text(f"{te('error')} هنوز عضو کانال‌ها نیستید")

# =========================
# ADMIN PANEL
# =========================
def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ کانال", callback_data="add_ch"),
         InlineKeyboardButton("➖ کانال", callback_data="del_ch")],
        [InlineKeyboardButton("➕ سرور", callback_data="add_sv"),
         InlineKeyboardButton("➖ سرور", callback_data="del_sv")],
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="broadcast")]
    ])

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    await update.message.reply_text(
        f"{te('warning')} پنل ادمین",
        reply_markup=admin_kb()
    )

# =========================
# STATES
# =========================
ADD_CH, DEL_CH, ADD_SV, DEL_SV, BROADCAST = range(5)

async def panel_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = {
        "add_ch": ("آیدی کانال:", ADD_CH),
        "del_ch": ("آیدی کانال:", DEL_CH),
        "add_sv": ("سرور:", ADD_SV),
        "del_sv": ("سرور:", DEL_SV),
        "broadcast": ("پیام همگانی:", BROADCAST),
    }

    text, state = data[q.data]
    await q.message.reply_text(text)
    return state

# =========================
# CHANNEL / SERVER / BROADCAST
# (بدون تغییر)
# =========================
async def add_channel(update, context):
    data = get_setting("channels")
    data.append(update.message.text.strip())
    set_setting("channels", data)
    await update.message.reply_text("✅ اضافه شد")
    return ConversationHandler.END

async def del_channel(update, context):
    data = get_setting("channels")
    val = update.message.text.strip()
    if val in data:
        data.remove(val)
    set_setting("channels", data)
    await update.message.reply_text("✅ حذف شد")
    return ConversationHandler.END

async def add_server(update, context):
    servers = get_setting("servers")
    servers.extend(update.message.text.splitlines())
    set_setting("servers", servers)
    await update.message.reply_text("✅ اضافه شد")
    return ConversationHandler.END

async def del_server(update, context):
    servers = get_setting("servers")
    val = update.message.text.strip()
    if val in servers:
        servers.remove(val)
    set_setting("servers", servers)
    await update.message.reply_text("✅ حذف شد")
    return ConversationHandler.END

async def broadcast_send(update, context):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    con.close()

    text = update.message.text
    sent = 0

    for u in users:
        try:
            await context.bot.send_message(u[0], text)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"📢 ارسال شد به {sent} نفر")
    return ConversationHandler.END

# =========================
# MAIN
# =========================
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(panel_router)],
        states={
            ADD_CH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel)],
            DEL_CH: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_channel)],
            ADD_SV: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_server)],
            DEL_SV: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_server)],
            BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app.add_handler(conv)

    app.run_polling()

if __name__ == "__main__":
    main()