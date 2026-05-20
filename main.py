import logging
import json
import os
import random
from datetime import datetime
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import MenuButtonCommands
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

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

BOT_TOKEN = "8878547383:AAEKAvalx3osK72rP2i7KqFLduBYdftGc_c"
ADMIN_IDS = [81469723,1892655576]
DB_FILE = "database.json"
CARD_NUMBER = "6037697637334522"
SUPPORT_ID = ["@hesamyaghoubii"
              "@puyaghsmi"]

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








}

def te(key):
    e = MSG_EMOJIS.get(key)
    if e and e["id"]:
        return f'<tg-emoji emoji-id="{e["id"]}">{e["char"]}</tg-emoji>'
    return e["char"] if e else ""

BTN_CFG = {
    "buy_new":          {"text": "خرید اشتراک جدید",    "style": "primary",  "emoji_id": "5348270285466385224"},
    "renew":            {"text": "تمدید اشتراک",        "style": "primary",  "emoji_id": "4956418939920843885"},
    "referral": {"text": "زیر مجموعه(رفرال)", "style": "primary", "emoji_id": "5350790271627968474"},
    "my_services":      {"text": "سرویس‌های من",       "style": "primary",  "emoji_id": "5409380072291316349"},
    "profile":          {"text": "پروفایل من",          "style": "primary",  "emoji_id": "5348136664738839786"},
    "news":             {"text": "آموزش و اخبار",       "style": "primary",  "emoji_id": "4956436416142771580"},
    "support":          {"text": "پشتیبانی",            "style": "primary",  "emoji_id": "5979065840102810733"},
    "back":             {"text": "بازگشت",              "style": "danger",  "emoji_id": "5972120066236357644"},
    "test_server":      {"text": "سرور تست رایگان",    "style": "success",  "emoji_id": "5348440533675031854"},
    "admin_add_plan":   {"text": "افزودن پلن",          "style": "primary",  "emoji_id": "4956232383721374836"},
    "admin_del_plan":   {"text": "حذف پلن",             "style": "primary",  "emoji_id": "4956475826762679249"},
    "admin_users":      {"text": "لیست کاربران",        "style": "primary",  "emoji_id": "5974235702701853774"},
    "admin_products":   {"text": "محصولات",             "style": "primary",  "emoji_id": "5409380072291316349"},
    "admin_broadcast":  {"text": "پیام همگانی",         "style": "primary",  "emoji_id": "5972240522889138094"},
    "admin_dm":         {"text": "پیام به کاربر",       "style": "primary",  "emoji_id": "5852830669599674051"},
    "admin_channels":   {"text": "مدیریت کانال‌ها",   "style": "primary",  "emoji_id": "4992622834166530981"},
    "admin_set_test":   {"text": "تنظیم سرور تست",     "style": "primary",  "emoji_id": "4958725487682650920"},
    "admin_add_server": {"text": "افزودن سرور", "style": "primary", "emoji_id": "4958725487682650920"},
    "admin_server_stats":{"text": "آمار سرورها","style": "primary", "emoji_id": "5409380072291316349"},
    "admin_receipts":{"text": "رسید های واریزی","style": "primary","emoji_id": "5350697092184944245"},
    "admin_referrals": {"text": "سیستم رفرال","style": "primary","emoji_id": "5350790271627968474"},
}

DYN_BTN_EMOJIS = {
    "channel_join":  "5350356823528455446",
    "check_join":    "5972326417940093090",
    "plan_item":     "4956232383721374836",
    "renew_item":    "4956418939920843885",
    "del_item":      "4956475826762679249",
    "add_item":      "4958725487682650920",
    "success_btn":   "6316422138085514606",
    "PRIME": "5350618807943576963",
    "month":         "4958686613933655185",
    "copy_btn":      "5987636855363867398",
    "back": "5972120066236357644",
    "support":"5979065840102810733",
    "accept":"5348404473129614535",
    "special":"5967337229310238293",
    "join":"5350835008007324644"

}

(
    GET_RECEIPT,
    RENEW_GET_RECEIPT,
    ADD_NAME,
    ADD_PRICE,
    BROADCAST_STATE,
    GET_DM_USER_ID,
    GET_DM_MESSAGE,
    MANAGE_CHANNELS,
    ADD_CHANNEL_USER,
    ADD_CHANNEL_LINK,
    DEL_CHANNEL_INDEX,
    SET_TEST_SERVER,
    SET_SERVER,
    BUY_SELECT_PLAN,
    BUY_SELECT_VOLUME,
    BUY_GET_COUNT,
    BUY_CONFIRM_RULES,
    TEST_SERVER_STATE,
    TEST_SERVER_INPUT
) = range(19)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

DURATION_MAP = {
    "vip": ("=vip ", 30),
    "prime": ("prime ", 60)
}

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
    "settings": {"channels": [], "test_servers": [], "servers": [],"server_session": {}},
    "users": {},
    "plans": [{"name": "تست رایگان", "price": 0, "id": 1234}],
    "receipts": []
}
        return default_data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            db = json.load(f)
            db.setdefault("receipts", [])
            db.setdefault("settings", {"channels": [], "test_server": ""})
            db["settings"].setdefault("test_servers", [])
            db["settings"].setdefault("servers", [])
            if "gift_volume" in db["settings"]: del db["settings"]["gift_volume"]
            db.setdefault("plans", [])
            db.setdefault("users", {})
            for uid, u_data in db["users"].items():
                if "invited" in u_data: del u_data["invited"]
                u_data.setdefault("has_test", False)
            return db
        except: return {"settings": {"channels": [], "test_server": ""}, "users": {}, "plans": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def create_btn(config_key, callback_data=None, url=None):
    cfg = BTN_CFG[config_key]
    kwargs = {"text": cfg["text"], "style": cfg.get("style", "primary")}

    if cfg.get("emoji_id"):
        kwargs["icon_custom_emoji_id"] = cfg["emoji_id"]

    if url:
        kwargs["url"] = url
    else:
        kwargs["callback_data"] = callback_data

    return InlineKeyboardButton(**kwargs)


def get_real_invited_count(user_id):
    db = load_db()
    count = 0

    for uid, user in db["users"].items():
        if user.get("inviter") == str(user_id) and user.get("is_active"):
            count += 1

    return count

def get_invited_buy_count(user_id):
    db = load_db()
    count = 0

    for uid, user in db["users"].items():
        if user.get("inviter") == str(user_id) and user.get("services"):
            count += 1

    return count


def get_user_buy_count(user_id):
    db = load_db()
    user = db["users"].get(str(user_id), {})
    return len(user.get("services", []))


def get_active_servers(user_id):
    db = load_db()
    services = db["users"].get(str(user_id), {}).get("services", [])

    active = 0
    now = datetime.now().timestamp()

    for s in services:
        if isinstance(s, dict) and s.get("expiry_ts", 0) > now:
            active += 1

    return active

def main_menu_kb():
    return InlineKeyboardMarkup([
        [create_btn("buy_new", "menu_buy")],
        [create_btn("referral", "profile_referral")],
        [create_btn("test_server", "menu_test")],

        [
            create_btn("profile", "menu_profile"),
            create_btn("support", "menu_support")
        ],
    ])

def admin_menu_kb():
    return InlineKeyboardMarkup([
        [create_btn("admin_add_plan", "admin_add_plan"), create_btn("admin_del_plan", "admin_del_plan")],
        [create_btn("admin_users", "admin_users"), create_btn("admin_products", "admin_products")],
        [create_btn("admin_broadcast", "admin_broadcast"), create_btn("admin_dm", "admin_dm")],
        [create_btn("admin_channels", "admin_channels"), create_btn("admin_set_test", "admin_set_test")],
        [create_btn("admin_add_server", "admin_add_server")],
        [create_btn("admin_server_stats", "admin_server_stats")],
        [create_btn("admin_receipts", "admin_receipts")],
        [create_btn("admin_referrals", "admin_referrals")],
    ])

def back_kb(target="main"):
    return InlineKeyboardMarkup([[create_btn("back", f"back_{target}")]])

def payment_invoice_kb(card: str, amount: int):
    return InlineKeyboardMarkup([
        [
        InlineKeyboardButton(
    "کپی شماره کارت",
    style="primary",
    icon_custom_emoji_id=DYN_BTN_EMOJIS["copy_btn"],
    copy_text=card
),
InlineKeyboardButton(
    "کپی مبلغ",
    style="primary",
    icon_custom_emoji_id=DYN_BTN_EMOJIS["copy_btn"],
    copy_text=str(int(amount) * 10)
)
        ],
        [create_btn("back", "back_main")],
    ])
def extract_number(text: str):
    if not text:
        return None

    text = text.replace("۰","0").replace("۱","1").replace("۲","2").replace("۳","3").replace("۴","4").replace("۵","5").replace("۶","6").replace("۷","7").replace("۸","8").replace("۹","9")

    cleaned = re.sub(r"[^\d]", "", text)

    return int(cleaned) if cleaned else None    
    
async def set_menu_button(app):
    await app.bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )
    
async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS: return True
    db = load_db()
    channels = db["settings"].get("channels", [])
    if not channels: return True
    not_joined = False
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch["username"], user_id)
            if member.status in ['left', 'kicked']: not_joined = True; break
        except: not_joined = True; break
    if not_joined:
        markup_keys = []
        for ch in channels:
            markup_keys.append([InlineKeyboardButton(f"عضویت در {ch['username']}", url=ch['link'], style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["join"])])
        markup_keys.append([InlineKeyboardButton("بررسی عضویت", callback_data="check_join_btn", style="success", icon_custom_emoji_id=DYN_BTN_EMOJIS["check_join"])])
        msg = f"{te('gift')} برای استفاده از ربات، لطفاً ابتدا در تمامی کانال‌های زیر عضو شوید:"
        if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(markup_keys), parse_mode="HTML")
        elif update.callback_query:
            try: await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(markup_keys), parse_mode="HTML")
            except: pass
        return False
    db = load_db()
    uid = str(user_id)

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
            if member.status in ['left', 'kicked']: all_joined = False; break
        except: all_joined = False; break
    if not all_joined:
        await query.answer("هنوز در همه کانال‌ها عضو نشده‌اید!", show_alert=True)
    else:
        await query.answer("عضویت شما تایید شد!", show_alert=True)
        await query.message.delete()
        await context.bot.send_message(user_id, f"{te('welcome')} <b>به صدورا بات خوش آمدید</b>\n\n{te('bullet')}برای ادامه گزینه مورد نظر خود را انتخاب کنید", reply_markup=main_menu_kb(), parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    if context.args:
        ref = context.args[0]
        if ref.startswith("ref_"):
            inviter = ref.split("_")[1]
    if uid not in db["users"]:

        inviter = None

        if context.args:
            ref = context.args[0]
            if ref.startswith("ref_"):
                inviter = ref.split("_")[1]

        db["users"][uid] = {
    "name": update.effective_user.first_name,
    "username": update.effective_user.username,
    "services": [],
    "pending_order": None,
    "has_test": False,
    "inviter": inviter,
    "is_active": True
}

        save_db(db)
    if not await check_force_join(update, context): return ConversationHandler.END
    msg = f"{te('welcome')} <b>به صدورا بات خوش آمدید</b>\n\n{te('bullet')}برای ادامه گزینه مورد نظر را انتخاب کنید"
    last_id = context.user_data.get("last_menu_msg_id")
    if last_id and update.message:
        try: await context.bot.delete_message(update.effective_chat.id, last_id)
        except: pass
    if update.message:
        try: await update.message.delete()
        except: pass
        sent = await context.bot.send_message(update.effective_chat.id, msg, reply_markup=main_menu_kb(), parse_mode="HTML")
        context.user_data["last_menu_msg_id"] = sent.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=main_menu_kb(), parse_mode="HTML")
        context.user_data["last_menu_msg_id"] = update.callback_query.message.message_id
    return ConversationHandler.END

async def support_handler(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
    [
        InlineKeyboardButton(
            "ارتباط با پشتیبانی",
            url="https://t.me/hesamyaghoubii",
            style="primary",
            icon_custom_emoji_id=DYN_BTN_EMOJIS["support"]
        )
    ],
    [
        InlineKeyboardButton(
            "بازگشت",
            callback_data="back_main",
            style="danger",
            icon_custom_emoji_id=DYN_BTN_EMOJIS["back"]
        )
    ]
]

    try:
        await query.message.edit_text(
            "برای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await context.bot.send_message(
            query.from_user.id,
            "برای ارتباط با پشتیبانی:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(f"{te('error')} عملیات لغو شد.\nبه منوی اصلی بازگشتید:", reply_markup=main_menu_kb(), parse_mode="HTML")
    return ConversationHandler.END

async def my_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await check_force_join(update, context): return
    uid = str(query.from_user.id)
    services = load_db()["users"].get(uid, {}).get("services", [])
    if not services:
        await query.message.edit_text(f"{te('error')} شما هیچ سرویس فعالی ندارید.", reply_markup=back_kb(), parse_mode="HTML")
        return
    await query.message.delete()
    await context.bot.send_message(uid, f"{te('rocket')} <b>سرویس‌های شما:</b>", parse_mode="HTML")
    now_ts = datetime.now().timestamp()
    for s in services:
        if isinstance(s, str): continue
        remaining = int((s.get("expiry_ts", 0) - now_ts) / 86400)
        status = f"{te('active')} فعال" if remaining > 0 else f"{te('expired')} منقضی"
        caption = f"{te('id_tag')} کد اشتراک: <code>{s.get('sub_id', '---')}</code>\n{te('box')} پلن: {s.get('name')}\n{te('time')} مانده: {remaining} روز\nوضعیت: {status}"
        if "photo_id" in s: await context.bot.send_photo(uid, s["photo_id"], caption=caption, parse_mode="HTML")
        else: await context.bot.send_message(uid, caption, parse_mode="HTML")
    await context.bot.send_message(uid, "جهت بازگشت به منو کلیک کنید:", reply_markup=back_kb())

async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await check_force_join(update, context): return
    await query.message.edit_text(f"{te('profile')} نام: {query.from_user.first_name}\n{te('id_tag')} شناسه عددی: <code>{query.from_user.id}</code>", parse_mode="HTML", reply_markup=back_kb())

async def show_channels_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channels = load_db()["settings"].get("channels", [])
    if not channels:
        await query.message.edit_text(f"{te('error')} در حال حاضر کانالی ثبت نشده است.", reply_markup=back_kb(), parse_mode="HTML")
        return
    text = f"{te('book')} <b>کانال‌های ما:</b>\n\n"
    for ch in channels: text += f"{te('bullet')} <a href='{ch['link']}'>{ch['username']}</a>\n"
    await query.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_kb())

async def test_server_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await check_force_join(update, context): return
    uid = str(query.from_user.id)
    db = load_db()
    if db["users"].get(uid, {}).get("has_test"):
        await query.message.edit_text(f"{te('error')} <b>شما قبلاً سرور تست دریافت کرده‌اید.</b>\n\nهر کاربر فقط یک بار می‌تواند سرور تست رایگان دریافت کند.", parse_mode="HTML", reply_markup=back_kb())
        return
    test_servers = db["settings"].get("test_servers", [])
    if not test_servers:
        await query.message.edit_text(f"{te('warning')} <b>سرور تست در حال حاضر در دسترس نیست.</b>\n\nلطفاً بعداً مراجعه کنید یا با پشتیبانی تماس بگیرید.", parse_mode="HTML", reply_markup=back_kb())
        return

    config = test_servers.pop(0) 
    db["users"][uid]["has_test"] = True
    save_db(db)
    await query.message.edit_text(
        f"{te('test')} <b>سرور تست رایگان شما:</b>\n\n<code>{config}</code>\n\n{te('warning')} این سرور فقط برای تست است و دارای محدودیت می‌باشد.",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    buttons = [
        [InlineKeyboardButton("VIP", callback_data="buy_VIP", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["PRIME"])],
        [create_btn("back", "back_main")],
    ]

    await query.message.edit_text(
        f"{te('pin')} پلن مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

    return BUY_SELECT_PLAN

async def buy_select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["plan"] = "VIP"

    buttons = [
        [
            InlineKeyboardButton(
                "1GB - 290,000",
                callback_data="buy_vol_1",
                style="primary",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["PRIME"]
            )
        ],
        [
            InlineKeyboardButton(
                "2GB - 580,000",
                callback_data="buy_vol_2",
                style="primary",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["PRIME"]
            )
        ],
        [
            InlineKeyboardButton(
                "3GB - 870,000",
                callback_data="buy_vol_3",
                style="primary",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["PRIME"]
            )
        ],
        [
            InlineKeyboardButton(
                "5 گیگ بخر 7 گیگ ببر - 1,450,000",
                callback_data="buy_vol_5",
                style="success",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["special"]
            )
        ],
        [
            InlineKeyboardButton(
                "10GB - 2,900,00",
                callback_data="buy_vol_5",
                style="primary",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["PRIME"]
            )
        ],        
        [create_btn("back", "back_main")],
    ]

    await query.message.edit_text(
        f"{te('box')} حجم مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

    return BUY_SELECT_VOLUME

async def buy_select_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    volume_map = {
        "buy_vol_1": ("1GB", 290000),
        "buy_vol_2": ("2GB", 580000),
        "buy_vol_3": ("5GB", 870000),
        "buy_vol_10": ("5GB", 2900000),
        "buy_vol_5": ("5گیگ بخر 7 گیگ ببر", 1450000),
    }

    volume, price = volume_map.get(query.data, ("نامشخص", 0))

    context.user_data["volume"] = volume
    context.user_data["price"] = price

    await query.message.edit_text(
    f"{te('box')} حجم انتخاب شد: {volume}\n\n"
    f"{te('money')} قیمت هر عدد: {price:,} تومان\n\n"
    f"{te('NUMBER')} تعداد اکانت مورد نظر را وارد کنید:",
    parse_mode="HTML",
    reply_markup=back_kb()
)
    return BUY_GET_COUNT    

async def buy_get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
    except ValueError:
        await update.message.reply_text("فقط عدد وارد کنید.")
        return BUY_GET_COUNT

    context.user_data["count"] = count

    base_price = context.user_data.get("price", 0)
    total = base_price * count
    context.user_data["total"] = total

    buttons = [
    [
        InlineKeyboardButton(
            "قوانین را میپذیرم",
            callback_data="accept_rules",
            style="success",
            icon_custom_emoji_id=DYN_BTN_EMOJIS["accept"]
        )
    ],
    [
        InlineKeyboardButton(
            "بازگشت",
            callback_data="back_main",
            style="danger",
            icon_custom_emoji_id=DYN_BTN_EMOJIS["back"]
        )
    ]
]
    text = (
        f"{te('rule')} قبل از خرید قوانین را تایید کنید.\n\n"

        f"{te('rules')} در صورت نارضایتی مشتری، تا ۲۴ ساعت بعد از خرید حجم مصرفی محاسبه شده و مبلغ باقی‌مانده به شما بازگردانده می‌شود یا سرور جایگزین ارسال می‌شود.\n\n"

        f"{te('rules')} فقط در صورت حادثه یا خاموشی دیتاسنتر حاصل از جنگ سرورهای ما قطع می‌شود و مسئولیت آن با ما نیست.\n\n"

        f"{te('rules')} احتمال قطعی کم وجود دارد، سرور های ما پایدار هستند ، ولی قطعی‌ها بسیار کم و سریع رفع می‌شوند.\n\n"

        f"{te('rules')} سرور دارای ساب‌لینک است؛ بعد از ارسال سرور، مسئولیت مصرف حجم و نحوه استفاده بر عهده مشتری می‌باشد.\n\n"

        f"{te('rules')} سرویس‌ها بدون محدودیت زمانی و بدون محدودیت کاربر ارائه می‌شوند.\n\n"

        f"{te('support')} پشتیبانی به‌صورت ۲۴ ساعته در خدمت شماست."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

    return BUY_CONFIRM_RULES

async def buy_confirm_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan = context.user_data["plan"]
    volume = context.user_data["volume"]
    count = context.user_data["count"]
    total = context.user_data["total"]

    exact_amount = total + random.randint(100, 999)
    context.user_data["exact_amount"] = exact_amount

    msg = (
        f"{te('card')} <b>فاکتور پرداخت</b>\n\n"
        f"{te('diamond')}  پلن:  {plan}\n\n"
        f"{te('box')} حجم: {volume}\n\n"
        f"{te('NUMBER')} تعداد: {count}\n\n"
        f"{te('money')} مبلغ قابل پرداخت:\n\n"
        f"{te('money')} <code>{exact_amount:,}</code> تومان\n\n"
        f"{te('card')} شماره کارت:\n\n"
        f"{te('card')} <code>{CARD_NUMBER}</code>\n\n"
        f"{te('stars')} پس از واریز عکس رسید را ارسال کنید:\n"
        f"<b>(در مبلغ پرداختی دقت فرمایید؛ در صورت مغایرت با مبلغ اعلام‌شده، رسید شما تایید نخواهد شد.)</b>\n\n"        
    )

    await query.message.edit_text(
        msg,
        parse_mode="HTML",
        reply_markup=payment_invoice_kb(CARD_NUMBER, exact_amount)
    )

    return GET_RECEIPT


async def buy_handle_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = next((p for p in load_db()["plans"] if p["id"] == int(query.data.split("_")[2])), None)
    if not plan:
        await query.message.edit_text(f"{te('error')} پلن نامعتبر است.", reply_markup=back_kb(), parse_mode="HTML")
        return ConversationHandler.END
    context.user_data["buy_plan"] = plan
    exact_amount = plan["price"] + random.randint(100, 999)
    context.user_data["exact_amount"] = exact_amount
    msg = (
        f"{te('card')} <b>فاکتور پرداخت</b>\n\n"
        f"{te('box')} سرویس: {plan['name']}\n"
        f"{te('money')} مبلغ دقیق واریز: <code>{exact_amount:,}</code> تومان\n\n"
        f"{te('warning')} <b>لطفاً دقیقاً همین مبلغ را واریز کنید</b> تا پرداخت شما شناسایی شود.\n\n"
        f"{te('card')} شماره کارت:\n<code>{CARD_NUMBER}</code>\n\n"
        f"پس از واریز، <b>عکس رسید</b> را همینجا ارسال کنید."
    )
    await query.message.edit_text(msg, parse_mode="HTML", reply_markup=payment_invoice_kb(CARD_NUMBER, exact_amount))
    return GET_RECEIPT

async def buy_VIP(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan = load_db()["plans"][0]  # یا هر پلن VIP که داری
    context.user_data["buy_plan"] = plan

    exact_amount = plan["price"] + random.randint(100, 999)
    context.user_data["exact_amount"] = exact_amount

    msg = (
        f"💳 <b>فاکتور VIP</b>\n\n"
        f"💎 سرویس: VIP\n\n"
        f"💰 مبلغ: <code>{exact_amount:,}</code> تومان\n\n"
        f"شماره کارت:\n\n<code>{CARD_NUMBER}</code>\n\n"
        "بعد از پرداخت، رسید را ارسال کنید."
    )

    await query.message.edit_text(
        msg,
        parse_mode="HTML",
        reply_markup=payment_invoice_kb(CARD_NUMBER, exact_amount)
    )

    return GET_RECEIPT

async def buy_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.photo:
        return await update.message.reply_text(
            f"{te('error')} لطفا عکس رسید پرداخت را ارسال کنید.",
            parse_mode="HTML"
)
    file_id = update.message.photo[-1].file_id

    uid = str(update.effective_user.id)

    plan = context.user_data.get("plan", "نامشخص")
    volume = context.user_data.get("volume", "نامشخص")
    count = context.user_data.get("count", 1)
    exact_amount = context.user_data.get("exact_amount", 0)

    db = load_db()

    if uid not in db["users"]:
        db["users"][uid] = {}

    db["users"][uid]["pending_order"] = {
        "type": "new",
        "plan": plan,
        "volume": volume,
        "count": count,
        "date": str(datetime.now()),
        "exact_amount": exact_amount
    }
    db["receipts"].append({
    "user_id": uid,
    "username": update.effective_user.username,
    "plan": plan,
    "volume": volume,
    "count": count,
    "price": exact_amount,
    "photo": file_id,
    "status": "pending"
})

    save_db(db)

    await update.message.reply_text(
        f"""{te('sedora')} <b>رسید شما دریافت شد</b>

{te('time')} سفارش شما در انتظار تایید ادمین است. """,
        parse_mode="HTML"
    )

    admin_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "تایید و ارسال سرور",
                callback_data=f"adm_approve_{uid}_new",
                style="success",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["success_btn"]
            )
        ],
        [
            InlineKeyboardButton(
                "رد سفارش",
                callback_data=f"adm_reject_{uid}",
                style="danger",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["del_item"]
            )
        ]
    ])

    for admin in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin,
                photo=update.message.photo[-1].file_id,
                caption=f"""
{te('mail')} <b>سفارش جدید</b>

{te('profile')} کاربر
<code>{uid}</code>

{te('diamond')} پلن
<code>{plan}</code>

{te('box')} حجم
<code>{volume}</code>

{te('number')} تعداد
<code>{count}</code>

{te('money')} مبلغ
<code>{exact_amount:,}</code> تومان
""",
                parse_mode="HTML",
                reply_markup=admin_markup
            )
        except Exception as e:
            print("ADMIN SEND ERROR:", e)

    return ConversationHandler.END

async def admin_receipts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    kb = [
        [
            InlineKeyboardButton(
                "⏳ در انتظار بررسی",
                callback_data="receipts_pending"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 تایید / رد شده",
                callback_data="receipts_archive"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_admin"
            )
        ]
    ]

    await query.message.edit_text(
        "مدیریت رسید ها:",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def show_pending_receipts(update, context):

    query = update.callback_query
    await query.answer()

    db = load_db()

    receipts = [
        (i, r)
        for i, r in enumerate(db["receipts"])
        if r.get("status") == "pending"
    ]

    receipts.reverse()  # جدیدترین بالا

    page = int(query.data.split("_")[-1]) if "page_" in query.data else 0

    per_page = 5

    start = page * per_page
    end = start + per_page

    page_items = receipts[start:end]

    kb = []

    for i, r in page_items:

        kb.append([
            InlineKeyboardButton(
                f"⏳ رسید {r['user_id']}",
                callback_data=f"view_receipt_{i}"
            )
        ])

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"receipts_pending_page_{page-1}"
            )
        )

    if end < len(receipts):
        nav.append(
            InlineKeyboardButton(
                "➡️ بعدی",
                callback_data=f"receipts_pending_page_{page+1}"
            )
        )

    if nav:
        kb.append(nav)

    kb.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_receipts"
        )
    ])

    await query.message.edit_text(
        f"⏳ رسید های در انتظار\n\nصفحه {page + 1}",
        reply_markup=InlineKeyboardMarkup(kb)
    )  


async def show_archive_receipts(update, context):

    query = update.callback_query
    await query.answer()

    db = load_db()

    receipts = [
        (i, r)
        for i, r in enumerate(db["receipts"])
        if r.get("status") in ["approved", "rejected"]
    ]

    kb = []

    for i, r in receipts:

        status = "✅" if r["status"] == "approved" else "❌"

        kb.append([
            InlineKeyboardButton(
                f"{status} رسید {r['user_id']}",
                callback_data=f"view_receipt_{i}"
            )
        ])

    kb.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="admin_receipts"
        )
    ])

    await query.message.edit_text(
        "📁 آرشیو رسید ها:",
        reply_markup=InlineKeyboardMarkup(kb)
    )    

async def view_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[-1])

    db = load_db()
    if index >= len(db["receipts"]):

        await query.answer(
            "رسید یافت نشد",
            show_alert=True
        )
        return    
    receipt = db["receipts"][index]

    uid = receipt["user_id"]
    user_data = db["users"].get(str(uid), {})

    text = f"""
📥 سفارش جدید

👤 کاربر: {uid}
🔗 یوزرنیم: @{receipt.get('username', '---')}

📦 پلن: {receipt.get('plan', '---')}
📦 حجم: {receipt.get('volume', '---')}
🔢 تعداد: {receipt.get('count', '---')}

💰 مبلغ: {receipt.get('price', 0):,} تومان
"""

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ تایید",
                callback_data=f"approve_receipt_{index}"
            ),
            InlineKeyboardButton(
                "❌ رد",
                callback_data=f"reject_receipt_{index}"
            )
        ]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_IDS[0],
        photo=receipt["photo"],
        caption=text,
        reply_markup=kb
    )


async def approve_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.replace("approve_receipt_", ""))

    db = load_db()

    if index >= len(db["receipts"]):
        await query.message.reply_text("رسید پیدا نشد")
        return

    receipt = db["receipts"][index]

    if receipt.get("status") != "pending":

        await query.answer(
            "این رسید قبلاً بررسی شده",
            show_alert=True
        )
        return

    uid = str(receipt["user_id"])

    user = db["users"].get(uid)

    if not user:
        await query.message.reply_text("کاربر پیدا نشد")
        return

    pending = user.get("pending_order")

    if not pending:
        await query.message.reply_text("pending_order وجود ندارد")
        return

    servers = db["settings"].get("servers", [])

    if not servers:
        await query.message.reply_text("سرور نداریم")
        return

    config = servers.pop(0)

    user.setdefault("services", []).append({
        "sub_id": config,
        "name": pending.get("plan", "unknown"),
        "start_ts": datetime.now().timestamp(),
        "expiry_ts": datetime.now().timestamp() + 30 * 86400
    })

    user["pending_order"] = None

    db["receipts"][index]["status"] = "approved"

    save_db(db)

    await context.bot.send_message(
        chat_id=uid,
        text=(
            f"{te('taeid')} <b>پرداخت تایید شد</b>\n\n"
            f"<code>{config}</code>"
        ),
        parse_mode="HTML"
    )

    await query.message.edit_caption("✅ ارسال شد")

async def reject_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[-1])

    db = load_db()
    db["receipts"][index]["status"] = "rejected"
    save_db(db)
    await query.message.edit_caption(
        "❌ رسید رد شد"
    )            

async def profile_menu(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
    [
        InlineKeyboardButton(
            "اطلاعات حساب",
            callback_data="profile_info",
            style="primary",
            icon_custom_emoji_id=MSG_EMOJIS["profile"]["id"]
        )
    ],
    [
        InlineKeyboardButton(
            "تاریخچه خرید",
            callback_data="profile_orders",
            style="primary",            
            icon_custom_emoji_id=MSG_EMOJIS["orders"]["id"]
        )
    ],
    [
        InlineKeyboardButton(
            "سرورهای من",
            callback_data="profile_servers",
            style="primary",            
            icon_custom_emoji_id=MSG_EMOJIS["servers"]["id"]
        )
    ],
    [
        InlineKeyboardButton(
            "بازگشت",
            callback_data="back_main",
            style="danger",
            icon_custom_emoji_id=MSG_EMOJIS["back"]["id"]
        )
    ],
]

    await query.message.edit_text(
    f"{te('profile')} پنل کاربری شما\n\n"
    f"{te('paein')} یکی از گزینه‌ها را انتخاب کنید:",
    reply_markup=InlineKeyboardMarkup(keyboard),
    parse_mode="HTML"
)

async def profile_referral(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot_username = (await context.bot.get_me()).username

    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    invited_count = get_real_invited_count(user_id)  # از دیتابیس

    remaining_invites = max(0, 10 - invited_count)

    text = f"""
{te('hand')} <b>سیستم دعوت دوستان</b>

{te('link')} <b>لینک دعوت شما:</b>

{referral_link}

{te('invite')} <b>تعداد دعوت‌ها:</b> {invited_count}
{te('stars')} <b>تعداد باقی مانده تا هدیه:</b> {remaining_invites}

{te('gift')} <b>با دعوت 10 نفر از دوستان خود و فوروارد پیام ربات به پشتیبانی، سرویس هدیه ویژه صدورا را دریافت کنید.</b>"""

    keyboard = [
        [
            InlineKeyboardButton(
                " ارتباط با پشتیبانی",
                style="success",
                url="https://t.me/hesamyaghoubii",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["support"]
            )
        ],

        [
            InlineKeyboardButton(
                " بازگشت",
                style="danger",
                callback_data="back_main",
                icon_custom_emoji_id=DYN_BTN_EMOJIS["back"]
                
            )
        ]
    ]
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def profile_info(update, context):
    query = update.callback_query
    await query.answer()

    # چک عضویت اجباری مثل بقیه بخش‌ها
    if not await check_force_join(update, context):
        return

    user_id = query.from_user.id

    buy_count = get_user_buy_count(user_id)
    active_servers = get_active_servers(user_id)

    text = f"""
<tg-emoji emoji-id="{MSG_EMOJIS['stats']['id']}">{MSG_EMOJIS['stats']['char']}</tg-emoji> اطلاعات حساب شما

<tg-emoji emoji-id="{MSG_EMOJIS['profile']['id']}">{MSG_EMOJIS['profile']['char']}</tg-emoji> آیدی کاربر: <code>{user_id}</code>

<tg-emoji emoji-id="{MSG_EMOJIS['card']['id']}">{MSG_EMOJIS['card']['char']}</tg-emoji> تعداد خریدها: {buy_count}
<tg-emoji emoji-id="{MSG_EMOJIS['box']['id']}">{MSG_EMOJIS['box']['char']}</tg-emoji> سرورهای فعال: {active_servers}
"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"{MSG_EMOJIS['back']['char']} بازگشت",
                style="danger",
                callback_data="back_main",
            )
        ]
    ])

    await query.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def profile_orders(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    db = load_db()

    services = db["users"].get(user_id, {}).get("services", [])

    if not services:
        text = f"<tg-emoji emoji-id='{MSG_EMOJIS['not']['id']}'>{MSG_EMOJIS['not']['char']}</tg-emoji> شما هنوز خریدی ثبت نکرده‌اید."
    else:
        text = " تاریخچه خرید شما:\n\n"
        for s in services:
            if isinstance(s, dict):
                text += f"• {s.get('name')} | کد: {s.get('sub_id','---')}\n"

    Keyboard = [[InlineKeyboardButton(f"{MSG_EMOJIS['back']['char']} بازگشت", style="danger", callback_data="menu_profile")]]

    await query.message.edit_text(
    text,
    reply_markup=InlineKeyboardMarkup(Keyboard),
    parse_mode="HTML"
)

async def profile_servers(update, context):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    db = load_db()

    services = db["users"].get(user_id, {}).get("services", [])

    if not services:
        text = f"<tg-emoji emoji-id='{MSG_EMOJIS['not']['id']}'></tg-emoji> شما سرور فعالی ندارید."
    else:
        text = f"<tg-emoji emoji-id='{MSG_EMOJIS['servers']['id']}'>{MSG_EMOJIS['servers']['char']}</tg-emoji> سرورهای شما:\n\n"

        for s in services:
            if isinstance(s, dict):
                text += f"🔹 {s.get('sub_id','---')}\n"

    keyboard = [[
        InlineKeyboardButton(
            f"{MSG_EMOJIS['back']['char']} بازگشت",
            style="danger",
            callback_data="menu_profile"
        )
    ]]

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def renew_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    services = load_db()["users"].get(str(query.from_user.id), {}).get("services", [])
    if not services:
        await query.message.edit_text(f"{te('error')} شما سرویسی برای تمدید ندارید.", reply_markup=back_kb(), parse_mode="HTML")
        return ConversationHandler.END
    btns = [[InlineKeyboardButton(f"کد: {s.get('sub_id', '---')} - {s['name']}", callback_data=f"ren_svc_{idx}", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["renew_item"])] for idx, s in enumerate(services) if isinstance(s, dict)]
    btns.append([create_btn("back", "back_main")])
    await query.message.edit_text(f"{te('refresh')} کدام اشتراک را تمدید می‌کنید؟", reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")
    return RENEW_GET_RECEIPT

async def renew_select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["renew_service_idx"] = int(query.data.split("_")[2])
    btns = [
        [InlineKeyboardButton("یک ماهه", callback_data="ren_dur_1m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"]), InlineKeyboardButton("دو ماهه", callback_data="ren_dur_2m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"])],
        [InlineKeyboardButton("سه ماهه", callback_data="ren_dur_3m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"]), InlineKeyboardButton("شش ماهه", callback_data="ren_dur_6m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"])],
        [create_btn("back", "back_main")]
    ]
    await query.message.edit_text(f"{te('time')} مدت تمدید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")

async def renew_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    duration_text = DURATION_MAP.get(query.data.split("_")[2], ("نامشخص", 0))[0]
    context.user_data["renew_duration"] = duration_text
    found_plan = next((p for p in load_db()["plans"] if duration_text in p["name"]), None)
    base_price = found_plan["price"] if found_plan else 0
    exact_amount = base_price + random.randint(100, 999) if base_price else 0
    context.user_data["renew_exact_amount"] = exact_amount
    price_txt = f"{exact_amount:,}" if exact_amount else "توافقی"
    msg = (
        f"{te('card')} <b>فاکتور تمدید</b>\n\n"
        f"{te('time')} مدت: {duration_text}\n"
        f"{te('money')} مبلغ دقیق واریز: <code>{price_txt}</code> تومان\n\n"
        f"{te('warning')} <b>لطفاً دقیقاً همین مبلغ را واریز کنید</b> تا پرداخت شما شناسایی شود.\n\n"
        f"{te('card')} شماره کارت:\n<code>{CARD_NUMBER}</code>\n\n"
        f"پس از واریز عکس رسید را ارسال کنید(روی دکمه ی کپی مبلغ برای اطمینان حاصل شدن از درست بودن هزینه پرداختی کلیک کنید)"
    )
    kb = payment_invoice_kb(CARD_NUMBER, exact_amount) if exact_amount else back_kb()
    await query.message.edit_text(msg, parse_mode="HTML", reply_markup=kb)
    return RENEW_GET_RECEIPT

async def renew_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return await update.message.reply_text(f"{te('error')} عکس رسید ارسال کنید.", reply_markup=back_kb(), parse_mode="HTML") and RENEW_GET_RECEIPT
    uid = str(update.effective_user.id)
    svc_idx = context.user_data.get("renew_service_idx")
    duration = context.user_data.get("renew_duration")
    exact_amount = context.user_data.get("renew_exact_amount", 0)
    db = load_db()
    sub_id = db["users"][uid]["services"][svc_idx].get("sub_id", "---")
    db["users"][uid]["pending_order"] = {"type": "renew", "service_idx": svc_idx, "duration_txt": duration, "sub_id": sub_id, "exact_amount": exact_amount}
    save_db(db)
    admin_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید تمدید", callback_data=f"adm_approve_{uid}_renew", style="success", icon_custom_emoji_id=DYN_BTN_EMOJIS["success_btn"])],
        [InlineKeyboardButton("رد", callback_data=f"adm_reject_{uid}", style="danger", icon_custom_emoji_id=DYN_BTN_EMOJIS["del_item"])]
    ])
    await update.message.reply_text(f"{te('success')} درخواست تمدید ثبت شد.", reply_markup=main_menu_kb(), parse_mode="HTML")
    for admin in ADMIN_IDS:
        try: await context.bot.send_photo(admin, update.message.photo[-1].file_id, caption=f"{te('refresh')} <b>درخواست تمدید</b>\n{te('profile')} کاربر: <code>{uid}</code>\n{te('id_tag')} کد: <code>{sub_id}</code>\n{te('time')} تمدید برای: {duration}\n{te('money')} مبلغ واریزی: {exact_amount:,}", parse_mode="HTML", reply_markup=admin_markup)
        except: pass
    return ConversationHandler.END


async def admin_referral_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()
    ref_map = {}

    # ساخت لیست دعوت‌کننده‌ها
    for uid, user in db["users"].items():
        inviter = user.get("inviter")
        if inviter:
            ref_map.setdefault(inviter, []).append(uid)

    if not ref_map:
        await query.message.edit_text(
            "هیچ رفرالی ثبت نشده است.",
            reply_markup=back_kb("admin")
        )
        return

    keyboard = []

    for inviter_id, invited_list in ref_map.items():
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {inviter_id} ({len(invited_list)})",
                callback_data=f"ref_user_{inviter_id}"
            )
        ])

    keyboard.append([create_btn("back", "back_admin")])

    await query.message.edit_text(
        "📊 لیست رفرال کاربران:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def admin_referral_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    inviter_id = query.data.split("_")[2]

    db = load_db()

    invited = []

    for uid, user in db["users"].items():
        if user.get("inviter") == inviter_id:
            invited.append(uid)

    text = f"👤 کاربر: {inviter_id}\n\n📌 دعوت‌شده‌ها:\n"

    if not invited:
        text += "هیچ زیرمجموعه‌ای ندارد."
    else:
        for u in invited:
            name = db["users"].get(u, {}).get("name", "unknown")
            text += f"• {name} (<code>{u}</code>)\n"

    keyboard = [
        [InlineKeyboardButton(" بازگشت",style="danger", callback_data="admin_referrals")]
    ]

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )        

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = f"{te('admin')} <b>پنل مدیریت</b>\n\nگزینه مورد نظر را انتخاب کنید:"
    last_id = context.user_data.get("last_menu_msg_id")
    if last_id and update.message:
        try: await context.bot.delete_message(update.effective_chat.id, last_id)
        except: pass
    if update.message:
        try: await update.message.delete()
        except: pass
        sent = await context.bot.send_message(update.effective_chat.id, msg, reply_markup=admin_menu_kb(), parse_mode="HTML")
        context.user_data["last_menu_msg_id"] = sent.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=admin_menu_kb(), parse_mode="HTML")
        context.user_data["last_menu_msg_id"] = update.callback_query.message.message_id
    return ConversationHandler.END

async def admin_server_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()

    remaining = len(db["settings"].get("servers", []))

    sent = 0
    for uid, user in db["users"].items():
        services = user.get("services", [])
        for s in services:
            if isinstance(s, dict):
                sent += 1

    text = f"""
📊 آمار سرورها

🟢 ارسال شده: {sent}

📦 باقی مانده در لیست: {remaining}

📊 مجموع کل:
{sent + remaining}
"""

    await query.message.edit_text(
        text,
        reply_markup=back_kb("admin")
    )    

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    uid = data[2]

    db = load_db()

    if data[1] == "reject":
        await context.bot.send_message(uid, f"{te('error')} سفارش شما رد شد.", parse_mode="HTML")
        return await query.edit_message_caption(
            caption=query.message.caption + f"\n\n{te('error')} رد شد.",
            parse_mode="HTML"
        )

    if not db["users"][uid].get("pending_order"):
        return await context.bot.send_message(
            query.from_user.id,
            f"{te('error')} سفارش یافت نشد.",
            parse_mode="HTML"
        )

    pending = db["users"][uid]["pending_order"]

    # گرفتن لیست سرورها
    servers = db["settings"].get("servers", [])

    if not servers:
        await context.bot.send_message(query.from_user.id, "هیچ سروری موجود نیست")
        return

    config = servers.pop(0)
    save_db(db)

    # سفارش جدید
    if data[3] == "new":

        db["users"][uid]["services"].append({
            "sub_id": config,
            "name": pending["plan"],
            "expiry_ts": datetime.now().timestamp() + (30 * 86400),
            "start_ts": datetime.now().timestamp(),
            "notified_5d": False
        })

        db["users"][uid]["pending_order"] = None
        save_db(db)

        await context.bot.send_message(
            uid,
            f"{te('success')} اشتراک شما فعال شد\n\n<code>{config}</code>",
            parse_mode="HTML"
        )

    # تمدید اشتراک
    elif data[3] == "renew":

        svc_idx = pending["service_idx"]

        days = next(
            (v[1] for k, v in DURATION_MAP.items() if v[0] == pending["duration_txt"]),
            30
        )

        db["users"][uid]["services"][svc_idx]["expiry_ts"] = max(
            db["users"][uid]["services"][svc_idx]["expiry_ts"],
            datetime.now().timestamp()
        ) + (days * 86400)

        db["users"][uid]["services"][svc_idx]["notified_5d"] = False
        db["users"][uid]["pending_order"] = None

        save_db(db)

        await context.bot.send_message(
            uid,
            f"{te('success')} اشتراک <code>{db['users'][uid]['services'][svc_idx].get('sub_id')}</code> تمدید شد.",
            parse_mode="HTML"
        )

        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n{te('success')} تمدید شد.",
            parse_mode="HTML"
        )
async def admin_add_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(f"{te('name')} نام پلن را وارد کنید:", reply_markup=back_kb("admin"), parse_mode="HTML")
    return ADD_NAME

async def admin_save_plan_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["np"] = update.message.text
    await update.message.reply_text(f"{te('money')} قیمت را به تومان وارد کنید:", reply_markup=back_kb("admin"), parse_mode="HTML")
    return ADD_PRICE

async def admin_save_plan_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = load_db()
        db["plans"].append({"name": context.user_data["np"], "price": int(update.message.text), "id": random.randint(1000, 9999)})
        save_db(db)
        await update.message.reply_text(f"{te('success')} پلن با موفقیت اضافه شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
        return ConversationHandler.END
    except:
        await update.message.reply_text(f"{te('error')} لطفاً قیمت را فقط به صورت عدد وارد کنید:", reply_markup=back_kb("admin"), parse_mode="HTML")
        return ADD_PRICE

async def list_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = f"{te('list')} <b>پلن‌های موجود:</b>\n\n"
    for p in load_db()["plans"]: text += f"{te('bullet')} {p['name']} | {p['price']:,} T\n"
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb("admin"))

async def del_plan_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    if not db["plans"]: return await query.message.edit_text(f"{te('error')} پلنی برای حذف وجود ندارد.", reply_markup=back_kb("admin"), parse_mode="HTML")
    btns = [[InlineKeyboardButton(p['name'], callback_data=f"delp_{p['id']}", style="danger", icon_custom_emoji_id=DYN_BTN_EMOJIS["del_item"])] for p in db["plans"]]
    btns.append([create_btn("back", "back_admin")])
    await query.message.edit_text(f"{te('trash')} روی پلن مورد نظر برای حذف کلیک کنید:", reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")

async def perform_del_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    db["plans"] = [p for p in db["plans"] if p["id"] != int(query.data.split("_")[1])]
    save_db(db)
    await query.message.edit_text(f"{te('success')} پلن با موفقیت حذف شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = f"{te('list')} <b>لیست کاربران:</b>\n\n"
    for uid, u in load_db()["users"].items():
        text += f"{te('profile')} {u.get('name', 'Unknown')} (<code>{uid}</code>)\n"
        for s in u["services"]:
            if isinstance(s, dict): text += f"   └ ID: <code>{s.get('sub_id','---')}</code> - {s['name']}\n"
        text += "\n"
    await query.message.edit_text(text[:4000], parse_mode="HTML", reply_markup=back_kb("admin"))

async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(f"{te('speaker')} لطفاً پیام همگانی خود را ارسال کنید:", reply_markup=back_kb("admin"), parse_mode="HTML")
    return BROADCAST_STATE

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = 0
    for uid in load_db()["users"]:
        try: await update.message.copy(chat_id=uid); count += 1
        except: pass
    await update.message.reply_text(f"{te('success')} پیام به {count} نفر ارسال شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    return ConversationHandler.END

async def admin_dm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(f"{te('profile')} لطفاً آیدی عددی کاربر مورد نظر را وارد کنید:", reply_markup=back_kb("admin"), parse_mode="HTML")
    return GET_DM_USER_ID

async def admin_dm_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    if update.message.text not in db["users"]: return await update.message.reply_text(f"{te('error')} کاربری یافت نشد. مجدداً وارد کنید:", reply_markup=back_kb("admin"), parse_mode="HTML") and GET_DM_USER_ID
    context.user_data["dm_target_id"] = update.message.text
    await update.message.reply_text(f"{te('success')} کاربر پیدا شد: <b>{db['users'][update.message.text].get('name')}</b>\n\n✍️ حالا پیام خود را بنویسید:", parse_mode="HTML", reply_markup=back_kb("admin"))
    return GET_DM_MESSAGE

async def admin_dm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = context.user_data.get("dm_target_id")
    try:
        await context.bot.send_message(uid, f"{te('mail')} <b>پیام جدید از طرف پشتیبانی:</b>", parse_mode="HTML")
        await update.message.copy(chat_id=uid)
        await update.message.reply_text(f"{te('success')} پیام با موفقیت ارسال شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    except Exception as e: await update.message.reply_text(f"{te('error')} خطا در ارسال پیام:\n{e}", reply_markup=admin_menu_kb(), parse_mode="HTML")
    return ConversationHandler.END

async def admin_manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channels = load_db()["settings"].get("channels", [])
    text = f"{te('admin')} <b>مدیریت کانال‌های جوین اجباری:</b>\n\n"
    if not channels: text += "هیچ کانالی ثبت نشده است."
    else:
        for i, ch in enumerate(channels): text += f"{i+1}. {ch['username']} - <a href='{ch['link']}'>لینک عضویت</a>\n"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("افزودن کانال", callback_data="add_ch", style="success", icon_custom_emoji_id=DYN_BTN_EMOJIS["add_item"]),
         InlineKeyboardButton("حذف کانال", callback_data="del_ch", style="danger", icon_custom_emoji_id=DYN_BTN_EMOJIS["del_item"])],
        [create_btn("back", "back_admin")]
    ])
    await query.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb)

async def admin_add_channel_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(f"{te('speaker')} لطفاً <b>آیدی کانال</b> را همراه با @ وارد کنید (مثال: @Ai_telegram):", reply_markup=back_kb("admin"), parse_mode="HTML")
    return ADD_CHANNEL_USER

async def admin_save_channel_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_ch_user"] = update.message.text
    await update.message.reply_text(f"{te('link')} حالا <b>لینک دعوت کانال</b> را وارد کنید:", reply_markup=back_kb("admin"), parse_mode="HTML")
    return ADD_CHANNEL_LINK

async def admin_save_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    db["settings"].setdefault("channels", []).append({"username": context.user_data["new_ch_user"], "link": update.message.text})
    save_db(db)
    await update.message.reply_text(f"{te('success')} کانال با موفقیت اضافه شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    return ConversationHandler.END

async def admin_del_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(f"{te('number')} لطفاً <b>شماره کانال</b> مورد نظر برای حذف را از لیست قبل وارد کنید (مثلاً 1):", reply_markup=back_kb("admin"), parse_mode="HTML")
    return DEL_CHANNEL_INDEX

async def admin_del_channel_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(update.message.text) - 1
        db = load_db()
        if 0 <= idx < len(db["settings"]["channels"]):
            deleted = db["settings"]["channels"].pop(idx)
            save_db(db)
            await update.message.reply_text(f"{te('success')} کانال {deleted['username']} از لیست حذف شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
        else: await update.message.reply_text(f"{te('error')} شماره اشتباه است.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    except: await update.message.reply_text(f"{te('error')} فقط عدد وارد کنید.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    return ConversationHandler.END

async def admin_add_server_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = str(update.effective_user.id) 

    db = load_db()

    db["settings"].setdefault("server_session", {})
    db["settings"]["server_session"][admin_id] = {
        "active": True,
        "servers": []
    }

    save_db(db)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اتمام ارسال", callback_data="finish_servers")],
        [create_btn("back", "back_admin")]
    ])

    await query.message.edit_text(
        "📡 حالت افزودن سرور فعال شد\n\n"
        "سرورها را یکی یکی ارسال کنید.\n"
        "وقتی تمام شد روی «اتمام ارسال» بزن.",
        reply_markup=keyboard
    )

    return SET_SERVER


async def admin_add_server_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = str(update.effective_user.id)

    db = load_db()

    db["settings"].setdefault("server_session", {})

    if admin_id not in db["settings"]["server_session"]:
        db["settings"]["server_session"][admin_id] = {
            "active": True,
            "servers": []
        }

    session = db["settings"]["server_session"][admin_id]

    server = update.message.text.strip()

    if not server:
        return SET_SERVER

    session["servers"].append(server)

    save_db(db)

    await update.message.reply_text(
        f"✅ سرور ذخیره شد\n📦 تعداد: {len(session['servers'])}"
    )

    return SET_SERVER



async def finish_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = str(query.from_user.id)   # ❗ این خط رو اضافه کن

    db = load_db()
    session = db["settings"].get("server_session", {}).get(admin_id, {})

    servers = session.get("servers", [])

    if len(servers) == 0:
        await query.message.edit_text("❌ هیچ سروری ثبت نشد.")
        return ConversationHandler.END

    db["settings"].setdefault("servers", []).extend(servers)

    # پاکسازی session
    db["settings"]["server_session"][admin_id] = {
        "active": False,
        "servers": []
    }

    save_db(db)

    await query.message.edit_text(
        f"✅ {len(servers)} سرور با موفقیت ذخیره شد.",
        reply_markup=admin_menu_kb()
    )

    return ConversationHandler.END


async def admin_set_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = str(query.from_user.id)

    db = load_db()

    db["settings"].setdefault("test_server_session", {})

    db["settings"]["test_server_session"][admin_id] = {
        "active": True,
        "servers": []
    }

    save_db(db)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ اتمام ارسال", callback_data="finish_test_servers")],
        [create_btn("back", "back_admin")]
    ])

    await query.message.edit_text(
        "🎁 حالت افزودن سرور تست فعال شد\n\n"
        "سرورها را یکی یکی ارسال کنید.\n"
        "پس از پایان روی «اتمام ارسال» بزنید.",
        reply_markup=keyboard
    )

    return TEST_SERVER_STATE

async def admin_test_server_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = str(update.effective_user.id)

    db = load_db()

    db["settings"].setdefault("test_server_session", {})

    if admin_id not in db["settings"]["test_server_session"]:
        db["settings"]["test_server_session"][admin_id] = {
            "active": True,
            "servers": []
        }

    session = db["settings"]["test_server_session"][admin_id]

    server = update.message.text.strip()

    if not server:
        return TEST_SERVER_STATE

    session["servers"].append(server)

    save_db(db)

    await update.message.reply_text(
        f"✅ سرور تست ذخیره شد\n📦 تعداد: {len(session['servers'])}"
    )

    return TEST_SERVER_STATE


async def finish_test_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = str(query.from_user.id)

    db = load_db()

    session = db["settings"].get("test_server_session", {}).get(admin_id, {})

    servers = session.get("servers", [])

    if not servers:
        await query.message.edit_text(
            "❌ هیچ سرور تستی ثبت نشد."
        )
        return ConversationHandler.END

    db["settings"].setdefault("test_servers", [])

    db["settings"]["test_servers"].extend(servers)

    db["settings"]["test_server_session"][admin_id] = {
        "active": False,
        "servers": []
    }

    save_db(db)

    await query.message.edit_text(
        f"✅ {len(servers)} سرور تست ذخیره شد.",
        reply_markup=admin_menu_kb()
    )

    return ConversationHandler.END

async def check_expirations(context: ContextTypes.DEFAULT_TYPE):
    db = load_db(); now = datetime.now().timestamp(); changed = False
    for uid, u in db["users"].items():
        for s in u["services"]:
            if isinstance(s, dict) and 4 < (s['expiry_ts'] - now) / 86400 <= 5 and not s.get("notified_5d"):
                try: await context.bot.send_message(uid, f"{te('warning')} اشتراک <code>{s.get('sub_id','')}</code> شما 5 روز دیگر تمام می‌شود.", parse_mode="HTML")
                except: pass
                s["notified_5d"] = True; changed = True
    if changed: save_db(db)

if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        load_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    if app.job_queue:
        app.job_queue.run_repeating(check_expirations, interval=14400, first=60)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_start))

    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join_btn$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(admin_start, pattern="^back_admin$"))
    app.add_handler(CallbackQueryHandler(my_services, pattern="^menu_services$"))
    app.add_handler(CallbackQueryHandler(profile_menu, pattern="^menu_profile$"))
    app.add_handler(CallbackQueryHandler(show_channels_text, pattern="^menu_news$"))
    app.add_handler(CallbackQueryHandler(test_server_handler, pattern="^menu_test$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop_"))
    app.add_handler(CallbackQueryHandler(list_users, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(list_plans, pattern="^admin_products$"))
    app.add_handler(CallbackQueryHandler(del_plan_prompt, pattern="^admin_del_plan$"))
    app.add_handler(CallbackQueryHandler(perform_del_plan, pattern="^delp_"))
    app.add_handler(CallbackQueryHandler(admin_manage_channels, pattern="^admin_channels$"))
    # app.add_handler(CallbackQueryHandler(buy_prime, pattern="^buy_prime$"))
    app.add_handler(CallbackQueryHandler(profile_info, pattern="^profile_info$"))
    app.add_handler(CallbackQueryHandler(profile_referral, pattern="^profile_referral$"))
    app.add_handler(CallbackQueryHandler(profile_orders, pattern="^profile_orders$"))
    app.add_handler(CallbackQueryHandler(profile_servers, pattern="^profile_servers$"))
    app.add_handler(CallbackQueryHandler(support_handler, pattern="^menu_support$"))
    app.add_handler(CallbackQueryHandler(admin_receipts, pattern="admin_receipts"))
    app.add_handler(CallbackQueryHandler(admin_referral_panel, pattern="^admin_referrals$"))
    app.add_handler(CallbackQueryHandler(admin_referral_user, pattern="^ref_user_"))

    # ---------------- BUY CONVERSATION ----------------
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(buy_start, pattern="^menu_buy$")],
            states={
                BUY_SELECT_PLAN: [
                    CallbackQueryHandler(buy_select_plan, pattern="^buy_VIP$")
                ],
                BUY_SELECT_VOLUME: [
                    CallbackQueryHandler(buy_select_volume, pattern="^buy_vol_")
                ],
                BUY_GET_COUNT: [
                    MessageHandler(filters.TEXT, buy_get_count)
                ],
                BUY_CONFIRM_RULES: [
                    CallbackQueryHandler(buy_confirm_rules, pattern="^accept_rules$")
                ],
                GET_RECEIPT: [
                    MessageHandler(filters.PHOTO, buy_receipt)
                ],
            },
            fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^back_")],
            allow_reentry=True
        )
    )

    # ---------------- ADMIN CONVERSATION ----------------
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(admin_callback_handler, pattern="^adm_"),
                CallbackQueryHandler(admin_add_plan, pattern="^admin_add_plan$"),
                CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$"),
                CallbackQueryHandler(admin_dm_start, pattern="^admin_dm$"),
                CallbackQueryHandler(admin_del_channel_prompt, pattern="^del_ch$"),
                CallbackQueryHandler(admin_set_test_start, pattern="^admin_set_test$"),
                CallbackQueryHandler(admin_add_server_start, pattern="^admin_add_server$"),
                CallbackQueryHandler(profile_info, pattern="profile_info"),
                CallbackQueryHandler(admin_server_stats, pattern="admin_server_stats"),
                CallbackQueryHandler(admin_receipts, pattern="admin_receipts"),
                CallbackQueryHandler(approve_receipt, pattern="^approve_receipt_"),
                CallbackQueryHandler(reject_receipt, pattern="^reject_receipt_"),
                CallbackQueryHandler(view_receipt, pattern="^view_receipt_"),
                CallbackQueryHandler(finish_test_servers, pattern="^finish_test_servers$"),
                CallbackQueryHandler(admin_add_channel_user, pattern="^add_ch$"),
                CallbackQueryHandler(show_pending_receipts,pattern="^receipts_pending$"),
                CallbackQueryHandler(show_archive_receipts,pattern="^receipts_archive$"),
            ],
            states={
                ADD_CHANNEL_USER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_channel_user)
                ],
                ADD_CHANNEL_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_channel_link)
                ],                

                TEST_SERVER_STATE: [

                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS),
                        admin_test_server_input
                    ),

                    CallbackQueryHandler(
                        finish_test_servers,
                        pattern="^finish_test_servers$"
                    ),

                ],

                SET_SERVER: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS),
                        admin_add_server_input
                    ),

                    CallbackQueryHandler(
                        finish_servers,
                        pattern="^finish_servers$"
                    ),
                ],
                TEST_SERVER_STATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS),
                        admin_test_server_input
                    ),

                    CallbackQueryHandler(
                        finish_test_servers,
                        pattern="^finish_test_servers$"
                    ),
                ],
            },
            fallbacks=[
              CallbackQueryHandler(admin_start, pattern="^back_admin$")
            ],
            allow_reentry=True
        )
    )

    print("--- Premium UI Bot Started ---")
    app.run_polling()