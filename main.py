import os
import json
import psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

# =========================
# CONFIG (SAFE)
# =========================
BOT_TOKEN = "8997328313:AAH-sbq8-7iUPSLU_g9ICPoBEFti9w9wTCw"
ADMIN_ID = 81469723
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set!")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set!")

# =========================
# EMOJIS (CUSTOM SAFE SYSTEM)
# =========================
MSG_EMOJIS = {
     "welcome": {"id": "6316501178368663573", "char": "🦅"},
    "error":   {"id": "5348132683304156113", "char": "❌"},
    "success": {"id": "4958725487682650920", "char": "✅"},
    "rocket":  {"id": "4958725487682650920", "char": "🚀"},
    "active":  {"id": "4956720180337050608", "char": "🟢"},
    "expired": {"id": "4956582500865410174", "char": "🔴"},
    "id_tag":  {"id": "4958686613933655185", "char": "🆔"},
    "box":     {"id": "5409380072291316349", "char": "📦"},
    "time":    {"id": "5350773074578916842", "char": "⏳"},
    "profile": {"id": "5348136664738839786", "char": "👤"},
    "book":    {"id": "4956436416142771580", "char": "📚"},
    "card":    {"id": "5940563313720037057", "char": "🔥"},
    "money":   {"id": "5956324890213619515", "char": "💸"},
    "bell":    {"id": "4956368164817470478", "char": "🔔"},
    "refresh": {"id": "4956418939920843885", "char": "🔄"},
    "admin":   {"id": "5971818172985117571", "char": "🛠"},
    "name":    {"id": "5972072533833289156", "char": "📛"},
    "list":    {"id": "5974235702701853774", "char": "📋"},
    "speaker": {"id": "5972240522889138094", "char": "📢"},
    "mail":    {"id": "5852830669599674051", "char": "📬"},
    "camera":  {"id": "4992254300202730194", "char": "📷"},
    "warning": {"id": "5350470691701407492", "char": "⚠️"},
    "trash":   {"id": "4956475826762679249", "char": "🗑"},
    "diamond": {"id": "5348270285466385224", "char": "🆕"},
    "bullet":  {"id": "5350572310627632617", "char": "✅"},
    "test":    {"id": "4958725487682650920", "char": "🎁"},
    "sedora":  {"id":"6316422138085514606",  "char": "🦅"},
    "pin":  {"id":"5348498060466996739",  "char": "📌"},
    "PRIME":  {"id":"5350618807943576963",  "char": "⚡️"},
    "NUMBER":  {"id":"5350477112677515642",  "char": "⚠️"},
    "accept":  {"id":"5348404473129614535",  "char": "✅"},
    "hand":  {"id":"5990225492282709220",  "char": "🫱"},
    "link":  {"id":"5841171023096976223",  "char": "🔥"},
    "invite":  {"id":"5348438459205831716",  "char": "🐾"},
    "support":  {"id":"5979065840102810733",  "char": "👩‍💻"},
    "orders":  {"id":"5348090777308251395",  "char": "🕐"},
    "paein":  {"id":"5350700390847365132",  "char": "⏬"},
    "back":  {"id":"5348514879558926674",  "char": "❌"},    
    "stats":  {"id":"5990060518293901972",  "char": "❌"},
    "not":  {"id":"5989790729923203577",  "char": "🚫"},
    "servers":  {"id":"5841171023096976223",  "char": "🔥"},
    "stars":  {"id":"5841394116583232174",  "char": "🔥"},
    "gift":  {"id":"5970037062932371393",  "char": "⭕️"},
    "taeid":  {"id":"6073335669260819751",  "char": "👍"},
    "rules":  {"id":"5987863552327684435",  "char": "🚫"},
    "rule":  {"id":"5956564630993114415",  "char": "💸"},
    "nv":  {"id":"6050626661043411760",  "char": "💸"},
    "v2box":  {"id":"5866266486942733691",  "char": "💸"},
    "ok":  {"id":"6102503234549586828",  "char": "✅"},
}

# ✔ FIXED emoji function (NO ID LEAK ANYMORE)
def te(name: str) -> str:
    e = MSG_EMOJIS.get(name)
    if not e:
        return ""
    return e.get("char", "")

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
            [InlineKeyboardButton(f"{te('accept')} بررسی عضویت", callback_data="check_join")]
        ]

        txt = (
            f"{te('sedora')} <b>به Sedora VPN خوش آمدید</b>\n\n"
            f"{te('invite')} برای دریافت سرویس تست، ابتدا عضو کانال‌ها شوید:\n\n"
            + "\n".join([f"{te('bullet')} {c}" for c in channels]) +
            f"\n\n{te('warning')} پس از عضویت روی دکمه زیر کلیک کنید"
        )

        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
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
        msg = f"{te('warning')} قبلاً سرور دریافت کرده‌اید\n\n{te('servers')} {r[1]}"
    else:
        servers = get_setting("servers")

        if not servers:
            msg = f"{te('not')} سروری موجود نیست"
        else:
            server = servers.pop(0)
            set_setting("servers", servers)

            cur.execute(
                "UPDATE users SET got_server=TRUE,server=%s WHERE user_id=%s",
                (server, uid)
            )
            con.commit()

            msg = f"{te('gift')} سرور شما آماده است:\n\n{te('servers')} {server}"

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
        await q.message.reply_text(f"{te('warning')} هنوز عضو همه کانال‌ها نیستید")

# =========================
# ADMIN PANEL
# =========================
def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{te('diamond')} افزودن کانال", callback_data="add_ch")],
        [InlineKeyboardButton(f"{te('trash')} حذف کانال", callback_data="del_ch")],
        [InlineKeyboardButton(f"{te('servers')} افزودن سرور", callback_data="add_sv")],
        [InlineKeyboardButton(f"{te('trash')} حذف سرور", callback_data="del_sv")],
    ])

async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"{te('admin')} پنل مدیریت",
        reply_markup=admin_kb()
    )

# =========================
# PANEL HANDLER
# =========================
ADD_CHANNEL, DEL_CHANNEL, ADD_SERVER, DEL_SERVER = range(4)

async def panel(update, context):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return ConversationHandler.END

    mapping = {
        "add_ch": ("آیدی کانال را ارسال کنید", ADD_CHANNEL),
        "del_ch": ("آیدی کانال را ارسال کنید", DEL_CHANNEL),
        "add_sv": ("سرورها را ارسال کنید", ADD_SERVER),
        "del_sv": ("سرور را ارسال کنید", DEL_SERVER),
    }

    txt, state = mapping[q.data]
    await q.message.reply_text(txt)
    return state

# =========================
# CHANNEL / SERVER OPS
# =========================
async def add_channel(update, context):
    data = get_setting("channels")
    data.append(update.message.text.strip())
    set_setting("channels", data)
    await update.message.reply_text("OK")
    return ConversationHandler.END

async def del_channel(update, context):
    data = get_setting("channels")
    val = update.message.text.strip()
    if val in data:
        data.remove(val)
    set_setting("channels", data)
    await update.message.reply_text("OK")
    return ConversationHandler.END

async def add_server(update, context):
    servers = get_setting("servers")
    servers.extend(update.message.text.splitlines())
    set_setting("servers", servers)
    await update.message.reply_text("OK")
    return ConversationHandler.END

async def del_server(update, context):
    servers = get_setting("servers")
    val = update.message.text.strip()
    if val in servers:
        servers.remove(val)
    set_setting("servers", servers)
    await update.message.reply_text("OK")
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