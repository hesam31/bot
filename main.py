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
BOT_TOKEN = "8997328313:AAH-sbq8-7iUPSLU_g9ICPoBEFti9w9wTCw"
ADMIN_ID = 81469723
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# DATABASE
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

# =========================
# PREMIUM BUTTON SYSTEM
# =========================
BTN_CFG = {
    "buy_new": {"text": "خرید اشتراک جدید", "emoji": "buy_new"},
    "renew": {"text": "تمدید اشتراک", "emoji": "renew"},
    "referral": {"text": "رفرال", "emoji": "referral"},
    "my_services": {"text": "سرویس‌های من", "emoji": "my_services"},
    "profile": {"text": "پروفایل من", "emoji": "profile"},
    "news": {"text": "آموزش و اخبار", "emoji": "news"},
    "support": {"text": "پشتیبانی", "emoji": "support"},
    "back": {"text": "بازگشت", "emoji": "back"},

    "admin_channels": {"text": "مدیریت کانال‌ها", "emoji": "admin_channels"},
    "admin_users": {"text": "لیست کاربران", "emoji": "admin_users"},
    "admin_add_server": {"text": "افزودن سرور", "emoji": "admin_add_plan"},
    "admin_del_server": {"text": "حذف سرور", "emoji": "admin_del_plan"},
    "admin_broadcast": {"text": "پیام همگانی", "emoji": "admin_broadcast"},
}

DYN_BTN_EMOJIS = {
    "buy_new": "5348270285466385224",
    "renew": "4956418939920843885",
    "referral": "5350790271627968474",
    "my_services": "5409380072291316349",
    "profile": "5348136664738839786",
    "news": "4956436416142771580",
    "support": "5979065840102810733",
    "back": "5972120066236357644",

    "admin_channels": "4992622834166530981",
    "admin_users": "5974235702701853774",
    "admin_add_plan": "4956232383721374836",
    "admin_del_plan": "4956475826762679249",
    "admin_broadcast": "5972240522889138094",
}

def btn(key, callback):
    cfg = BTN_CFG.get(key)
    if not cfg:
        return None

    return InlineKeyboardButton(
        text=cfg["text"],
        callback_data=callback,
        custom_emoji_id=DYN_BTN_EMOJIS.get(cfg["emoji"])
    )

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

        kb = [
            [InlineKeyboardButton("بررسی عضویت", callback_data="check_join")]
        ]

        txt = "🔔 برای ادامه ابتدا عضو کانال‌ها شوید:\n\n"
        txt += "\n".join([f"• {c}" for c in channels])

        await update.message.reply_text(
            txt,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    await send_server(u.id, update, context)

# =========================
# SERVER SEND
# =========================
async def send_server(uid, update, context):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT got_server,server FROM users WHERE user_id=%s", (uid,))
    r = cur.fetchone()

    if r and r[0]:
        msg = f"⚠️ قبلاً سرور گرفته‌اید\n\n🔥 {r[1]}"
    else:
        servers = get_setting("servers")

        if not servers:
            msg = "🚫 سروری موجود نیست"
        else:
            server = servers.pop(0)
            set_setting("servers", servers)

            cur.execute(
                "UPDATE users SET got_server=TRUE,server=%s WHERE user_id=%s",
                (server, uid)
            )
            con.commit()

            msg = f"🎁 سرور شما آماده است:\n\n🔥 {server}"

    con.close()

    if update.callback_query:
        await update.callback_query.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)

# =========================
# CHECK JOIN
# =========================
async def check_join(update, context):
    q = update.callback_query
    await q.answer()

    if await joined_all(q.from_user.id, context.bot):
        await send_server(q.from_user.id, update, context)
    else:
        await q.message.reply_text("⚠️ هنوز عضو کانال‌ها نیستید")

# =========================
# ADMIN PANEL
# =========================
def admin_kb():
    return InlineKeyboardMarkup([
        [btn("admin_channels", "add_ch")],
        [btn("admin_users", "del_ch")],
        [btn("admin_add_server", "add_sv")],
        [btn("admin_del_server", "del_sv")],
        [btn("admin_broadcast", "broadcast")]
    ])

async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "🛠 پنل مدیریت",
        reply_markup=admin_kb()
    )

# =========================
# CONVERSATION
# =========================
ADD_CHANNEL, DEL_CHANNEL, ADD_SERVER, DEL_SERVER = range(4)

async def panel(update, context):
    q = update.callback_query
    await q.answer()

    mapping = {
        "add_ch": ("آیدی کانال:", ADD_CHANNEL),
        "del_ch": ("آیدی کانال:", DEL_CHANNEL),
        "add_sv": ("سرور:", ADD_SERVER),
        "del_sv": ("سرور:", DEL_SERVER),
    }

    txt, state = mapping[q.data]
    await q.message.reply_text(txt)
    return state

async def add_channel(update, context):
    data = get_setting("channels")
    data.append(update.message.text.strip())
    set_setting("channels", data)
    await update.message.reply_text("✅ انجام شد")
    return ConversationHandler.END

async def del_channel(update, context):
    data = get_setting("channels")
    val = update.message.text.strip()
    if val in data:
        data.remove(val)
    set_setting("channels", data)
    await update.message.reply_text("✅ انجام شد")
    return ConversationHandler.END

async def add_server(update, context):
    servers = get_setting("servers")
    servers.extend(update.message.text.splitlines())
    set_setting("servers", servers)
    await update.message.reply_text("✅ انجام شد")
    return ConversationHandler.END

async def del_server(update, context):
    servers = get_setting("servers")
    val = update.message.text.strip()
    if val in servers:
        servers.remove(val)
    set_setting("servers", servers)
    await update.message.reply_text("✅ انجام شد")
    return ConversationHandler.END

# =========================
# MAIN
# =========================
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