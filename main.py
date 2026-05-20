import logging
import json
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

BOT_TOKEN = ""
ADMIN_IDS = [1892655576]
DB_FILE = "database.json"
CARD_NUMBER = ""
SUPPORT_ID = "@puyaghsmi"

MSG_EMOJIS = {
    "welcome": {"id": "5388886459744792797", "char": "👋"},
    "error":   {"id": "4958526153955476488", "char": "❌"},
    "success": {"id": "4958725487682650920", "char": "✅"},
    "rocket":  {"id": "4958725487682650920", "char": "🚀"},
    "active":  {"id": "4956720180337050608", "char": "🟢"},
    "expired": {"id": "4956582500865410174", "char": "🔴"},
    "id_tag":  {"id": "4958686613933655185", "char": "🆔"},
    "box":     {"id": "5409380072291316349", "char": "📦"},
    "time":    {"id": "4958686613933655185", "char": "⏳"},
    "profile": {"id": "4956387556594811916", "char": "👤"},
    "book":    {"id": "4956436416142771580", "char": "📚"},
    "card":    {"id": "4956719506027185156", "char": "💳"},
    "money":   {"id": "4956269706987177066", "char": "💰"},
    "bell":    {"id": "4956368164817470478", "char": "🔔"},
    "refresh": {"id": "4956418939920843885", "char": "🔄"},
    "admin":   {"id": "5971818172985117571", "char": "🛠"},
    "name":    {"id": "5972072533833289156", "char": "📛"},
    "list":    {"id": "5974235702701853774", "char": "📋"},
    "speaker": {"id": "5972240522889138094", "char": "📢"},
    "mail":    {"id": "5852830669599674051", "char": "📬"},
    "link":    {"id": "4992622834166530981", "char": "🔗"},
    "number":  {"id": "4992684226429059932", "char": "🔢"},
    "camera":  {"id": "4992254300202730194", "char": "📷"},
    "warning": {"id": "4956611513369494230", "char": "⚠️"},
    "trash":   {"id": "4956475826762679249", "char": "🗑"},
    "diamond": {"id": "4956232383721374836", "char": "💎"},
    "bullet":  {"id": "4958489311726011319", "char": "🔹"},
    "test":    {"id": "4958725487682650920", "char": "🎁"},
}

def te(key):
    e = MSG_EMOJIS.get(key)
    if e and e["id"]:
        return f'<tg-emoji emoji-id="{e["id"]}">{e["char"]}</tg-emoji>'
    return e["char"] if e else ""

BTN_CFG = {
    "buy_new":          {"text": "خرید اشتراک جدید",    "style": "primary",  "emoji_id": "4956232383721374836"},
    "renew":            {"text": "تمدید اشتراک",        "style": "primary",  "emoji_id": "4956418939920843885"},
    "my_services":      {"text": "سرویس‌های من",       "style": "primary",  "emoji_id": "5409380072291316349"},
    "profile":          {"text": "پروفایل من",          "style": "primary",  "emoji_id": "4956387556594811916"},
    "news":             {"text": "آموزش و اخبار",       "style": "primary",  "emoji_id": "4956436416142771580"},
    "support":          {"text": "پشتیبانی",            "style": "primary",  "emoji_id": "5852830669599674051"},
    "back":             {"text": "بازگشت",              "style": "primary",  "emoji_id": "4958526153955476488"},
    "test_server":      {"text": "سرور تست رایگان",    "style": "success",  "emoji_id": "4958725487682650920"},
    "admin_add_plan":   {"text": "افزودن پلن",          "style": "primary",  "emoji_id": "4956232383721374836"},
    "admin_del_plan":   {"text": "حذف پلن",             "style": "primary",  "emoji_id": "4956475826762679249"},
    "admin_users":      {"text": "لیست کاربران",        "style": "primary",  "emoji_id": "5974235702701853774"},
    "admin_products":   {"text": "محصولات",             "style": "primary",  "emoji_id": "5409380072291316349"},
    "admin_broadcast":  {"text": "پیام همگانی",         "style": "primary",  "emoji_id": "5972240522889138094"},
    "admin_dm":         {"text": "پیام به کاربر",       "style": "primary",  "emoji_id": "5852830669599674051"},
    "admin_channels":   {"text": "مدیریت کانال‌ها",   "style": "primary",  "emoji_id": "4992622834166530981"},
    "admin_set_test":   {"text": "تنظیم سرور تست",     "style": "primary",  "emoji_id": "4958725487682650920"},
}

DYN_BTN_EMOJIS = {
    "channel_join":  "5972240522889138094",
    "check_join":    "4958725487682650920",
    "plan_item":     "4956232383721374836",
    "renew_item":    "4956418939920843885",
    "del_item":      "4956475826762679249",
    "add_item":      "4958725487682650920",
    "success_btn":   "4958725487682650920",
    "month":         "4958686613933655185",
    "copy_btn":      "4992684226429059932",
}

(
    GET_RECEIPT,
    RENEW_GET_RECEIPT,
    ADD_NAME,
    ADD_PRICE,
    BROADCAST_STATE,
    GET_SUB_ID,
    GET_QR_PHOTO,
    GET_DM_USER_ID,
    GET_DM_MESSAGE,
    MANAGE_CHANNELS,
    ADD_CHANNEL_USER,
    ADD_CHANNEL_LINK,
    DEL_CHANNEL_INDEX,
    SET_TEST_SERVER,
) = range(14)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

DURATION_MAP = {
    "1m": ("یک ماهه", 30),
    "2m": ("دو ماهه", 60),
    "3m": ("سه ماهه", 90),
    "6m": ("شش ماهه", 180),
    "12m": ("یک ساله", 365)
}

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {"settings": {"channels": [], "test_server": ""}, "users": {}, "plans": [{"name": "یک ماهه (تست)", "price": 10000, "id": 1234}]}
        save_db(default_data)
        return default_data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            db = json.load(f)
            db.setdefault("settings", {"channels": [], "test_server": ""})
            db["settings"].setdefault("test_server", "")
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
    if cfg.get("emoji_id"): kwargs["icon_custom_emoji_id"] = cfg["emoji_id"]
    if url: kwargs["url"] = url
    else: kwargs["callback_data"] = callback_data
    return InlineKeyboardButton(**kwargs)

def main_menu_kb():
    return InlineKeyboardMarkup([
        [create_btn("buy_new", "menu_buy"), create_btn("renew", "menu_renew")],
        [create_btn("my_services", "menu_services"), create_btn("profile", "menu_profile")],
        [create_btn("news", "menu_news"), create_btn("support", "menu_support")],
        [create_btn("test_server", "menu_test")],
    ])

def admin_menu_kb():
    return InlineKeyboardMarkup([
        [create_btn("admin_add_plan", "admin_add_plan"), create_btn("admin_del_plan", "admin_del_plan")],
        [create_btn("admin_users", "admin_users"), create_btn("admin_products", "admin_products")],
        [create_btn("admin_broadcast", "admin_broadcast"), create_btn("admin_dm", "admin_dm")],
        [create_btn("admin_channels", "admin_channels"), create_btn("admin_set_test", "admin_set_test")],
    ])

def back_kb(target="main"):
    return InlineKeyboardMarkup([[create_btn("back", f"back_{target}")]])

def payment_invoice_kb(card: str, amount: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 کپی شماره کارت", callback_data="noop_card", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["copy_btn"], copy_text=card),
            InlineKeyboardButton("💰 کپی مبلغ", callback_data="noop_amount", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["copy_btn"], copy_text=str(amount)),
        ],
        [create_btn("back", "back_main")],
    ])

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
            markup_keys.append([InlineKeyboardButton(f"عضویت در {ch['username']}", url=ch['link'], style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["channel_join"])])
        markup_keys.append([InlineKeyboardButton("بررسی عضویت", callback_data="check_join_btn", style="success", icon_custom_emoji_id=DYN_BTN_EMOJIS["check_join"])])
        msg = f"{te('error')} برای استفاده از ربات، لطفاً ابتدا در تمامی کانال‌های زیر عضو شوید:"
        if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(markup_keys), parse_mode="HTML")
        elif update.callback_query:
            try: await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(markup_keys), parse_mode="HTML")
            except: pass
        return False
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
        await context.bot.send_message(user_id, f"{te('welcome')} <b>به ربات خوش آمدید</b>\n\n{te('bullet')} گزینه مورد نظر را انتخاب کنید:", reply_markup=main_menu_kb(), parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"name": update.effective_user.first_name, "username": update.effective_user.username, "services": [], "pending_order": None, "has_test": False}
        save_db(db)
    if not await check_force_join(update, context): return ConversationHandler.END
    msg = f"{te('welcome')} <b>به ربات خوش آمدید</b>\n\nگزینه مورد نظر را انتخاب کنید:"
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
    test_config = db["settings"].get("test_server", "")
    if not test_config:
        await query.message.edit_text(f"{te('warning')} <b>سرور تست در حال حاضر در دسترس نیست.</b>\n\nلطفاً بعداً مراجعه کنید یا با پشتیبانی تماس بگیرید.", parse_mode="HTML", reply_markup=back_kb())
        return
    db["users"][uid]["has_test"] = True
    save_db(db)
    await query.message.edit_text(
        f"{te('test')} <b>سرور تست رایگان شما:</b>\n\n<code>{test_config}</code>\n\n{te('warning')} این سرور فقط برای تست است و دارای محدودیت می‌باشد.",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not load_db()["plans"]:
        await query.message.edit_text(f"{te('error')} فعلا هیچ محصولی موجود نیست.", reply_markup=back_kb(), parse_mode="HTML")
        return ConversationHandler.END
    btns = [
        [InlineKeyboardButton("یک ماهه", callback_data="buy_dur_1m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"]), InlineKeyboardButton("دو ماهه", callback_data="buy_dur_2m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"])],
        [InlineKeyboardButton("سه ماهه", callback_data="buy_dur_3m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"]), InlineKeyboardButton("شش ماهه", callback_data="buy_dur_6m", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["month"])],
        [create_btn("back", "back_main")]
    ]
    await query.message.edit_text(f"{te('time')} مدت زمان اشتراک را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")
    return GET_RECEIPT

async def buy_handle_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    duration_text = DURATION_MAP.get(query.data.split("_")[2], ("نامشخص", 0))[0]
    context.user_data["buy_duration"] = duration_text
    filtered = [p for p in load_db()["plans"] if duration_text in p["name"]]
    if not filtered:
        await query.message.edit_text(f"{te('error')} پلنی برای این مدت تعریف نشده است.", reply_markup=back_kb(), parse_mode="HTML")
        return ConversationHandler.END
    btns = [[InlineKeyboardButton(f"{p['name']} - {p['price']:,} T", callback_data=f"buy_plan_{p['id']}", style="primary", icon_custom_emoji_id=DYN_BTN_EMOJIS["plan_item"])] for p in filtered]
    btns.append([create_btn("back", "back_main")])
    await query.message.edit_text(f"{te('diamond')} پلن مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")

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

async def buy_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return await update.message.reply_text(f"{te('error')} لطفاً عکس رسید را ارسال کنید.", reply_markup=back_kb(), parse_mode="HTML") and GET_RECEIPT
    uid = str(update.effective_user.id)
    plan = context.user_data.get("buy_plan")
    exact_amount = context.user_data.get("exact_amount", plan["price"] if plan else 0)
    db = load_db()
    db["users"][uid]["pending_order"] = {"type": "new", "plan": plan, "duration_txt": context.user_data.get("buy_duration", ""), "date": str(datetime.now()), "exact_amount": exact_amount}
    save_db(db)
    admin_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید و تنظیم کد", callback_data=f"adm_approve_{uid}_new", style="success", icon_custom_emoji_id=DYN_BTN_EMOJIS["success_btn"])],
        [InlineKeyboardButton("رد سفارش", callback_data=f"adm_reject_{uid}", style="danger", icon_custom_emoji_id=DYN_BTN_EMOJIS["del_item"])]
    ])
    await update.message.reply_text(f"{te('success')} رسید شما دریافت شد.\n{te('time')} پس از تایید، کد اشتراک ارسال می‌شود.", reply_markup=main_menu_kb(), parse_mode="HTML")
    for admin in ADMIN_IDS:
        try: await context.bot.send_photo(admin, update.message.photo[-1].file_id, caption=f"{te('bell')} <b>سفارش جدید</b>\n{te('profile')} کاربر: <code>{uid}</code>\n{te('box')} پلن: {plan['name']}\n{te('money')} مبلغ واریزی: {exact_amount:,}", parse_mode="HTML", reply_markup=admin_markup)
        except: pass
    return ConversationHandler.END

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
        f"پس از واریز، عکس رسید را بفرستید."
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

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    uid = data[2]
    if data[1] == "reject":
        await context.bot.send_message(uid, f"{te('error')} سفارش شما رد شد.", parse_mode="HTML")
        return await query.edit_message_caption(caption=query.message.caption + f"\n\n{te('error')} رد شد.", parse_mode="HTML")
    db = load_db()
    if not db["users"][uid].get("pending_order"): return await context.bot.send_message(query.from_user.id, f"{te('error')} سفارش یافت نشد.", parse_mode="HTML")
    if data[3] == "new":
        context.user_data["target_uid"] = uid
        context.user_data["pending_info"] = db["users"][uid]["pending_order"]
        await context.bot.send_message(query.from_user.id, f"{te('number')} <b>مرحله 1 از 2</b>\nلطفاً <b>کد اشتراک</b> (مثلاً <code>1006</code>) را وارد کنید:", parse_mode="HTML", reply_markup=back_kb("admin"))
        return GET_SUB_ID
    elif data[3] == "renew":
        pending = db["users"][uid]["pending_order"]
        svc_idx = pending["service_idx"]
        days = next((v[1] for k, v in DURATION_MAP.items() if v[0] == pending["duration_txt"]), 30)
        db["users"][uid]["services"][svc_idx]["expiry_ts"] = max(db["users"][uid]["services"][svc_idx]["expiry_ts"], datetime.now().timestamp()) + (days * 86400)
        db["users"][uid]["services"][svc_idx]["notified_5d"] = False
        db["users"][uid]["pending_order"] = None
        save_db(db)
        await context.bot.send_message(uid, f"{te('success')} اشتراک <code>{db['users'][uid]['services'][svc_idx].get('sub_id')}</code> تمدید شد.", parse_mode="HTML")
        await query.edit_message_caption(caption=query.message.caption + f"\n\n{te('success')} تمدید شد.", parse_mode="HTML")

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

async def admin_set_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = load_db()["settings"].get("test_server", "تنظیم نشده")
    await query.message.edit_text(
        f"{te('test')} <b>تنظیم سرور تست</b>\n\nکانفیگ فعلی:\n<code>{current}</code>\n\nکانفیگ جدید را ارسال کنید:",
        parse_mode="HTML", reply_markup=back_kb("admin")
    )
    return SET_TEST_SERVER

async def admin_save_test_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    db["settings"]["test_server"] = update.message.text.strip()
    save_db(db)
    await update.message.reply_text(f"{te('success')} سرور تست با موفقیت ذخیره شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    return ConversationHandler.END

async def admin_get_sub_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_sub_id"] = update.message.text
    await update.message.reply_text(f"{te('success')} کد <code>{update.message.text}</code> ثبت شد.\n\n{te('camera')} <b>مرحله 2 از 2</b>\nحالا <b>عکس QR</b> را بفرستید:", parse_mode="HTML", reply_markup=back_kb("admin"))
    return GET_QR_PHOTO

async def admin_get_qr_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return await update.message.reply_text(f"{te('error')} عکس ارسال کنید.", reply_markup=back_kb("admin"), parse_mode="HTML") and GET_QR_PHOTO
    uid = context.user_data["target_uid"]
    days = next((v[1] for k, v in DURATION_MAP.items() if v[0] == context.user_data["pending_info"]["duration_txt"]), 30)
    db = load_db()
    db["users"][uid]["services"].append({
        "sub_id": context.user_data["new_sub_id"], "name": context.user_data["pending_info"]["plan"]["name"], "photo_id": update.message.photo[-1].file_id,
        "expiry_ts": datetime.now().timestamp() + (days * 86400), "start_ts": datetime.now().timestamp(), "notified_5d": False
    })
    db["users"][uid]["pending_order"] = None
    save_db(db)
    try:
        await context.bot.send_photo(uid, update.message.photo[-1].file_id, caption=f"{te('success')} سفارش فعال شد.\n{te('id_tag')} کد اشتراک: <code>{context.user_data['new_sub_id']}</code>\n{te('time')} اعتبار: {days} روز", parse_mode="HTML")
        await update.message.reply_text(f"{te('success')} ارسال شد.", reply_markup=admin_menu_kb(), parse_mode="HTML")
    except Exception as e: await update.message.reply_text(f"{te('error')} خطا: {e}", parse_mode="HTML")
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
    if not os.path.exists(DB_FILE): load_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    if app.job_queue: app.job_queue.run_repeating(check_expirations, interval=14400, first=60)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join_btn$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(admin_start, pattern="^back_admin$"))
    app.add_handler(CallbackQueryHandler(my_services, pattern="^menu_services$"))
    app.add_handler(CallbackQueryHandler(user_profile, pattern="^menu_profile$"))
    app.add_handler(CallbackQueryHandler(show_channels_text, pattern="^menu_news$"))
    app.add_handler(CallbackQueryHandler(test_server_handler, pattern="^menu_test$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer() or u.callback_query.message.edit_text(f"{te('admin')} پشتیبانی: {SUPPORT_ID}", reply_markup=back_kb(), parse_mode="HTML"), pattern="^menu_support$"))
    app.add_handler(CallbackQueryHandler(list_users, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(list_plans, pattern="^admin_products$"))
    app.add_handler(CallbackQueryHandler(del_plan_prompt, pattern="^admin_del_plan$"))
    app.add_handler(CallbackQueryHandler(perform_del_plan, pattern="^delp_"))
    app.add_handler(CallbackQueryHandler(admin_manage_channels, pattern="^admin_channels$"))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_start, pattern="^menu_buy$")],
        states={GET_RECEIPT: [CallbackQueryHandler(buy_handle_duration, pattern="^buy_dur_"), CallbackQueryHandler(buy_handle_plan, pattern="^buy_plan_"), MessageHandler(filters.PHOTO, buy_receipt)]},
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^back_")]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(renew_start, pattern="^menu_renew$")],
        states={RENEW_GET_RECEIPT: [CallbackQueryHandler(renew_select_duration, pattern="^ren_svc_"), CallbackQueryHandler(renew_process_payment, pattern="^ren_dur_"), MessageHandler(filters.PHOTO, renew_receipt)]},
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^back_")]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_callback_handler, pattern="^adm_"),
            CallbackQueryHandler(admin_add_plan, pattern="^admin_add_plan$"),
            CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$"),
            CallbackQueryHandler(admin_dm_start, pattern="^admin_dm$"),
            CallbackQueryHandler(admin_add_channel_user, pattern="^add_ch$"),
            CallbackQueryHandler(admin_del_channel_prompt, pattern="^del_ch$"),
            CallbackQueryHandler(admin_set_test_start, pattern="^admin_set_test$"),
        ],
        states={
            GET_SUB_ID: [MessageHandler(filters.TEXT, admin_get_sub_id)],
            GET_QR_PHOTO: [MessageHandler(filters.PHOTO, admin_get_qr_photo)],
            ADD_NAME: [MessageHandler(filters.TEXT, admin_save_plan_name)],
            ADD_PRICE: [MessageHandler(filters.TEXT, admin_save_plan_price)],
            BROADCAST_STATE: [MessageHandler(filters.ALL, admin_broadcast_send)],
            GET_DM_USER_ID: [MessageHandler(filters.TEXT, admin_dm_get_id)],
            GET_DM_MESSAGE: [MessageHandler(filters.ALL, admin_dm_send)],
            ADD_CHANNEL_USER: [MessageHandler(filters.TEXT, admin_save_channel_user)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT, admin_save_channel_link)],
            DEL_CHANNEL_INDEX: [MessageHandler(filters.TEXT, admin_del_channel_save)],
            SET_TEST_SERVER: [MessageHandler(filters.TEXT, admin_save_test_server)],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^back_")]
    ))

    print("--- Premium UI Bot Started ---")
    app.run_polling()
