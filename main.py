# main.py
import os, json, random, psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = "8997328313:AAH5lmrQJODXNjlK0eJmAp-Pfb1ejuE3-7k"
ADMIN_ID = 81469723
DATABASE_URL = os.getenv("DATABASE_URL")

ADD_CHANNEL, DEL_CHANNEL, ADD_SERVER, DEL_SERVER = range(4)

# 💎 Premium UI Safe Emojis (NO custom emoji tags)
MSG_EMOJIS = {
    "welcome": "🦅",
    "error": "❌",
    "success": "✅",
    "rocket": "🚀",
    "active": "🟢",
    "expired": "🔴",
    "id_tag": "🆔",
    "box": "📦",
    "time": "⏳",
    "profile": "👤",
    "book": "📚",
    "card": "🔥",
    "money": "💸",
    "bell": "🔔",
    "refresh": "🔄",
    "admin": "🛠",
    "name": "📛",
    "list": "📋",
    "speaker": "📢",
    "mail": "📬",
    "camera": "📷",
    "warning": "⚠️",
    "trash": "🗑",
    "diamond": "🆕",
    "bullet": "•",
    "test": "🎁",
    "sedora": "🦅",
    "pin": "📌",
    "prime": "⚡️",
    "number": "⚠️",
    "accept": "✅",
    "hand": "🫱",
    "link": "🔥",
    "invite": "🐾",
    "support": "👩‍💻",
    "orders": "🕐",
    "down": "⏬",
    "back": "❌",
    "stats": "📊",
    "not": "🚫",
    "servers": "🔥",
    "stars": "✨",
    "gift": "🎁",
    "taeid": "👍",
    "rules": "🚫",
    "rule": "💸",
}

# 💎 SAFE emoji function
def te(name):
    return MSG_EMOJIS.get(name, "")

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        got_server BOOLEAN DEFAULT FALSE,
        server TEXT)""")

    for k in ["channels", "servers"]:
        cur.execute(
            "INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT DO NOTHING",
            (k, "[]")
        )

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

        kb = [
            [InlineKeyboardButton(f"{te('accept')} بررسی عضویت", callback_data="check_join")]
        ]

        txt = (
            f"{te('sedora')} <b>به Sedora VPN خوش آمدید</b>\n\n"
            f"{te('invite')} برای دریافت سرویس تست، ابتدا عضو کانال‌ها شوید:\n\n"
            + "\n".join([f"{te('bullet')} {c}" for c in channels]) +
            f"\n\n{te('warning')} پس از عضویت روی دکمه زیر کلیک کنید"
        )

        await update.message.reply_text(
            txt,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        return

    await send_server(u.id, update, context)

async def send_server(uid, update, context):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT got_server,server FROM users WHERE user_id=%s", (uid,))
    r = cur.fetchone()

    if r and r[0]:
        msg = (
            f"{te('warning')} <b>شما قبلاً سرور دریافت کرده‌اید</b>\n\n"
            f"{te('servers')} <code>{r[1]}</code>"
        )

    else:
        servers = get_setting("servers")

        if not servers:
            msg = (
                f"{te('not')} <b>سرور فعلاً موجود نیست</b>\n\n"
                f"{te('support')} به زودی دوباره فعال می‌شود"
            )
        else:
            server = servers.pop(0)
            set_setting("servers", servers)

            cur.execute(
                "UPDATE users SET got_server=TRUE,server=%s WHERE user_id=%s",
                (server, uid)
            )
            con.commit()

            msg = (
                f"{te('gift')} <b>سرور تست شما آماده است</b>\n\n"
                f"{te('servers')} <code>{server}</code>\n\n"
                f"{te('warning')} پیشنهاد: NapsternetV یا V2Box\n"
                f"{te('rocket')} اتصال سریع و پایدار"
            )

    con.close()

    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_text(msg, parse_mode="HTML")

async def check_join(update, context):
    q = update.callback_query
    await q.answer()

    if await joined_all(q.from_user.id, context.bot):
        await send_server(q.from_user.id, update, context)
    else:
        await q.message.reply_text(
            f"{te('warning')} هنوز در تمامی کانال‌های اجباری عضو نشده‌اید."
        )

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{te('diamond')} افزودن کانال", callback_data="add_ch")],
        [InlineKeyboardButton(f"{te('trash')} حذف کانال", callback_data="del_ch")],
        [InlineKeyboardButton(f"{te('servers')} افزودن سرور", callback_data="add_sv")],
        [InlineKeyboardButton(f"{te('not')} حذف سرور", callback_data="del_sv")],
    ])

async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"{te('admin')} <b>پنل مدیریت Sedora</b>\n"
        f"{te('list')} مدیریت کامل سرورها و کانال‌ها",
        reply_markup=admin_kb(),
        parse_mode="HTML"
    )

async def panel(update, context):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    m = {
        "add_ch": (f"{te('pin')} آیدی کانال را ارسال کنید", ADD_CHANNEL),
        "del_ch": (f"{te('trash')} آیدی کانال را ارسال کنید", DEL_CHANNEL),
        "add_sv": (f"{te('servers')} سرورها را خط به خط ارسال کنید", ADD_SERVER),
        "del_sv": (f"{te('warning')} سرور مورد نظر را ارسال کنید", DEL_SERVER),
    }

    await q.message.reply_text(m[q.data][0], parse_mode="HTML")
    return m[q.data][1]

async def add_channel(update, context):
    data = get_setting("channels")
    data.append(update.message.text.strip())
    set_setting("channels", data)
    await update.message.reply_text(f"{te('success')} انجام شد.")
    return ConversationHandler.END

async def del_channel(update, context):
    data = get_setting("channels")
    ch = update.message.text.strip()
    if ch in data:
        data.remove(ch)
    set_setting("channels", data)
    await update.message.reply_text(f"{te('success')} انجام شد.")
    return ConversationHandler.END

async def add_server(update, context):
    servers = get_setting("servers")
    servers.extend([x.strip() for x in update.message.text.splitlines() if x.strip()])
    set_setting("servers", servers)
    await update.message.reply_text(f"{te('success')} انجام شد.")
    return ConversationHandler.END

async def del_server(update, context):
    servers = get_setting("servers")
    s = update.message.text.strip()
    if s in servers:
        servers.remove(s)
    set_setting("servers", servers)
    await update.message.reply_text(f"{te('success')} انجام شد.")
    return ConversationHandler.END

def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(panel, pattern="^(add_ch|del_ch|add_sv|del_sv)$")],
        states={
            ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel)],
            DEL_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_channel)],
            ADD_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_server)],
            DEL_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_server)],
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