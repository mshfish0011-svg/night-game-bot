import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# ============================================================
# ApexRival 2.0 - single-file Telegram group game bot
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
PORT = int(os.getenv("PORT", "10000") or 10000)
DATA_FILE = os.getenv("DATA_FILE", "game_data.json")

QUESTIONS = [
    "آخرین سوتی‌ای که دادی چی بود؟",
    "اگر یک روز جای یکی از اعضای گروه بودی، جای چه کسی می‌رفتی؟ چرا؟",
    "کدام عادتت را دوست داری بقیه کمتر ببینند؟",
    "خجالت‌آورترین پیام اشتباهی که فرستادی چه بود؟",
    "اگر مجبور باشی یک لقب برای خودت انتخاب کنی، چی می‌گذاری؟",
    "اگر فقط یک نفر از گروه را برای یک سفر انتخاب کنی، چه کسی؟",
    "کدام ویژگی شخصیتی در دیگران سریع توجهت را جلب می‌کند؟",
    "یک تصمیم کوچک که نتیجه بزرگی برایت داشت چه بود؟",
    "اگر قرار باشد یک قانون جدید برای این گروه بسازی، چیست؟",
    "چه چیزی می‌تواند در چند ثانیه حالت را بهتر کند؟",
    "اگر سه کلمه برای توصیف خودت بگویی، چه هستند؟",
    "کدام مهارت را دوست داری فوری یاد بگیری؟",
    "بامزه‌ترین سوءتفاهمی که برایت پیش آمده چه بوده؟",
    "اگر یک روز نامرئی شوی، اولین کار بی‌خطر و بامزه‌ای که می‌کنی چیست؟",
    "کدام انتخابت را اگر دوباره فرصت داشته باشی، متفاوت انجام می‌دهی؟",
]

DARES = [
    "با لحن گوینده اخبار، آخرین چیزی که خوردی را گزارش کن.",
    "۳۰ ثانیه فقط با ایموجی جواب بده.",
    "یک جمله کاملاً جدی درباره یک موضوع مسخره بنویس.",
    "برای خودت یک تبلیغ ۱۵ ثانیه‌ای بساز.",
    "سه تعریف واقعی و محترمانه از سه نفر گروه بنویس.",
    "یک لقب بامزه و محترمانه برای خودت انتخاب کن و تا دو پیام استفاده‌اش کن.",
    "یک داستان سه‌جمله‌ای بساز که هر سه جمله با یک کلمه شروع شوند.",
    "یک ویس ۱۰ ثانیه‌ای با لحن گوینده رادیو بفرست.",
    "بدون استفاده از کلمه «من» یک جمله درباره خودت بنویس.",
    "یک شعار خنده‌دار برای ApexRival بساز.",
]

FLIRTY = [
    "یک تعریف محترمانه و واقعی از یک نفر در گروه بنویس؛ طرف مقابل کاملاً حق رد کردن دارد.",
    "یک لقب بامزه و محترمانه برای یک نفر انتخاب کن؛ بدون کنایه یا توهین.",
    "یک جمله شروع گفت‌وگوی رمانتیکِ محترمانه بنویس، بدون خطاب اجباری به شخص خاص.",
    "یک ویژگی شخصیتی جذاب را نام ببر و بگو چرا برایت جذاب است.",
    "اگر دوست داشتی، یک تعریف کوتاه درباره انرژی یا استایل یکی از اعضا بگو.",
]

ADULT_SAFE = [
    "۱۸+: درباره یک قرار ایده‌آل، فقط در حد غیرصریح و محترمانه، یک سناریوی کوتاه بگو.",
    "۱۸+: در یک رابطه سالم، مهم‌ترین مرز شخصی از نظر تو چیست؟",
    "۱۸+: یک سؤال صمیمی اما غیرجنسی از گروه بپرس؛ هرکس می‌تواند رد کند.",
    "۱۸+: یک ویژگی جذاب شخصیتی را نام ببر و توضیح بده چرا.",
    "۱۸+: یک «اگر مجبور بودی...» درباره رابطه سالم و بدون جزئیات جنسی مطرح کن.",
]

PENALTIES = [
    "یک پیام خنده‌دار با ۳ ایموجی تصادفی بفرست.",
    "برای ۲ دقیقه با یک لقب بامزه و محترمانه صدایت کنند.",
    "یک تعریف واقعی از سه نفر گروه بنویس.",
    "یک جمله کاملاً رسمی درباره یک موضوع خنده‌دار بنویس.",
    "یک ویس ۱۰ ثانیه‌ای با صدای گوینده اخبار بفرست.",
    "یک شعار خنده‌دار برای بازیکن برنده بساز.",
    "در یک پیام، سه کلمه‌ای را که سرگروه می‌گوید استفاده کن؛ بدون توهین یا اطلاعات خصوصی.",
    "یک حرکت نمایشی بی‌خطر را در چت با سه ایموجی توضیح بده.",
]

BOSS = [
    "اولین بازیکنی که «APEX» را دقیقاً بفرستد +۵ XP می‌گیرد.",
    "یک سؤال کوتاه از گروه پرسیده می‌شود؛ سرگروه پاسخ درست را انتخاب می‌کند و برنده +۵ XP می‌گیرد.",
    "همه یک ایموجی می‌فرستند؛ سرگروه یک نفر را برای +۳ XP انتخاب می‌کند.",
    "هر بازیکن یک کلمه می‌فرستد؛ سرگروه خلاق‌ترین پاسخ را انتخاب می‌کند و +۵ XP می‌گیرد.",
]

EVENTS = [
    "بازیکن با بیشترین XP در این دست یک سپر دارد و یک بار می‌تواند از مجازات رد شود.",
    "امتیاز مرحله بعد دو برابر می‌شود.",
    "همه بازیکنان یک پیام کوتاه بفرستند؛ سرگروه یک پاسخ را +۳ XP می‌کند.",
    "یک بازیکن تصادفی مأموریت کوتاه دریافت می‌کند.",
    "سه بازیکن تصادفی هرکدام +۱ XP می‌گیرند.",
]

MAIN_BUTTONS = [
    ["🎮 بازی‌ها", "🕵️ اعتراف", "🔥 جرئت"],
    ["⚔️ دوئل", "🎰 گردونه", "🧠 سؤال گروهی"],
    ["⚡ مسابقه سرعت", "🤫 مأموریت مخفی", "🗳 رأی‌گیری"],
    ["⚖️ حکم", "👤 پروفایل من", "🏆 رتبه‌بندی"],
    ["📜 قوانین", "❓ راهنما"],
]

DEFAULT_USER = {
    "name": "کاربر", "xp": 0, "coins": 0, "wins": 0, "losses": 0,
    "streak": 0, "best_streak": 0, "games": 0, "trials": 0, "banned": False,
}


def load_data() -> dict[str, Any]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("bad data")
    except Exception:
        data = {}
    data.setdefault("users", {})
    data.setdefault("groups", {})
    data.setdefault("games", {})
    data.setdefault("settings", {"adult_default": False, "max_players": 30})
    return data


DATA = load_data()
LOCK = threading.RLock()


def save_data() -> None:
    tmp = DATA_FILE + ".tmp"
    with LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)


def user_key(uid: int) -> str:
    return str(uid)


def get_user(uid: int, name: str = "کاربر") -> dict[str, Any]:
    with LOCK:
        u = DATA["users"].setdefault(user_key(uid), DEFAULT_USER.copy())
        if name:
            u["name"] = name
        for k, v in DEFAULT_USER.items():
            u.setdefault(k, v)
        return u


def add_xp(uid: int, amount: int, name: str = "کاربر") -> None:
    u = get_user(uid, name)
    u["xp"] = max(0, int(u.get("xp", 0)) + amount)


def add_coins(uid: int, amount: int, name: str = "کاربر") -> None:
    u = get_user(uid, name)
    u["coins"] = max(0, int(u.get("coins", 0)) + amount)


def title_for(xp: int) -> str:
    if xp >= 1000: return "👑 افسانه Apex"
    if xp >= 500: return "🔥 کابوس گروه"
    if xp >= 250: return "⚔️ رقیب جدی"
    if xp >= 100: return "🎯 بازیکن حرفه‌ای"
    if xp >= 50: return "🧨 دردسرساز"
    return "🌱 تازه‌وارد"


def mention_user(user_id: int, name: str) -> str:
    safe = escape(name or "بازیکن")
    return f'<a href="tg://user?id={user_id}">{safe}</a>'


def mention_obj(user) -> str:
    return mention_user(user.id, user.first_name or "بازیکن")


def group_key(chat_id: int) -> str:
    return str(chat_id)


def get_group(chat_id: int) -> dict[str, Any]:
    with LOCK:
        g = DATA["groups"].setdefault(group_key(chat_id), {
            "adult_mode": False, "enabled": True, "active_game": None,
            "created_games": 0, "max_players": 30,
        })
        for k, v in {"adult_mode": False, "enabled": True, "active_game": None, "created_games": 0, "max_players": 30}.items():
            g.setdefault(k, v)
        return g


def is_admin(uid: int) -> bool:
    return bool(ADMIN_ID and uid == ADMIN_ID)


def is_banned(uid: int) -> bool:
    return bool(get_user(uid).get("banned", False))


def is_group(chat_id: int) -> bool:
    return bool(chat_id)


def active_game(chat_id: int) -> dict[str, Any] | None:
    gid = get_group(chat_id).get("active_game")
    return DATA["games"].get(gid) if gid else None


def reply_keyboard(uid: int) -> ReplyKeyboardMarkup:
    rows = [r[:] for r in MAIN_BUTTONS]
    if is_admin(uid):
        rows.append(["👑 پنل مدیر"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def lobby_keyboard(gid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟 ثبت‌نام", callback_data=f"join:{gid}"), InlineKeyboardButton("❌ خروج", callback_data=f"leave:{gid}")],
        [InlineKeyboardButton("👥 بازیکنان", callback_data=f"players:{gid}"), InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"refresh:{gid}")],
        [InlineKeyboardButton("▶️ شروع بازی", callback_data=f"startgame:{gid}"), InlineKeyboardButton("🛑 لغو", callback_data=f"cancelgame:{gid}")],
        [InlineKeyboardButton("⚙️ تنظیمات لابی", callback_data=f"settings:{gid}")],
    ])


def game_menu(chat_id: int) -> InlineKeyboardMarkup:
    adult = bool(get_group(chat_id).get("adult_mode"))
    rows = [
        [InlineKeyboardButton("🕵️ اعتراف", callback_data="play:truth"), InlineKeyboardButton("🔥 جرئت", callback_data="play:dare")],
        [InlineKeyboardButton("💘 فلرت", callback_data="play:flirty"), InlineKeyboardButton("🎰 گردونه", callback_data="play:roulette")],
        [InlineKeyboardButton("⚔️ دوئل", callback_data="play:duel"), InlineKeyboardButton("⚡ سرعت", callback_data="play:speed")],
        [InlineKeyboardButton("🧠 سؤال", callback_data="play:question"), InlineKeyboardButton("🤫 مأموریت مخفی", callback_data="play:secret")],
        [InlineKeyboardButton("🗳 رأی‌گیری", callback_data="play:vote"), InlineKeyboardButton("👑 Boss", callback_data="play:boss")],
        [InlineKeyboardButton("🎲 رویداد", callback_data="play:event"), InlineKeyboardButton("☠️ حکم من", callback_data="my_penalty")],
        [InlineKeyboardButton("🛑 پایان بازی", callback_data="endgame")],
    ]
    if adult:
        rows.insert(-1, [InlineKeyboardButton("🔞 +18 غیرصریح", callback_data="play:adult")])
    return InlineKeyboardMarkup(rows)


def leader_keyboard(gid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ شروع", callback_data=f"startgame:{gid}"), InlineKeyboardButton("🛑 پایان", callback_data="endgame")],
        [InlineKeyboardButton("👥 بازیکنان", callback_data=f"players:{gid}"), InlineKeyboardButton("⚙️ تنظیمات", callback_data=f"settings:{gid}")],
        [InlineKeyboardButton("🎲 مرحله تصادفی", callback_data="leader:random"), InlineKeyboardButton("☠️ مجازات تصادفی", callback_data="leader:penalty")],
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار", callback_data="admin:stats"), InlineKeyboardButton("👥 کاربران", callback_data="admin:users")],
        [InlineKeyboardButton("🎮 بازی‌های فعال", callback_data="admin:games"), InlineKeyboardButton("👥 گروه‌ها", callback_data="admin:groups")],
        [InlineKeyboardButton("📝 سؤال‌ها", callback_data="admin:questions"), InlineKeyboardButton("🔥 جرئت‌ها", callback_data="admin:dares")],
        [InlineKeyboardButton("☠️ مجازات‌ها", callback_data="admin:penalties"), InlineKeyboardButton("💘 فلرت", callback_data="admin:flirty")],
        [InlineKeyboardButton("🔞 +18", callback_data="admin:adult"), InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin:settings")],
        [InlineKeyboardButton("💾 ذخیره", callback_data="admin:save"), InlineKeyboardButton("🎲 رویداد", callback_data="admin:event")],
        [InlineKeyboardButton("👑 Boss", callback_data="admin:boss"), InlineKeyboardButton("🧹 پاکسازی", callback_data="admin:cleanup")],
    ])


def admin_content_text() -> str:
    return (
        "🛠 <b>مدیریت محتوای ApexRival</b>\n\n"
        "برای افزودن متن جدید از دستورهای زیر در چت خصوصی بات استفاده کن:\n"
        "<code>/addq متن سؤال</code>\n"
        "<code>/addd متن جرئت</code>\n"
        "<code>/addp متن مجازات</code>\n"
        "<code>/addf متن فلرت</code>\n\n"
        "حذف آخرین مورد:\n"
        "<code>/popq</code> / <code>/popd</code> / <code>/popp</code> / <code>/popf</code>"
    )


def game_players_text(g: dict[str, Any]) -> str:
    if not g.get("players"):
        return "هنوز کسی ثبت‌نام نکرده."
    lines = []
    for i, uid in enumerate(g["players"], 1):
        name = g.get("names", {}).get(str(uid), "بازیکن")
        mark = " 👑" if uid == g.get("leader_id") else ""
        lines.append(f"{i}. {escape(name)}{mark}")
    return "\n".join(lines)


def game_status_text(g: dict[str, Any]) -> str:
    status_map = {"lobby": "🟡 در انتظار شروع", "active": "🟢 در حال بازی", "finished": "🏁 تمام‌شده", "cancelled": "🛑 لغوشده"}
    return status_map.get(g.get("status"), "❔")


def new_game(chat_id: int, leader_id: int, leader_name: str) -> str:
    gid = f"{chat_id}:{int(time.time()*1000)}:{random.randint(1000,9999)}"
    DATA["games"][gid] = {
        "id": gid, "chat_id": chat_id, "leader_id": leader_id, "leader_name": leader_name,
        "status": "lobby", "players": [leader_id], "names": {str(leader_id): leader_name},
        "created": time.time(), "round": 0, "active": None, "pending_penalties": {},
        "used_shield": [], "scores": {str(leader_id): 0}, "duel": None, "vote": None,
        "speed": None, "secret": {}, "last_action": "لابی ساخته شد",
    }
    get_group(chat_id)["active_game"] = gid
    get_group(chat_id)["created_games"] = int(get_group(chat_id).get("created_games", 0)) + 1
    return gid


def touch_player(g: dict[str, Any], uid: int, name: str) -> None:
    if uid not in g["players"]:
        g["players"].append(uid)
    g["names"][str(uid)] = name or "بازیکن"
    g["scores"].setdefault(str(uid), 0)
    get_user(uid, name)


def remove_player(g: dict[str, Any], uid: int) -> None:
    if uid in g["players"]:
        g["players"].remove(uid)
    g["names"].pop(str(uid), None)
    g["scores"].pop(str(uid), None)
    g["pending_penalties"].pop(str(uid), None)


def award_win(uid: int, name: str, xp: int = 5, coins: int = 2) -> None:
    u = get_user(uid, name)
    add_xp(uid, xp, name)
    add_coins(uid, coins, name)
    u["wins"] = int(u.get("wins", 0)) + 1
    u["games"] = int(u.get("games", 0)) + 1
    u["streak"] = int(u.get("streak", 0)) + 1
    u["best_streak"] = max(int(u.get("best_streak", 0)), int(u["streak"]))


def award_loss(uid: int, name: str) -> None:
    u = get_user(uid, name)
    u["losses"] = int(u.get("losses", 0)) + 1
    u["games"] = int(u.get("games", 0)) + 1
    u["streak"] = 0


def assign_penalty(g: dict[str, Any], uid: int, name: str, text: str | None = None) -> str:
    penalty = text or random.choice(PENALTIES)
    g["pending_penalties"][str(uid)] = {"text": penalty, "assigned": time.time(), "done": False}
    return penalty


def end_game(g: dict[str, Any]) -> None:
    g["status"] = "finished"
    get_group(g["chat_id"])["active_game"] = None
    for uid in g.get("players", []):
        u = get_user(uid, g.get("names", {}).get(str(uid), "بازیکن"))
        if not u.get("games_counted_in_current", False):
            u["games"] = int(u.get("games", 0)) + 1
            u["games_counted_in_current"] = False


def normalize_html(text: str) -> str:
    return escape(text, quote=False)


async def ensure_allowed(update: Update) -> bool:
    user = update.effective_user
    uid = user.id if user else 0
    if is_banned(uid) and not is_admin(uid):
        if update.callback_query:
            await update.callback_query.answer("🚫 دسترسی شما توسط مدیر مسدود شده است.", show_alert=True)
        elif update.effective_message:
            await update.effective_message.reply_text("🚫 دسترسی شما مسدود است.")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(
        f"🎮 <b>ApexRival</b>\n\nخوش اومدی {mention_obj(update.effective_user)}!\n"
        f"⭐ XP: {u['xp']}\n💰 سکه: {u['coins']}\n🏅 عنوان: {title_for(u['xp'])}\n\n"
        "برای ساخت لابی گروهی، داخل گروه <code>/game</code> را بزن.",
        parse_mode=ParseMode.HTML, reply_markup=reply_keyboard(update.effective_user.id))


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    await update.message.reply_text("🎮 <b>منوی ApexRival</b>", parse_mode=ParseMode.HTML, reply_markup=reply_keyboard(update.effective_user.id))


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("این دستور را داخل گروه اجرا کن.")
        return
    chat_id = update.effective_chat.id
    group = get_group(chat_id)
    if not group.get("enabled", True) and not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 ApexRival در این گروه توسط مدیر غیرفعال شده است.")
        return
    existing = active_game(chat_id)
    if existing and existing.get("status") in ("lobby", "active"):
        await update.message.reply_text("⛔ یک بازی فعال است. اول همان بازی را تمام یا لغو کنید.", reply_markup=leader_keyboard(existing["id"]) if update.effective_user.id == existing["leader_id"] else None)
        return
    gid = new_game(chat_id, update.effective_user.id, update.effective_user.first_name or "سرگروه")
    await update.message.reply_text(
        "🎮 <b>ApexRival — لابی جدید</b>\n\n"
        f"👑 سرگروه: {mention_obj(update.effective_user)}\n"
        "🟡 وضعیت: در انتظار تأیید سرگروه\n\n"
        "هرکس می‌خواهد بازی کند باید خودش ثبت‌نام کند. <b>هیچ مرحله‌ای تا زدن دکمه شروع توسط سرگروه اجرا نمی‌شود.</b>\n\n"
        f"👥 بازیکنان ({len(DATA['games'][gid]['players'])}):\n{game_players_text(DATA['games'][gid])}",
        parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(gid))
    save_data()


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(
        f"👤 <b>پروفایل {escape(update.effective_user.first_name or 'بازیکن')}</b>\n\n"
        f"🏅 عنوان: {title_for(u['xp'])}\n⭐ XP: {u['xp']}\n💰 سکه: {u['coins']}\n"
        f"🎮 بازی‌ها: {u['games']}\n🏆 برد: {u['wins']}\n☠️ باخت: {u['losses']}\n"
        f"🔥 استریک: {u['streak']} | بهترین: {u['best_streak']}\n🎟 تست‌ها: {u['trials']}",
        parse_mode=ParseMode.HTML)


async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    users = []
    for uid, u in DATA["users"].items():
        users.append((int(u.get("xp", 0)), int(uid), u.get("name", "کاربر"), int(u.get("wins", 0))))
    users.sort(reverse=True)
    lines = ["🏆 <b>رتبه‌بندی ApexRival</b>"]
    for i, (xp, uid, name, wins) in enumerate(users[:10], 1):
        lines.append(f"{i}. {mention_user(uid, name)} — ⭐ {xp} | 🏆 {wins}")
    await update.message.reply_text("\n".join(lines) if len(lines) > 1 else "هنوز داده‌ای برای رتبه‌بندی نیست.", parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    await update.message.reply_text(
        "❓ <b>راهنمای ApexRival</b>\n\n"
        "1️⃣ داخل گروه <code>/game</code> را بزن.\n"
        "2️⃣ بازیکنان با «ثبت‌نام» وارد لابی می‌شوند.\n"
        "3️⃣ فقط سازنده لابی می‌تواند بازی را شروع کند.\n"
        "4️⃣ بعد از شروع، مراحل بازی فعال می‌شوند.\n"
        "5️⃣ بعضی مراحل برنده/بازنده دارند و بازنده حکم می‌گیرد.\n\n"
        "⚔️ دوئل، 🎰 گردونه، ⚡ سرعت، 🤫 مأموریت مخفی و 🗳 رأی‌گیری از حالت‌های اصلی هستند.\n"
        "🔞 +18 فقط در صورت فعال‌سازی گروه و به‌شکل غیرصریح است.\n\n"
        "هرکس می‌تواند یک چالش نامناسب را رد کند؛ توهین، تهدید، اجبار، اطلاعات خصوصی و کار خطرناک ممنوع است.",
        parse_mode=ParseMode.HTML)


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🆔 User ID: <code>{update.effective_user.id}</code>\nChat ID: <code>{update.effective_chat.id}</code>", parse_mode=ParseMode.HTML)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    await update.message.reply_text("👑 <b>Super Admin — ApexRival</b>\n\nکنترل کامل سیستم از این پنل در دسترس است.", parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def add_content(update: Update, context: ContextTypes.DEFAULT_TYPE, bucket: list[str], label: str) -> None:
    if not is_admin(update.effective_user.id): return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text(f"فرمت: /add... متن {label}")
        return
    bucket.append(text[:1000])
    save_data()
    await update.message.reply_text(f"✅ به {label} اضافه شد. تعداد: {len(bucket)}")


async def pop_content(update: Update, bucket: list[str], label: str) -> None:
    if not is_admin(update.effective_user.id): return
    if not bucket:
        await update.message.reply_text("لیست خالی است.")
        return
    item = bucket.pop()
    save_data()
    await update.message.reply_text(f"🗑 حذف شد از {label}:\n{item}")


async def toggle_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 دسترسی ندارید.")
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("این دستور را داخل گروه اجرا کن.")
        return
    g = get_group(update.effective_chat.id)
    g["enabled"] = not g.get("enabled", True)
    save_data()
    await update.message.reply_text(f"🔧 ApexRival در این گروه: {'فعال' if g['enabled'] else 'غیرفعال'}")


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not await ensure_allowed(update): return
    uid = q.from_user.id
    data = q.data or ""
    chat_id = q.message.chat_id

    # ---------------- lobby ----------------
    if data.startswith("join:"):
        gid = data.split(":", 1)[1]
        g = DATA["games"].get(gid)
        if not g or g.get("status") != "lobby":
            await q.answer("این لابی دیگر فعال نیست.", show_alert=True); return
        if uid in g["players"]:
            await q.answer("قبلاً ثبت‌نام کردی.", show_alert=True); return
        if len(g["players"]) >= int(get_group(chat_id).get("max_players", 30)):
            await q.answer("ظرفیت لابی پر شده است.", show_alert=True); return
        touch_player(g, uid, q.from_user.first_name or "بازیکن")
        save_data()
        await q.edit_message_text(
            "🎮 <b>ApexRival — لابی</b>\n\n"
            f"👑 سرگروه: {escape(g['leader_name'])}\n🟡 هنوز شروع نشده\n\n"
            f"👥 بازیکنان ({len(g['players'])}):\n{game_players_text(g)}\n\n"
            "برای شروع، سرگروه باید دکمه ▶️ را بزند.",
            parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(gid))
        return

    if data.startswith("leave:"):
        gid = data.split(":", 1)[1]
        g = DATA["games"].get(gid)
        if not g or g.get("status") != "lobby":
            await q.answer("لابی فعال نیست.", show_alert=True); return
        if uid == g["leader_id"]:
            await q.answer("سرگروه باید بازی را لغو کند.", show_alert=True); return
        remove_player(g, uid); save_data(); await q.answer("از بازی خارج شدی.")
        await q.edit_message_text(f"🎮 <b>لابی ApexRival</b>\n\n👥 بازیکنان ({len(g['players'])}):\n{game_players_text(g)}", parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(gid))
        return

    if data.startswith("players:") or data.startswith("refresh:"):
        gid = data.split(":", 1)[1]
        g = DATA["games"].get(gid)
        if not g:
            await q.answer("بازی پیدا نشد.", show_alert=True); return
        await q.answer(f"👥 {len(g['players'])} بازیکن\n\n{game_players_text(g)}"[:190], show_alert=True)
        return

    if data.startswith("startgame:"):
        gid = data.split(":", 1)[1]
        g = DATA["games"].get(gid)
        if not g: return
        if uid != g["leader_id"] and not is_admin(uid):
            await q.answer("فقط سرگروه یا Super Admin می‌تواند بازی را شروع کند.", show_alert=True); return
        if g.get("status") != "lobby":
            await q.answer("این بازی قبلاً شروع شده یا تمام شده.", show_alert=True); return
        if len(g["players"]) < 2:
            await q.answer("حداقل ۲ بازیکن لازم است.", show_alert=True); return
        g["status"] = "active"; g["round"] = 1; g["last_action"] = "بازی شروع شد"; save_data()
        await q.edit_message_text(
            "🟢 <b>ApexRival شروع شد!</b>\n\n"
            f"👑 سرگروه: {escape(g['leader_name'])}\n"
            f"👥 بازیکنان: {len(g['players'])}\n🎯 راند: {g['round']}\n\n"
            "از منوی زیر مرحله بعدی را انتخاب کنید.", parse_mode=ParseMode.HTML, reply_markup=game_menu(chat_id))
        return

    if data.startswith("cancelgame:"):
        gid = data.split(":", 1)[1]
        g = DATA["games"].get(gid)
        if not g: return
        if uid != g["leader_id"] and not is_admin(uid):
            await q.answer("فقط سرگروه یا مدیر می‌تواند لغو کند.", show_alert=True); return
        g["status"] = "cancelled"; get_group(g["chat_id"])["active_game"] = None; save_data()
        await q.edit_message_text("🛑 بازی لغو شد. هیچ امتیازی برای شروع ثبت نمی‌شود.")
        return

    if data.startswith("settings:"):
        gid = data.split(":", 1)[1]; g = DATA["games"].get(gid)
        if not g or (uid != g["leader_id"] and not is_admin(uid)):
            await q.answer("فقط سرگروه یا مدیر.", show_alert=True); return
        await q.message.reply_text(
            f"⚙️ <b>تنظیمات بازی</b>\n\n👥 بازیکنان: {len(g['players'])}\n🔞 +18 گروه: {'روشن' if get_group(chat_id).get('adult_mode') else 'خاموش'}\n🎯 راند: {g['round']}\n\n"
            "سرگروه می‌تواند از منوی بازی مراحل را انتخاب یا بازی را پایان دهد.", parse_mode=ParseMode.HTML)
        return

    # ---------------- active game ----------------
    if data == "endgame":
        g = active_game(chat_id)
        if not g:
            await q.answer("بازی فعالی نیست.", show_alert=True); return
        if uid != g["leader_id"] and not is_admin(uid):
            await q.answer("فقط سرگروه یا مدیر می‌تواند بازی را تمام کند.", show_alert=True); return
        g["status"] = "finished"; get_group(chat_id)["active_game"] = None; save_data()
        await q.edit_message_text("🏁 <b>ApexRival تمام شد!</b>\n\nامتیازات این دست در پروفایل بازیکنان باقی می‌ماند.", parse_mode=ParseMode.HTML)
        return

    if data.startswith("play:"):
        g = active_game(chat_id)
        if not g or g.get("status") != "active":
            await q.answer("⛔ اول سرگروه باید بازی را شروع کند.", show_alert=True); return
        kind = data.split(":", 1)[1]
        await play_kind(q.message, q.from_user, g, kind)
        return

    if data == "my_penalty":
        g = active_game(chat_id)
        if not g:
            await q.answer("بازی فعالی نیست.", show_alert=True); return
        p = g.get("pending_penalties", {}).get(str(uid))
        if not p or p.get("done"):
            await q.answer("حکم فعالی برای تو ثبت نشده.", show_alert=True); return
        await q.message.reply_text(f"☠️ <b>حکم تو</b>\n\n{escape(p['text'])}", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ انجام شد", callback_data="penalty_done"), InlineKeyboardButton("🛡 رد با سپر", callback_data="penalty_shield")]]))
        return

    if data == "penalty_done":
        g = active_game(chat_id)
        p = g and g.get("pending_penalties", {}).get(str(uid))
        if not p or p.get("done"):
            await q.answer("حکم فعالی نیست.", show_alert=True); return
        p["done"] = True; add_xp(uid, 3, q.from_user.first_name or "بازیکن"); add_coins(uid, 1, q.from_user.first_name or "بازیکن"); save_data()
        await q.edit_message_text("✅ انجام حکم ثبت شد! +۳ XP و +۱ سکه")
        return

    if data == "penalty_shield":
        g = active_game(chat_id)
        if not g or uid not in g.get("players", []): return
        if uid in g.get("used_shield", []):
            await q.answer("سپر این بازیکن قبلاً مصرف شده.", show_alert=True); return
        if str(uid) not in g.get("pending_penalties", {}):
            await q.answer("حکم فعالی نداری.", show_alert=True); return
        g.setdefault("used_shield", []).append(uid)
        g["pending_penalties"][str(uid)]["done"] = True
        save_data(); await q.edit_message_text("🛡 سپر مصرف شد؛ این حکم برای این مرحله حذف شد.")
        return

    if data.startswith("duel_accept:"):
        gid = data.split(":", 1)[1]; g = DATA["games"].get(gid)
        if not g or g.get("status") != "active": return
        duel = g.get("duel")
        if not duel or duel.get("status") != "pending" or duel.get("target") != uid:
            await q.answer("این دعوت دیگر معتبر نیست.", show_alert=True); return
        duel["status"] = "active"; duel["answer"] = random.choice(["A", "B", "C"]); duel["expires"] = time.time() + 45; save_data()
        await q.edit_message_text(f"⚔️ <b>دوئل شروع شد!</b>\n\nهر دو بازیکن باید یکی از گزینه‌های A/B/C را بفرستند.\n⏱ ۴۵ ثانیه فرصت دارید.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("A", callback_data=f"duelpick:A:{gid}"), InlineKeyboardButton("B", callback_data=f"duelpick:B:{gid}"), InlineKeyboardButton("C", callback_data=f"duelpick:C:{gid}")]]))
        return

    if data.startswith("duel_decline:"):
        gid = data.split(":", 1)[1]; g = DATA["games"].get(gid)
        if g and g.get("duel", {}).get("target") == uid:
            g["duel"] = None; save_data(); await q.edit_message_text("⚔️ دعوت دوئل رد شد.")
        return

    if data.startswith("duelpick:"):
        _, choice, gid = data.split(":", 2); g = DATA["games"].get(gid)
        duel = g and g.get("duel")
        if not duel or duel.get("status") != "active" or uid not in (duel.get("challenger"), duel.get("target")):
            await q.answer("دوئل فعال نیست یا تو بازیکن دوئل نیستی.", show_alert=True); return
        duel.setdefault("choices", {})[str(uid)] = choice
        if len(duel["choices"]) < 2:
            await q.answer("انتخابت ثبت شد؛ منتظر حریف باش.", show_alert=True); return
        ids = [duel["challenger"], duel["target"]]
        c1, c2 = duel["choices"].get(str(ids[0])), duel["choices"].get(str(ids[1]))
        # Rock-paper-scissors style over A/B/C; tie => random tiebreaker.
        wins = {"A": "C", "B": "A", "C": "B"}
        if c1 == c2:
            winner = random.choice(ids); loser = ids[1] if winner == ids[0] else ids[0]
        else:
            winner = ids[0] if wins[c1] == c2 else ids[1]; loser = ids[1] if winner == ids[0] else ids[0]
        wn = g["names"].get(str(winner), "برنده"); ln = g["names"].get(str(loser), "بازنده")
        award_win(winner, wn, 8, 3); award_loss(loser, ln)
        penalty = assign_penalty(g, loser, ln)
        g["duel"] = None; g["round"] += 1; save_data()
        await q.message.reply_text(f"⚔️ <b>نتیجه دوئل</b>\n\n🏆 برنده: {escape(wn)}\n☠️ بازنده: {escape(ln)}\n\n☠️ حکم بازنده:\n{escape(penalty)}\n\n🏆 +۸ XP | 💰 +۳ سکه", parse_mode=ParseMode.HTML)
        return

    if data.startswith("vote:"):
        parts = data.split(":")
        if len(parts) != 3: return
        _, target_s, gid = parts
        g = DATA["games"].get(gid); vote = g and g.get("vote")
        if not vote or vote.get("status") != "active":
            await q.answer("رأی‌گیری تمام شده.", show_alert=True); return
        target = int(target_s)
        if uid not in g["players"]:
            await q.answer("فقط بازیکنان ثبت‌نام‌شده رأی می‌دهند.", show_alert=True); return
        if str(uid) in vote["votes"]:
            await q.answer("قبلاً رأی دادی.", show_alert=True); return
        vote["votes"][str(uid)] = target
        if len(vote["votes"]) >= len(g["players"]):
            counts = {}
            for t in vote["votes"].values(): counts[str(t)] = counts.get(str(t), 0) + 1
            chosen = int(max(counts, key=counts.get)); name = g["names"].get(str(chosen), "بازیکن")
            penalty = assign_penalty(g, chosen, name)
            award_loss(chosen, name)
            g["vote"] = None; g["round"] += 1; save_data()
            await q.edit_message_text(f"🗳 <b>نتیجه رأی‌گیری</b>\n\n☠️ بیشترین رأی: {escape(name)}\n\nحکم:\n{escape(penalty)}", parse_mode=ParseMode.HTML)
        else:
            await q.answer("رأی ثبت شد.")
        return

    if data.startswith("secret_done:"):
        gid = data.split(":", 1)[1]; g = DATA["games"].get(gid)
        if not g: return
        s = g.get("secret", {}).get(str(uid))
        if not s or s.get("done"): await q.answer("مأموریت فعالی نیست.", show_alert=True); return
        s["done"] = True; add_xp(uid, 6, q.from_user.first_name or "بازیکن"); add_coins(uid, 2, q.from_user.first_name or "بازیکن"); save_data()
        await q.edit_message_text("🤫 مأموریت ثبت شد! +۶ XP و +۲ سکه")
        return

    # ---------------- admin ----------------
    if data.startswith("admin:"):
        if not is_admin(uid):
            await q.answer("🚫 دسترسی ندارید.", show_alert=True); return
        action = data.split(":", 1)[1]
        if action == "stats":
            active = sum(1 for g in DATA["games"].values() if g.get("status") in ("lobby", "active"))
            await q.message.reply_text(f"📊 کاربران: {len(DATA['users'])}\n👥 گروه‌ها: {len(DATA['groups'])}\n🎮 کل بازی‌ها: {len(DATA['games'])}\n🟢 فعال: {active}")
        elif action == "users":
            top = sorted(DATA["users"].items(), key=lambda x: int(x[1].get("xp", 0)), reverse=True)[:15]
            lines = ["👥 <b>کاربران</b>"] + [f"{i}. {escape(u.get('name','کاربر'))} — ID <code>{uid2}</code> — XP {u.get('xp',0)} — {'🚫' if u.get('banned') else '✅'}" for i, (uid2, u) in enumerate(top, 1)]
            await q.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        elif action == "games":
            active = [g for g in DATA["games"].values() if g.get("status") in ("lobby", "active")]
            if not active: await q.message.reply_text("🎮 بازی فعالی نیست.")
            else:
                await q.message.reply_text("\n\n".join([f"🎮 {escape(g['id'])}\n👑 {escape(g['leader_name'])}\n👥 {len(g['players'])}\n📌 {game_status_text(g)}" for g in active])[:4000])
        elif action == "groups":
            await q.message.reply_text("👥 <b>گروه‌ها</b>\n\n" + "\n".join(f"{gid}: {'فعال' if g.get('enabled') else 'خاموش'} | +18={'روشن' if g.get('adult_mode') else 'خاموش'}" for gid, g in list(DATA['groups'].items())[:30]), parse_mode=ParseMode.HTML)
        elif action in ("questions", "dares", "penalties", "flirty"):
            bucket = {"questions": QUESTIONS, "dares": DARES, "penalties": PENALTIES, "flirty": FLIRTY}[action]
            await q.message.reply_text(f"📚 تعداد {action}: {len(bucket)}\n\n{admin_content_text()}", parse_mode=ParseMode.HTML)
        elif action == "adult":
            await q.message.reply_text("🔞 +18 فقط به‌صورت اختیاری، برای گروه‌های واقعاً ۱۸+ و غیرصریح طراحی شده. برای تغییر گروه از دستور /adult در همان گروه استفاده کن.")
        elif action == "settings":
            await q.message.reply_text(f"⚙️ تنظیمات اصلی\n\nحداکثر بازیکن پیش‌فرض: {DATA['settings'].get('max_players',30)}\nحالت +18 پیش‌فرض: {'روشن' if DATA['settings'].get('adult_default') else 'خاموش'}\n\nدستورهای مدیریتی: /setmax عدد ، /broadcast متن")
        elif action == "save":
            save_data(); await q.message.reply_text("💾 اطلاعات ذخیره شد.")
        elif action == "event":
            await q.message.reply_text("🎲 " + random.choice(EVENTS))
        elif action == "boss":
            await q.message.reply_text("👑 " + random.choice(BOSS))
        elif action == "cleanup":
            cutoff = time.time() - 7 * 86400
            removed = 0
            for gid in list(DATA["games"]):
                g = DATA["games"][gid]
                if g.get("status") in ("finished", "cancelled") and g.get("created", 0) < cutoff:
                    DATA["games"].pop(gid, None); removed += 1
            save_data(); await q.message.reply_text(f"🧹 {removed} بازی قدیمی پاک شد.")
        return

    if data == "leader:random" or data == "leader:penalty":
        g = active_game(chat_id)
        if not g: return
        if uid != g["leader_id"] and not is_admin(uid):
            await q.answer("فقط سرگروه یا مدیر.", show_alert=True); return
        if data == "leader:random": await play_kind(q.message, q.from_user, g, random.choice(["truth", "dare", "roulette", "question", "vote", "boss", "event"]))
        else:
            target = random.choice(g["players"]); name = g["names"].get(str(target), "بازیکن"); p = assign_penalty(g, target, name); save_data(); await q.message.reply_text(f"☠️ حکم برای {escape(name)}:\n{escape(p)}", parse_mode=ParseMode.HTML)
        return


async def play_kind(message, actor, g: dict[str, Any], kind: str) -> None:
    chat_id = g["chat_id"]
    if kind == "truth":
        text = f"🕵️ <b>اعتراف</b>\n\n{escape(random.choice(QUESTIONS))}"
    elif kind == "dare":
        text = f"🔥 <b>جرئت</b>\n\n{escape(random.choice(DARES))}"
    elif kind == "flirty":
        text = f"💘 <b>فلرت محترمانه</b>\n\n{escape(random.choice(FLIRTY))}"
    elif kind == "adult":
        if not get_group(chat_id).get("adult_mode"):
            await message.reply_text("🔒 حالت +18 برای این گروه فعال نیست."); return
        text = f"🔞 <b>۱۸+ غیرصریح</b>\n\n{escape(random.choice(ADULT_SAFE))}"
    elif kind == "roulette":
        target = random.choice(g["players"]); name = g["names"].get(str(target), "بازیکن"); p = assign_penalty(g, target, name); award_loss(target, name); g["round"] += 1
        text = f"🎰 <b>گردونه چرخید!</b>\n\n🎯 انتخاب شد: {escape(name)}\n☠️ حکم:\n{escape(p)}"
    elif kind == "speed":
        answer = str(random.randint(10, 99)); g["speed"] = {"answer": answer, "expires": time.time() + 30}; text = f"⚡ <b>مسابقه سرعت!</b>\n\nاولین بازیکن ثبت‌نام‌شده که عدد <b>{answer}</b> را دقیق بفرستد، +۵ XP می‌گیرد.\n⏱ ۳۰ ثانیه"
    elif kind == "question":
        text = f"🧠 <b>سؤال گروهی</b>\n\n{escape(random.choice(QUESTIONS))}\n\nسرگروه می‌تواند پاسخ خلاقانه‌تر را انتخاب کند."
    elif kind == "secret":
        target = random.choice(g["players"]); name = g["names"].get(str(target), "بازیکن")
        mission = random.choice([
            "در سه پیام بعدی کاری کن یک بازیکن کلمه «بازی» را بگوید، بدون فاش کردن مأموریت.",
            "در دو پیام بعدی یک نفر را وادار کن یک ایموجی خاص بفرستد، بدون گفتن دلیل.",
            "یک سؤال عادی بپرس که باعث شود یکی از بازیکنان یک کلمه مشخص را بگوید.",
        ])
        g.setdefault("secret", {})[str(target)] = {"text": mission, "done": False, "created": time.time()}
        text = f"🤫 <b>مأموریت مخفی</b>\n\n🎯 مأموریت برای: {escape(name)}\n\n{escape(mission)}\n\nبعد از انجام، دکمه زیر را بزن."
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("✅ مأموریت انجام شد", callback_data=f"secret_done:{g['id']}")]])
        g["round"] += 1; g["last_action"] = "مأموریت مخفی"; save_data(); await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup); return
    elif kind == "vote":
        if len(g["players"]) < 2:
            await message.reply_text("حداقل ۲ بازیکن لازم است."); return
        g["vote"] = {"status": "active", "votes": {}, "created": time.time()}
        question = random.choice(["چه کسی احتمالاً بیشتر از همه برنده می‌شود؟", "چه کسی بیشتر از همه اهل ریسک در بازی است؟", "چه کسی احتمالاً آخرین نفر تسلیم می‌شود؟"])
        rows = []
        for uid in g["players"]:
            rows.append([InlineKeyboardButton(g["names"].get(str(uid), "بازیکن")[:30], callback_data=f"vote:{uid}:{g['id']}")])
        await message.reply_text(f"🗳 <b>رأی‌گیری</b>\n\n{question}\n\nهر بازیکن فقط یک رأی دارد.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows)); return
    elif kind == "duel":
        if len(g["players"]) < 2: await message.reply_text("حداقل ۲ بازیکن لازم است."); return
        challenger = actor.id if actor.id in g["players"] else g["leader_id"]
        targets = [x for x in g["players"] if x != challenger]
        target = random.choice(targets)
        g["duel"] = {"status": "pending", "challenger": challenger, "target": target, "choices": {}}
        text = f"⚔️ <b>دعوت به دوئل</b>\n\n{mention_user(challenger, g['names'].get(str(challenger), 'بازیکن'))} حریف را به دوئل دعوت کرده است.\n🎯 حریف: {mention_user(target, g['names'].get(str(target), 'بازیکن'))}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ قبول دوئل", callback_data=f"duel_accept:{g['id']}"), InlineKeyboardButton("❌ رد", callback_data=f"duel_decline:{g['id']}")]])
        g["last_action"] = "دعوت دوئل"; save_data(); await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup); return
    elif kind == "boss":
        text = "👑 <b>Boss Round</b>\n\n" + escape(random.choice(BOSS))
    elif kind == "event":
        text = "🎲 <b>رویداد تصادفی</b>\n\n" + escape(random.choice(EVENTS))
    else:
        return
    g["round"] = int(g.get("round", 0)) + 1
    g["last_action"] = kind
    save_data()
    await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=game_menu(chat_id))


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    text = (update.message.text or "").strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    g = active_game(chat_id) if update.effective_chat.type in ("group", "supergroup") else None

    if text == "👑 پنل مدیر":
        await admin_command(update, context); return
    if text == "🎮 بازی‌ها":
        if not g or g.get("status") != "active":
            await update.message.reply_text("⛔ هنوز بازی فعال نشده. اگر لابی وجود دارد، فقط سرگروه می‌تواند آن را شروع کند.")
        else:
            await update.message.reply_text("🎮 <b>مراحل بازی</b>", parse_mode=ParseMode.HTML, reply_markup=game_menu(chat_id))
        return
    mapping = {"🕵️ اعتراف": "truth", "🔥 جرئت": "dare", "⚔️ دوئل": "duel", "🎰 گردونه": "roulette", "🧠 سؤال گروهی": "question", "⚡ مسابقه سرعت": "speed", "🤫 مأموریت مخفی": "secret", "🗳 رأی‌گیری": "vote"}
    if text in mapping:
        if not g or g.get("status") != "active":
            await update.message.reply_text("⛔ هنوز بازی شروع نشده. سرگروه باید لابی را تأیید و شروع کند.")
        elif text == "⚔️ دوئل" and uid != g["leader_id"] and uid not in g["players"]:
            await update.message.reply_text("فقط بازیکنان ثبت‌نام‌شده می‌توانند دوئل کنند.")
        else:
            await play_kind(update.message, update.effective_user, g, mapping[text])
        return
    if text == "⚖️ حکم":
        if not g or g.get("status") != "active":
            await update.message.reply_text("اول بازی را شروع کنید."); return
        p = g.get("pending_penalties", {}).get(str(uid))
        if not p or p.get("done"):
            await update.message.reply_text("☠️ حکم فعالی برای تو ثبت نشده."); return
        await update.message.reply_text(f"☠️ <b>حکم تو</b>\n\n{escape(p['text'])}", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ انجام شد", callback_data="penalty_done"), InlineKeyboardButton("🛡 سپر", callback_data="penalty_shield")]])); return
    if text == "👤 پروفایل من": await profile(update, context); return
    if text == "🏆 رتبه‌بندی": await rank(update, context); return
    if text == "📜 قوانین":
        await update.message.reply_text("📜 <b>قوانین</b>\n\nرضایت مهم است. هرکس می‌تواند چالش نامناسب را رد کند. اجبار، تهدید، آزار، توهین شدید، اطلاعات خصوصی و کار خطرناک ممنوع است. +18 فقط اختیاری و غیرصریح است.", parse_mode=ParseMode.HTML); return
    if text == "❓ راهنما": await help_cmd(update, context); return

    # Speed game: only registered players can win.
    if g and g.get("status") == "active" and g.get("speed"):
        speed = g["speed"]
        if time.time() <= speed.get("expires", 0) and text == str(speed.get("answer")) and uid in g["players"]:
            add_xp(uid, 5, update.effective_user.first_name or "بازیکن"); add_coins(uid, 2, update.effective_user.first_name or "بازیکن"); g["speed"] = None; g["round"] += 1; save_data()
            await update.message.reply_text(f"🏁 {mention_obj(update.effective_user)} سریع‌تر از همه بود! +۵ XP و +۲ سکه", parse_mode=ParseMode.HTML)
            return
        if time.time() > speed.get("expires", 0):
            g["speed"] = None; save_data()


async def adult_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("این دستور را داخل گروه اجرا کن."); return
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("فقط Super Admin می‌تواند حالت +18 را تغییر دهد."); return
    g = get_group(update.effective_chat.id); g["adult_mode"] = not g.get("adult_mode", False); save_data()
    await update.message.reply_text(f"🔞 حالت +18 غیرصریح: {'فعال شد' if g['adult_mode'] else 'خاموش شد'}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id): return
    text = " ".join(context.args).strip()
    if not text: await update.message.reply_text("فرمت: /broadcast متن"); return
    sent = 0; failed = 0
    for uid in list(DATA["users"]):
        try:
            await context.bot.send_message(int(uid), f"📢 <b>ApexRival</b>\n\n{escape(text)}", parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"📢 ارسال تمام شد. موفق: {sent} | ناموفق: {failed}")


async def setmax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id): return
    try: value = max(2, min(100, int(context.args[0])))
    except Exception:
        await update.message.reply_text("فرمت: /setmax 30"); return
    DATA["settings"]["max_players"] = value
    save_data(); await update.message.reply_text(f"⚙️ حداکثر بازیکن پیش‌فرض: {value}")


async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text(f"فرمت: /{action} USER_ID"); return
    try: target = int(context.args[0])
    except Exception:
        await update.message.reply_text("User ID باید عدد باشد."); return
    u = get_user(target)
    if action == "ban": u["banned"] = True
    elif action == "unban": u["banned"] = False
    elif action == "reset": DATA["users"][str(target)] = DEFAULT_USER.copy()
    elif action in ("addxp", "addcoins"):
        if len(context.args) < 2: await update.message.reply_text(f"فرمت: /{action} USER_ID AMOUNT"); return
        amount = int(context.args[1]); key = "xp" if action == "addxp" else "coins"; u[key] = max(0, int(u.get(key, 0)) + amount)
    save_data(); await update.message.reply_text(f"✅ {action} روی {target} انجام شد.")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ApexRival OK")
    def log_message(self, format, *args):
        return


def start_health_server() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        ("start", "شروع"), ("game", "ساخت لابی بازی"), ("menu", "منوی بازی"),
        ("profile", "پروفایل"), ("rank", "رتبه‌بندی"), ("help", "راهنما"), ("id", "آیدی"),
        ("admin", "پنل مدیر"), ("adult", "تغییر +18 توسط مدیر"),
    ])


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")
    start_health_server()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game_command))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("adult", adult_command))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("setmax", setmax))
    app.add_handler(CommandHandler("ban", lambda u, c: user_action(u, c, "ban")))
    app.add_handler(CommandHandler("unban", lambda u, c: user_action(u, c, "unban")))
    app.add_handler(CommandHandler("reset", lambda u, c: user_action(u, c, "reset")))
    app.add_handler(CommandHandler("addxp", lambda u, c: user_action(u, c, "addxp")))
    app.add_handler(CommandHandler("addcoins", lambda u, c: user_action(u, c, "addcoins")))
    app.add_handler(CommandHandler("addq", lambda u, c: add_content(u, c, QUESTIONS, "سؤال")))
    app.add_handler(CommandHandler("addd", lambda u, c: add_content(u, c, DARES, "جرئت")))
    app.add_handler(CommandHandler("addp", lambda u, c: add_content(u, c, PENALTIES, "مجازات")))
    app.add_handler(CommandHandler("addf", lambda u, c: add_content(u, c, FLIRTY, "فلرت")))
    app.add_handler(CommandHandler("popq", lambda u, c: pop_content(u, QUESTIONS, "سؤال")))
    app.add_handler(CommandHandler("popd", lambda u, c: pop_content(u, DARES, "جرئت")))
    app.add_handler(CommandHandler("popp", lambda u, c: pop_content(u, PENALTIES, "مجازات")))
    app.add_handler(CommandHandler("popf", lambda u, c: pop_content(u, FLIRTY, "فلرت")))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("ApexRival 2.0 starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
