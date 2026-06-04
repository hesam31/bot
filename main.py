import logging
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import BotCommand, BotCommandScopeChat, MenuButtonCommands
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# پچ دکمه‌های پریمیوم تلگرام
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_orig_init = InlineKeyboardButton.__init__
_orig_to_dict = InlineKeyboardButton.to_dict
_extras_store = {}

def _patched_init(self, text, callback_data=None, url=None, style=None, icon_custom_emoji_id=None, copy_text=None, **kwargs):
    _orig_init(self, text=text, callback_data=callback_data, url=url, **kwargs)
    extra = {}
    if style: extra["style"] = style
    if icon_custom_emoji_id: extra["icon_custom_emoji_id"] = icon_custom_emoji_id
    if copy_text: extra["copy_text"] = {"text": copy_text}
    if extra: _extras_store[id(self)] = extra

def _patched_to_dict(self, *args, **kwargs):
    d = _orig_to_dict(self, *args, **kwargs)
    extra = _extras_store.get(id(self))
    if extra: d.update(extra)
    return d

InlineKeyboardButton.__init__ = _patched_init
InlineKeyboardButton.to_dict = _patched_to_dict

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# تنظیمات اصلی — اینجا ویرایش کنید
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOT_TOKEN = os.getenv("8997328313:AAESG5KXik9CvVJn8vPgGEwGmjK-AeGeGx4")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [81469723, 1892655576]  # آیدی عددی ادمین‌ها

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# اموجی‌های پریمیوم
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MSG_EMOJIS = {
    "welcome":  {"id": "6316501178368663573", "char": "🦅"},
    "success":  {"id": "4958725487682650920", "char": "✅"},
    "error":    {"id": "5348132683304156113", "char": "❌"},
    "active":   {"id": "4956720180337050608", "char": "🟢"},
    "admin":    {"id": "5971818172985117571", "char": "🛠"},
    "list":     {"id": "5974235702701853774", "char": "📋"},
    "channel":  {"id": "4992254300202730194", "char": "📢"},
    "server":   {"id": "5841171023096976223", "char": "🔥"},
    "stats":    {"id": "5990060518293901972", "char": "📊"},
    "profile":  {"id": "5348136664738839786", "char": "👤"},
    "warning":  {"id": "5350470691701407492", "char": "⚠️"},
    "back":     {"id": "5348514879558926674", "char": "❌"},
    "add":      {"id": "4958725487682650920", "char": "➕"},
    "trash":    {"id": "4956475826762679249", "char": "🗑"},
    "rocket":   {"id": "4958725487682650920", "char": "🚀"},
    "join":     {"id": "5350835008007324644", "char": "🔗"},
    "check":    {"id": "5972326417940093090", "char": "✅"},
    "box":      {"id": "5409380072291316349", "char": "📦"},
    "time":     {"id": "5350773074578916842", "char": "⏳"},
    "test":     {"id": "4958725487682650920", "char": "🎁"},
}

def te(key):
    e = MSG_EMOJIS.get(key)
    if e and e["id"]:
        return f'<tg-emoji emoji-id="{e["id"]}">{e["char"]}</tg-emoji>'
    return e["char"] if e else ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# state های ConversationHandler
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(
    ADD_CHANNEL_USER,
    ADD_CHANNEL_LINK,
    DEL_CHANNEL_INDEX,
    ADD_SERVER_INPUT,
) = range(4)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دیتابیس (PostgreSQL)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_data (
            id INTEGER PRIMARY KEY,
            data JSONB
        )
    """)
    cur.execute("SELECT id FROM bot_data WHERE id = 1")
    exists = cur.fetchone()
    if not exists:
        default_data = {
            "settings": {
                "channels": [],
                "servers": [],
            },
            "users": {},
        }
        cur.execute(
            "INSERT INTO bot_data (id, data) VALUES (%s, %s)",
            (1, json.dumps(default_data))
        )
    conn.commit()
    cur.close()
    conn.close()

def load_db():
    init_db()
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT data FROM bot_data WHERE id = 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return {"settings": {"channels": [], "servers": []}, "users": {}}
    db = row["data"]
    db.setdefault("settings", {})
    db["settings"].setdefault("channels", [])
    db["settings"].setdefault("servers", [])
    db.setdefault("users", {})
    return db

def save_db(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE bot_data SET data = %s WHERE id = 1",
        (json.dumps(data),)
    )
    conn.commit()
    cur.close()
    conn.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# کیبوردها
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{MSG_EMOJIS['server']['char']} دریافت سرور",
            callback_data="get_server",
            style="primary",
            icon_custom_emoji_id=MSG_EMOJIS["server"]["id"]
        )],
    ])

def admin_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{MSG_EMOJIS['channel']['char']} مدیریت کانال‌های جوین اجباری",
            callback_data="admin_channels",
            style="primary",
            icon_custom_emoji_id=MSG_EMOJIS["channel"]["id"]
        )],
        [InlineKeyboardButton(
            f"{MSG_EMOJIS['server']['char']} مدیریت سرورها",
            callback_data="admin_servers",
            style="primary",
            icon_custom_emoji_id=MSG_EMOJIS["server"]["id"]
        )],
        [InlineKeyboardButton(
            f"{MSG_EMOJIS['stats']['char']} آمار کلی",
            callback_data="admin_stats",
            style="primary",
            icon_custom_emoji_id=MSG_EMOJIS["stats"]["id"]
        )],
    ])

def back_admin_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"{MSG_EMOJIS['back']['char']} بازگشت",
            callback_data="back_admin",
            style="danger",
            icon_custom_emoji_id=MSG_EMOJIS["back"]["id"]
        )
    ]])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# جوین اجباری
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id

    # ادمین‌ها معاف هستند
    if user_id in ADMIN_IDS:
        return True

    db = load_db()
    channels = db["settings"].get("channels", [])

    # اگر کانالی تنظیم نشده همه می‌توانند ادامه دهند
    if not channels:
        return True

    not_joined = False
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch["username"], user_id)
            if member.status in ["left", "kicked"]:
                not_joined = True
                break
        except:
            not_joined = True
            break

    if not_joined:
        rows = []
        for ch in channels:
            rows.append([
                InlineKeyboardButton(
                    f"عضویت در {ch['username']}",
                    url=ch["link"],
                    style="success",                           # ← سبز
                    icon_custom_emoji_id=MSG_EMOJIS["join"]["id"]
                )
            ])
        rows.append([
            InlineKeyboardButton(
                "بررسی عضویت ✅",
                callback_data="check_join_btn",
                style="success",
                icon_custom_emoji_id=MSG_EMOJIS["check"]["id"]
            )
        ])

        msg = (
            f"{te('warning')} برای استفاده از ربات ابتدا در همه کانال‌های زیر عضو شوید:"
        )

        if update.message:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
        elif update.callback_query:
            try:
                await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
            except:
                pass
        return False

    # علامت‌گذاری کاربر به عنوان فعال
    uid = str(user_id)
    db = load_db()
    if uid in db["users"]:
        db["users"][uid]["is_active"] = True
        save_db(db)

    return True


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    db = load_db()
    channels = db["settings"].get("channels", [])

    all_joined = True
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch["username"], user_id)
            if member.status in ["left", "kicked"]:
                all_joined = False
                break
        except:
            all_joined = False
            break

    if not all_joined:
        await query.answer("هنوز در همه کانال‌ها عضو نشده‌اید!", show_alert=True)
    else:
        await query.answer("عضویت شما تأیید شد! ✅", show_alert=True)
        uid = str(user_id)
        db["users"].setdefault(uid, {})
        db["users"][uid]["is_active"] = True
        save_db(db)
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            user_id,
            f"{te('welcome')} <b>خوش آمدید!</b>\n\nگزینه مورد نظر را انتخاب کنید:",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# استارت
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)

    # ثبت کاربر اگر جدید است
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": update.effective_user.first_name,
            "username": update.effective_user.username,
            "is_active": False,
            "received_server": False,
        }
        save_db(db)

    # چک جوین اجباری
    if not await check_force_join(update, context):
        return

    await update.message.reply_text(
        f"{te('welcome')} <b>خوش آمدید!</b>\n\nگزینه مورد نظر را انتخاب کنید:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دریافت سرور (بعد از جوین همه کانال‌ها)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def get_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await check_force_join(update, context):
        return

    uid = str(query.from_user.id)
    db = load_db()

    # هر کاربر فقط یک بار سرور می‌گیرد
    if db["users"].get(uid, {}).get("received_server"):
        await query.message.edit_text(
            f"{te('error')} شما قبلاً سرور دریافت کرده‌اید.",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    servers = db["settings"].get("servers", [])

    if not servers:
        await query.message.edit_text(
            f"{te('warning')} در حال حاضر سروری موجود نیست.\nلطفاً بعداً مراجعه کنید.",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    # ارسال اولین سرور و حذف از لیست
    server = servers.pop(0)
    db["settings"]["servers"] = servers
    db["users"][uid]["received_server"] = True
    save_db(db)

    await query.message.edit_text(
        f"{te('server')} <b>سرور شما:</b>\n\n"
        f"<code>{server}</code>\n\n"
        f"{te('warning')} این سرور مخصوص شماست.",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# پنل ادمین
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    msg = f"{te('admin')} <b>پنل مدیریت</b>\n\nگزینه مورد نظر را انتخاب کنید:"

    if update.message:
        try:
            await update.message.delete()
        except:
            pass
        await context.bot.send_message(
            update.effective_chat.id,
            msg,
            reply_markup=admin_menu_kb(),
            parse_mode="HTML"
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            msg,
            reply_markup=admin_menu_kb(),
            parse_mode="HTML"
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# مدیریت کانال‌های جوین اجباری
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def admin_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()
    channels = db["settings"].get("channels", [])

    text = f"{te('channel')} <b>کانال‌های جوین اجباری:</b>\n\n"
    if not channels:
        text += "هیچ کانالی ثبت نشده است."
    else:
        for i, ch in enumerate(channels):
            text += f"{i+1}. {ch['username']}\n"

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ افزودن کانال",
                callback_data="add_channel",
                style="success",
                icon_custom_emoji_id=MSG_EMOJIS["add"]["id"]
            ),
            InlineKeyboardButton(
                "🗑 حذف کانال",
                callback_data="del_channel",
                style="danger",
                icon_custom_emoji_id=MSG_EMOJIS["trash"]["id"]
            ),
        ],
        [InlineKeyboardButton(
            f"{MSG_EMOJIS['back']['char']} بازگشت",
            callback_data="back_admin",
            style="danger",
            icon_custom_emoji_id=MSG_EMOJIS["back"]["id"]
        )],
    ])

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        f"{te('channel')} آیدی کانال را با @ وارد کنید:\n\nمثال: <code>@mychannel</code>",
        parse_mode="HTML",
        reply_markup=back_admin_kb()
    )
    return ADD_CHANNEL_USER


async def add_channel_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_ch_user"] = update.message.text.strip()
    await update.message.reply_text(
        f"{te('channel')} لینک دعوت کانال را وارد کنید:\n\nمثال: <code>https://t.me/mychannel</code>",
        parse_mode="HTML",
        reply_markup=back_admin_kb()
    )
    return ADD_CHANNEL_LINK


async def add_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    db["settings"]["channels"].append({
        "username": context.user_data["new_ch_user"],
        "link": update.message.text.strip()
    })
    save_db(db)
    await update.message.reply_text(
        f"{te('success')} کانال با موفقیت اضافه شد.",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def del_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()
    channels = db["settings"].get("channels", [])

    if not channels:
        await query.message.edit_text(
            f"{te('error')} کانالی برای حذف وجود ندارد.",
            reply_markup=back_admin_kb(),
            parse_mode="HTML"
        )
        return ConversationHandler.END

    text = f"{te('trash')} شماره کانال مورد نظر برای حذف را وارد کنید:\n\n"
    for i, ch in enumerate(channels):
        text += f"{i+1}. {ch['username']}\n"

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=back_admin_kb())
    return DEL_CHANNEL_INDEX


async def del_channel_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text.strip()) - 1
        db = load_db()
        channels = db["settings"].get("channels", [])
        if 0 <= idx < len(channels):
            removed = channels.pop(idx)
            db["settings"]["channels"] = channels
            save_db(db)
            await update.message.reply_text(
                f"{te('success')} کانال {removed['username']} حذف شد.",
                reply_markup=admin_menu_kb(),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"{te('error')} شماره اشتباه است.",
                reply_markup=admin_menu_kb(),
                parse_mode="HTML"
            )
    except:
        await update.message.reply_text(
            f"{te('error')} فقط عدد وارد کنید.",
            reply_markup=admin_menu_kb(),
            parse_mode="HTML"
        )
    return ConversationHandler.END

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# مدیریت سرورها
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def admin_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()
    count = len(db["settings"].get("servers", []))

    text = (
        f"{te('server')} <b>مدیریت سرورها</b>\n\n"
        f"{te('box')} سرورهای موجود: <b>{count}</b>\n\n"
        "هر سرور را در یک پیام جداگانه ارسال کنید.\n"
        "پس از اتمام روی «پایان» بزنید."
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "➕ افزودن سرور",
            callback_data="add_server",
            style="success",
            icon_custom_emoji_id=MSG_EMOJIS["add"]["id"]
        )],
        [InlineKeyboardButton(
            f"{MSG_EMOJIS['back']['char']} بازگشت",
            callback_data="back_admin",
            style="danger",
            icon_custom_emoji_id=MSG_EMOJIS["back"]["id"]
        )],
    ])

    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


async def add_server_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        f"{te('server')} سرورها را ارسال کنید (هر سرور در یک پیام).\n\n"
        "پس از اتمام روی «پایان» بزنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "✅ پایان",
                callback_data="finish_servers",
                style="success",
                icon_custom_emoji_id=MSG_EMOJIS["check"]["id"]
            )
        ]])
    )
    return ADD_SERVER_INPUT


async def add_server_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = update.message.text.strip()
    if not config:
        return ADD_SERVER_INPUT

    db = load_db()
    servers = db["settings"].get("servers", [])

    if config not in servers:
        servers.append(config)
        db["settings"]["servers"] = servers
        save_db(db)
        await update.message.reply_text(
            f"{te('success')} سرور اضافه شد. مجموع: {len(servers)}\n\nسرور بعدی را ارسال کنید یا «پایان» را بزنید.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "✅ پایان",
                    callback_data="finish_servers",
                    style="success",
                    icon_custom_emoji_id=MSG_EMOJIS["check"]["id"]
                )
            ]])
        )
    else:
        await update.message.reply_text(
            f"{te('warning')} این سرور قبلاً ثبت شده بود.",
            parse_mode="HTML"
        )

    return ADD_SERVER_INPUT


async def finish_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()
    count = len(db["settings"].get("servers", []))

    await query.message.edit_text(
        f"{te('success')} عملیات تمام شد. مجموع سرورهای موجود: <b>{count}</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )
    return ConversationHandler.END

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# آمار کلی
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()

    total_users   = len(db["users"])
    active_users  = sum(1 for u in db["users"].values() if u.get("is_active", False))
    got_server    = sum(1 for u in db["users"].values() if u.get("received_server", False))
    servers_left  = len(db["settings"].get("servers", []))
    channels_cnt  = len(db["settings"].get("channels", []))

    text = (
        f"{te('stats')} <b>آمار کلی ربات</b>\n\n"
        f"{te('profile')} کل کاربران (استارت زده): <b>{total_users}</b>\n"
        f"{te('active')} کاربران فعال (جوین‌شده): <b>{active_users}</b>\n"
        f"{te('server')} سرور دریافت کرده‌اند: <b>{got_server}</b>\n"
        f"{te('box')} سرورهای موجود در مخزن: <b>{servers_left}</b>\n"
        f"{te('channel')} کانال‌های جوین اجباری: <b>{channels_cnt}</b>\n"
    )

    await query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_admin_kb()
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# تنظیم کامندها
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def set_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "شروع ربات")])
    for admin_id in ADMIN_IDS:
        await app.bot.set_my_commands(
            [BotCommand("start", "شروع ربات"), BotCommand("admin", "پنل مدیریت")],
            scope=BotCommandScopeChat(admin_id)
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# اجرای ربات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":

    async def post_init(app):
        await set_commands(app)

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # ── هندلرهای پایه ──
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join_btn$"))
    app.add_handler(CallbackQueryHandler(start,        pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(admin_start,  pattern="^back_admin$"))
    app.add_handler(CallbackQueryHandler(get_server,   pattern="^get_server$"))

    # ── پنل ادمین ──
    app.add_handler(CallbackQueryHandler(admin_channels, pattern="^admin_channels$"))
    app.add_handler(CallbackQueryHandler(admin_servers,  pattern="^admin_servers$"))
    app.add_handler(CallbackQueryHandler(admin_stats,    pattern="^admin_stats$"))

    # ── مکالمه مدیریت کانال‌ها ──
    channel_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_channel_start, pattern="^add_channel$"),
            CallbackQueryHandler(del_channel_start, pattern="^del_channel$"),
        ],
        states={
            ADD_CHANNEL_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_username)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_link)],
            DEL_CHANNEL_INDEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_channel_save)],
        },
        fallbacks=[CallbackQueryHandler(admin_start, pattern="^back_admin$")],
        allow_reentry=True,
    )
    app.add_handler(channel_conv)

    # ── مکالمه مدیریت سرورها ──
    server_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_server_start, pattern="^add_server$"),
        ],
        states={
            ADD_SERVER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_input),
                CallbackQueryHandler(finish_servers, pattern="^finish_servers$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(admin_start, pattern="^back_admin$")],
        allow_reentry=True,
    )
    app.add_handler(server_conv)

    print("--- Bot Started ---")
    init_db()
    app.run_polling()
