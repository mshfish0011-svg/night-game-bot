import asyncio
import json
import logging
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else None
PORT = int(os.getenv("PORT", "10000"))
DATA_FILE = Path(os.getenv("DATA_FILE", "game_data.json"))

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("night_game")

# ------------------------------------------------------------
# Content banks (safe, playful, consent-based)
# ------------------------------------------------------------
QUESTIONS = [
    "آخرین باری که وانمود کردی چیزی برات مهم نیست ولی در واقع خیلی مهم بود، چی بود؟",
    "اگر مجبور باشی یک نفر از این جمع را برای یک سفر انتخاب کنی، چه کسی را انتخاب می‌کنی و چرا؟",
    "خجالت‌آورترین سوتی‌ای که هنوز یادت مانده چیست؟",
    "تا حالا شده عمداً جواب یک پیام را دیر بدهی تا طرف فکر کند سرت شلوغ بوده؟ چرا؟",
    "یک ویژگی در خودت بگو که معمولاً بقیه دیر متوجهش می‌شوند.",
    "اگر قرار باشد امشب یک نفر رازدار تو باشد، چه کسی را انتخاب می‌کنی؟",
    "چه چیزی خیلی سریع می‌تواند تو را از یک نفر دلزده کند؟",
    "آخرین باری که به کسی حسودی کردی، سر چه چیزی بود؟",
    "اگر می‌توانستی یک تصمیم قدیمی‌ات را عوض کنی، کدام را عوض می‌کردی؟",
    "یک اعتراف کوچک که گفتنش برایت سخت نیست، چیست؟",
    "کدام عضو گروه از چیزی که فکر می‌کردی باهوش‌تر است؟",
    "اگر یک هفته مجبور باشی با یک نفر هم‌تیمی باشی، چه کسی را انتخاب می‌کنی؟",
]

DARES = [
    "در گروه یک پیام خیلی رسمی بنویس، انگار داری برای رئیس‌جمهور نامه می‌نویسی! 😂",
    "سه پیام بعدی‌ات باید با یک ایموجی تصادفی تمام شوند.",
    "یک جمله تعریف واقعی و محترمانه درباره یکی از بازیکنان بنویس.",
    "در یک پیام خودت را با یک لقب مسخره معرفی کن و تا دو دقیقه همان لقب را نگه دار.",
    "یک جمله بساز که در آن هم «پیتزا» باشد هم «فضانورد». 🍕🚀",
    "در 20 ثانیه یک داستان سه‌خطی درباره بدترین روز زندگی‌ات بساز؛ لازم نیست واقعی باشد.",
    "یک پیام بفرست که هر کلمه‌اش با حرف یکسان شروع شود.",
    "به انتخاب ربات، یکی از ایموجی‌های 😂 😎 😭 را در دو پیام آینده استفاده کن.",
]

FLIRTY = [
    "اگر مجبور باشی یک نفر از بازیکنان را برای یک قرار قهوه‌ای دوستانه انتخاب کنی، چه کسی را انتخاب می‌کنی؟",
    "کدام ویژگی شخصیتی در یک نفر برایت از همه جذاب‌تر است؟",
    "بین بازیکنان، با چه کسی احتمالاً بیشتر از همه می‌خندی؟",
    "یک تعریف کوتاه و محترمانه از کسی که انتخاب می‌کنی بنویس.",
    "اگر بخواهی با یکی از بازیکنان یک تیم دونفره بسازی، چه کسی را انتخاب می‌کنی؟",
    "چه چیزی در یک نفر باعث می‌شود سریع‌تر به او علاقه‌مند شوی؟",
]

ADULT_SAFE = [
    "🔞 سؤال جسورانه: تا حالا از کسی خوشت آمده و وانمود کرده‌ای اصلاً برایت مهم نیست؟ فقط بگو آره یا نه و اگر خواستی دلیل کوتاه.",
    "🔞 بین بازیکنان، چه کسی از نظر شخصیت برایت جذاب‌تر است؟ پاسخ محترمانه و اختیاری است.",
    "🔞 بزرگ‌ترین «ردفلگ»ی که در یک آشنایی برایت غیرقابل‌قبول است چیست؟",
    "🔞 چه نوع توجهی از طرف کسی بیشتر از همه روی تو اثر می‌گذارد؟",
    "🔞 اگر بخواهی یک قرار ایده‌آل طراحی کنی، فضای آن چطور است؟",
]

PENALTIES = [
    ("😂 بازیگر رسمی", "تا سه پیام بعدی با لحن خیلی رسمی حرف بزن."),
    ("🎭 لقب اجباری", "یک لقب خنده‌دار انتخاب کن و تا 5 دقیقه با همان لقب معرفی شو."),
    ("🧠 اعتراف کوتاه", "یک اعتراف کوچک و بی‌خطر درباره خودت بگو."),
    ("💬 جمله ممنوعه", "ربات یک کلمه به تو می‌دهد؛ تا 3 دقیقه آن را استفاده نکن."),
    ("⚡ سرعتی", "در 20 ثانیه یک سؤال رندوم را جواب بده؛ اگر جواب ندهی 30 XP کم می‌شود."),
    ("😈 فلرت محترمانه", "یک تعریف واقعی و غیرجنسی از یکی از بازیکنان بنویس؛ فقط در صورت تمایل هر دو طرف."),
    ("🔄 شانس دوباره", "یک چالش کوچک انجام بده و 25 XP از جریمه‌ات کم کن."),
]

BOSS_CHALLENGES = [
    "در 25 ثانیه سه جواب متفاوت برای «اگر فردا مشهور شوم...» بنویس.",
    "اولین نفر که جواب درست بدهد: 100 XP. سؤال: چه چیزی هرچه بیشتر از آن برداری، بزرگ‌تر می‌شود؟",
    "در یک پیام، یک داستان خنده‌دار 30 کلمه‌ای بنویس.",
]

RANDOM_EVENTS = [
    ("⚡ شکار سریع", "اولین نفر که «🔥» بفرستد، 40 XP می‌گیرد."),
    ("🎯 عدد مخفی", "اولین نفر که عدد 27 را بفرستد، 60 XP می‌گیرد."),
    ("😂 کلمه ممنوعه", "در دو دقیقه هرکس «اوکی» بگوید 15 XP از دست می‌دهد."),
    ("🎁 جایزه ناگهانی", "اولین نفر که یک ایموجی انتخابی خودش بفرستد، 50 XP می‌گیرد."),
]

# ------------------------------------------------------------
# State
# ------------------------------------------------------------
DEFAULT_PLAYER = {
    "xp": 0,
    "coins": 100,
    "wins": 0,
    "losses": 0,
    "streak": 0,
    "best_streak": 0,
    "challenges": 0,
    "completed_penalties": 0,
    "title": "بازیکن تازه‌وارد",
    "adult_ok": False,
}


def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {"players": {}, "groups": {}, "pending_duels": {}, "active_games": {}, "version": 1}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        log.exception("Could not load data; starting fresh")
        return {"players": {}, "groups": {}, "pending_duels": {}, "active_games": {}, "version": 1}


def save_data() -> None:
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(DB, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_FILE)


DB = load_data()
SAVE_LOCK = threading.Lock()


def save() -> None:
    with SAVE_LOCK:
        save_data()


def player_key(user_id: int) -> str:
    return str(user_id)


def ensure_player(user_id: int, name: str = "بازیکن") -> dict[str, Any]:
    key = player_key(user_id)
    if key not in DB["players"]:
        DB["players"][key] = {**DEFAULT_PLAYER, "name": name}
    else:
        DB["players"][key].setdefault("name", name)
        for k, v in DEFAULT_PLAYER.items():
            DB["players"][key].setdefault(k, v)
    return DB["players"][key]


def level_for_xp(xp: int) -> int:
    return max(1, xp // 250 + 1)


def title_for(player: dict[str, Any]) -> str:
    xp = player["xp"]
    streak = player["streak"]
    wins = player["wins"]
    losses = player["losses"]
    if streak >= 7:
        return "🔥 کابوس گروه"
    if wins >= 20:
        return "👑 رئیس بازی"
    if losses >= 15 and losses > wins * 2:
        return "💀 قربانی همیشگی"
    if player["completed_penalties"] >= 15:
        return "😈 حکم‌باز"
    if xp >= 2000:
        return "⚡ افسانه"
    if xp >= 1000:
        return "🎯 چالش‌طلب"
    if wins >= 10:
        return "🧠 شکارچی برد"
    return "🎮 بازیکن تازه‌وارد"


def add_xp(user_id: int, amount: int) -> None:
    p = ensure_player(user_id)
    p["xp"] = max(0, p["xp"] + amount)
    p["title"] = title_for(p)


def register_win(user_id: int, xp: int = 100) -> None:
    p = ensure_player(user_id)
    p["wins"] += 1
    p["streak"] += 1
    p["best_streak"] = max(p["best_streak"], p["streak"])
    p["coins"] += 30
    add_xp(user_id, xp + min(p["streak"] * 10, 50))


def register_loss(user_id: int, xp_loss: int = 30) -> None:
    p = ensure_player(user_id)
    p["losses"] += 1
    p["streak"] = 0
    p["coins"] += 5
    add_xp(user_id, -xp_loss)


def mention(user) -> str:
    safe_name = (user.first_name or user.username or "بازیکن").replace("<", "").replace(">", "")
    return f"<a href=\"tg://user?id={user.id}\">{safe_name}</a>"


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        ["🎮 بازی‌ها", "🕵️ اعتراف"],
        ["🔥 جرئت", "⚔️ دوئل"],
        ["🎰 گردونه", "🧠 سؤال گروهی"],
        ["⚡ مسابقه سرعت", "⚖️ حکم"],
        ["👤 پروفایل من", "🏆 رتبه‌بندی"],
        ["📜 قوانین", "❓ راهنما"],
    ]
    if is_admin:
        rows.append(["👑 پنل مدیر"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def game_keyboard(adult_enabled: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🕵️ اعتراف", callback_data="game:truth"), InlineKeyboardButton("🔥 جرئت", callback_data="game:dare")],
        [InlineKeyboardButton("💘 فلرت", callback_data="game:flirty"), InlineKeyboardButton("🎰 گردونه", callback_data="game:roulette")],
        [InlineKeyboardButton("⚡ سرعت", callback_data="game:speed"), InlineKeyboardButton("🧠 سؤال", callback_data="game:question")],
        [InlineKeyboardButton("🎲 رویداد تصادفی", callback_data="game:event"), InlineKeyboardButton("👑 باس", callback_data="game:boss")],
    ]
    if adult_enabled:
        buttons.append([InlineKeyboardButton("🔞 جسورانه +۱۸", callback_data="game:adult")])
    return InlineKeyboardMarkup(buttons)


def ranking_text() -> str:
    players = []
    for uid, p in DB["players"].items():
        players.append((p.get("xp", 0), p.get("wins", 0), p.get("name", "بازیکن"), uid))
    players.sort(reverse=True)
    if not players:
        return "🏆 هنوز کسی بازی نکرده."
    lines = ["🏆 <b>رتبه‌بندی بزرگ</b>", ""]
    medals = ["🥇", "🥈", "🥉"]
    for i, (xp, wins, name, uid) in enumerate(players[:10], 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {name} — <b>{xp} XP</b> | {wins} برد")
    return "\n".join(lines)


def group_state(chat_id: int) -> dict[str, Any]:
    key = str(chat_id)
    if key not in DB["groups"]:
        DB["groups"][key] = {
            "adult_mode": False,
            "enabled": True,
            "round": 0,
            "last_event": 0,
        }
    return DB["groups"][key]


def is_admin(user_id: int) -> bool:
    return ADMIN_ID is not None and user_id == ADMIN_ID


# ------------------------------------------------------------
# HTTP health server for Render
# ------------------------------------------------------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            payload = b'{"ok":true,"service":"night-game-bot"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt, *args):
        return


def start_health_server():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("Health server listening on 0.0.0.0:%s", PORT)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
async def ensure_user(update: Update) -> dict[str, Any]:
    user = update.effective_user
    p = ensure_player(user.id, user.first_name or user.username or "بازیکن")
    p["title"] = title_for(p)
    save()
    return p


async def safe_answer(query, text: str | None = None):
    try:
        await query.answer(text=text or "")
    except Exception:
        pass


async def send_game(chat_id: int, kind: str, bot, actor_id: int | None = None):
    gs = group_state(chat_id)
    gs["round"] += 1

    if kind == "truth":
        text = f"🕵️ <b>اعتراف — دور {gs['round']}</b>\n\n{random.choice(QUESTIONS)}\n\n⏱ اختیاری؛ می‌توانی «پاس» کنی."
    elif kind == "dare":
        text = f"🔥 <b>جرئت — دور {gs['round']}</b>\n\n{random.choice(DARES)}\n\n😈 اگر انجامش دادی، بنویس «انجام شد»."
    elif kind == "flirty":
        text = f"💘 <b>چالش جذاب — دور {gs['round']}</b>\n\n{random.choice(FLIRTY)}\n\n⚠️ محترمانه و اختیاری؛ مزاحمت برای کسی جزو بازی نیست."
    elif kind == "adult":
        if not gs.get("adult_mode"):
            return await bot.send_message(chat_id, "🔒 حالت جسورانه +۱۸ در این گروه فعال نیست. مدیر گروه می‌تواند آن را فعال کند.")
        text = f"🔞 <b>حالت جسورانه +۱۸ — دور {gs['round']}</b>\n\n{random.choice(ADULT_SAFE)}\n\n✅ پاسخ‌دادن اختیاری است و هرکس می‌تواند رد کند."
    elif kind == "roulette":
        text = (
            f"🎰 <b>گردونه شانس</b>\n\n"
            f"گردونه چرخید...\n\n"
            f"🎯 بخش امروز: <b>{random.choice(['اعتراف', 'جرئت', 'فلرت محترمانه', 'سرعت', 'حکم'])}</b>\n\n"
            f"برای انتخاب برنده، همه روی دکمه «ورود» بزنند."
        )
    elif kind == "speed":
        target = random.choice(["🔥", "😂", "🎯", "27", "بازی شروع شد"])
        DB["active_games"][str(chat_id)] = {"type": "speed", "target": target, "started": time.time()}
        text = f"⚡ <b>مسابقه سرعت!</b>\n\nاولین نفری که دقیقاً این را بفرستد برنده است:\n\n<b>{target}</b>\n\n🏁 GO!"
    elif kind == "question":
        text = f"🧠 <b>سؤال گروهی</b>\n\n{random.choice(QUESTIONS)}\n\n💬 بهترین پاسخ را گروه انتخاب می‌کند."
    elif kind == "event":
        title, event = random.choice(RANDOM_EVENTS)
        text = f"🚨 <b>{title}</b>\n\n{event}\n\n⏱ از همین الان شروع شد!"
    elif kind == "boss":
        challenge = random.choice(BOSS_CHALLENGES)
        text = f"👑 <b>BOSS ROUND</b>\n\n{challenge}\n\n🏆 پاداش ویژه: +100 XP"
    else:
        text = "بازی پیدا نشد."

    await bot.send_message(chat_id, text, parse_mode="HTML")
    save()


# ------------------------------------------------------------
# Commands
# ------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await ensure_user(update)
    admin = is_admin(update.effective_user.id)
    text = (
        "🎭 <b>به شب‌گرد خوش اومدی!</b>\n\n"
        "اینجا هر دور می‌تواند به یک اعتراف، جرئت، دوئل، گردونه، حکم یا اتفاق کاملاً تصادفی تبدیل شود. 😈\n\n"
        f"🎮 سطح تو: <b>{level_for_xp(p['xp'])}</b>\n"
        f"⭐ XP: <b>{p['xp']}</b>\n"
        f"🪙 سکه: <b>{p['coins']}</b>\n\n"
        "از دکمه‌های فارسی پایین استفاده کن."
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_keyboard(admin))


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_user(update)
    await update.message.reply_text("🎮 منوی بازی آماده است.", reply_markup=main_keyboard(is_admin(update.effective_user.id)))


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 شناسه تلگرام شما:\n\n<code>{update.effective_user.id}</code>", parse_mode="HTML")


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await ensure_user(update)
    await update.message.reply_text(
        "👤 <b>پروفایل من</b>\n\n"
        f"🏷 عنوان: {p['title']}\n"
        f"⭐ XP: <b>{p['xp']}</b>\n"
        f"🎚 سطح: <b>{level_for_xp(p['xp'])}</b>\n"
        f"🪙 سکه: <b>{p['coins']}</b>\n"
        f"🏆 برد: <b>{p['wins']}</b>\n"
        f"💀 باخت: <b>{p['losses']}</b>\n"
        f"🔥 بهترین استریک: <b>{p['best_streak']}</b>\n"
        f"⚖️ حکم‌های موفق: <b>{p['completed_penalties']}</b>",
        parse_mode="HTML",
    )


async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_user(update)
    await update.message.reply_text(ranking_text(), parse_mode="HTML")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ <b>راهنما</b>\n\n"
        "🎮 بازی‌ها: انتخاب یک بازی\n"
        "🕵️ اعتراف: سؤال‌های شخصی و بامزه\n"
        "🔥 جرئت: مأموریت‌های کوتاه و خنده‌دار\n"
        "⚔️ دوئل: رقابت دو نفره (در نسخه بعدی گسترده‌تر می‌شود)\n"
        "🎰 گردونه: انتخاب تصادفی نوع بازی\n"
        "⚖️ حکم: مشاهده/اجرای حکم فعال\n\n"
        "برای تجربه کامل در گروه، ربات باید در گروه دسترسی مناسب داشته باشد.",
        parse_mode="HTML",
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 <b>قوانین شب‌گرد</b>\n\n"
        "1) هیچ‌کس مجبور به پاسخ شخصی نیست و می‌تواند پاس کند.\n"
        "2) چالش‌ها نباید شامل خطر، آزار، تهدید یا انتشار اطلاعات خصوصی باشند.\n"
        "3) حالت جسورانه +۱۸ فقط برای جمع‌های واقعاً ۱۸+ و با رضایت اعضاست.\n"
        "4) فلرت فقط محترمانه و اختیاری است.\n"
        "5) مدیر می‌تواند بازی را متوقف یا یک بازیکن را از بازی خارج کند.",
        parse_mode="HTML",
    )


async def game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_user(update)
    gs = group_state(update.effective_chat.id)
    await update.message.reply_text(
        "🎮 <b>منوی بازی</b>\n\nیک حالت را انتخاب کن:",
        parse_mode="HTML",
        reply_markup=game_keyboard(gs.get("adult_mode", False)),
    )


async def direct_truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_user(update)
    await send_game(update.effective_chat.id, "truth", context.bot, update.effective_user.id)


async def direct_dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_user(update)
    await send_game(update.effective_chat.id, "dare", context.bot, update.effective_user.id)


async def direct_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_user(update)
    await send_game(update.effective_chat.id, "roulette", context.bot, update.effective_user.id)


async def punishment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await ensure_user(update)
    title, text = random.choice(PENALTIES)
    p["challenges"] += 1
    save()
    await update.message.reply_text(
        f"⚖️ <b>حکم امروزت</b>\n\n<b>{title}</b>\n{text}\n\n✅ بعد از انجامش بنویس: «انجام شد»",
        parse_mode="HTML",
    )


# ------------------------------------------------------------
# Admin
# ------------------------------------------------------------
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ این بخش فقط برای مدیر ربات است.")
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔞 روشن/خاموش +۱۸", callback_data="admin:adult")],
        [InlineKeyboardButton("🚨 رویداد تصادفی", callback_data="admin:event")],
        [InlineKeyboardButton("👑 باس راند", callback_data="admin:boss")],
        [InlineKeyboardButton("💾 ذخیره داده", callback_data="admin:save")],
        [InlineKeyboardButton("📊 آمار", callback_data="admin:stats")],
    ])
    await update.message.reply_text("👑 <b>پنل مدیر</b>", parse_mode="HTML", reply_markup=keyboard)


async def admin_callback(query, chat_id: int, bot):
    action = query.data.split(":", 1)[1]
    if not is_admin(query.from_user.id):
        await safe_answer(query, "⛔ دسترسی نداری")
        return
    if action == "adult":
        if chat_id not in [None, 0]:
            gs = group_state(chat_id)
            gs["adult_mode"] = not gs.get("adult_mode", False)
            save()
            status = "روشن ✅" if gs["adult_mode"] else "خاموش 🔒"
            await query.edit_message_text(f"🔞 حالت جسورانه +۱۸: <b>{status}</b>", parse_mode="HTML")
        else:
            await query.edit_message_text("این گزینه را باید داخل همان گروهی اجرا کنی که می‌خواهی تنظیم شود.")
    elif action == "event":
        await send_game(chat_id, "event", bot)
        await query.edit_message_text("🚨 رویداد در گروه ارسال شد.")
    elif action == "boss":
        await send_game(chat_id, "boss", bot)
        await query.edit_message_text("👑 باس راند در گروه ارسال شد.")
    elif action == "save":
        save()
        await query.edit_message_text("💾 اطلاعات ذخیره شد.")
    elif action == "stats":
        await query.edit_message_text(
            f"📊 بازیکنان ثبت‌شده: <b>{len(DB['players'])}</b>\n"
            f"🎮 گروه‌های ثبت‌شده: <b>{len(DB['groups'])}</b>",
            parse_mode="HTML",
        )


# ------------------------------------------------------------
# Callback + text routing
# ------------------------------------------------------------
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    data = query.data or ""
    chat_id = update.effective_chat.id if update.effective_chat else None

    if data.startswith("game:"):
        kind = data.split(":", 1)[1]
        if kind == "roulette":
            # The roulette chooses a type, then runs it.
            kind = random.choice(["truth", "dare", "flirty", "question", "speed"])
        await send_game(chat_id, kind, context.bot, query.from_user.id)
        return

    if data.startswith("admin:"):
        await admin_callback(query, chat_id, context.bot)
        return


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    text = (update.message.text or "").strip()
    user = update.effective_user
    chat = update.effective_chat
    p = ensure_player(user.id, user.first_name or user.username or "بازیکن")

    # Speed game auto-win
    active = DB["active_games"].get(str(chat.id))
    if active and active.get("type") == "speed":
        if text == active.get("target"):
            DB["active_games"].pop(str(chat.id), None)
            register_win(user.id, 80)
            save()
            await update.message.reply_text(
                f"⚡🏆 <b>{user.first_name}</b> سریع‌تر از همه بود!\n\n+80 XP 🔥\n⭐ مجموع XP: {p['xp']}",
                parse_mode="HTML",
            )
            return

    if text in ("🎮 بازی‌ها", "بازی‌ها"):
        await game_menu(update, context)
    elif text in ("🕵️ اعتراف", "اعتراف"):
        await direct_truth(update, context)
    elif text in ("🔥 جرئت", "جرئت"):
        await direct_dare(update, context)
    elif text in ("⚔️ دوئل", "دوئل"):
        await update.message.reply_text("⚔️ دوئل در مرحله بعد با انتخاب دو بازیکن و تأیید حریف فعال می‌شود.")
    elif text in ("🎰 گردونه", "گردونه"):
        await direct_roulette(update, context)
    elif text in ("🧠 سؤال گروهی", "سؤال گروهی"):
        await send_game(chat.id, "question", context.bot, user.id)
    elif text in ("⚡ مسابقه سرعت", "مسابقه سرعت"):
        await send_game(chat.id, "speed", context.bot, user.id)
    elif text in ("⚖️ حکم", "حکم"):
        await punishment(update, context)
    elif text in ("👤 پروفایل من", "پروفایل من"):
        await profile(update, context)
    elif text in ("🏆 رتبه‌بندی", "رتبه‌بندی"):
        await rank(update, context)
    elif text in ("📜 قوانین", "قوانین"):
        await rules(update, context)
    elif text in ("❓ راهنما", "راهنما"):
        await help_cmd(update, context)
    elif text in ("👑 پنل مدیر", "پنل مدیر"):
        await admin_menu(update, context)
    elif text == "انجام شد":
        p["completed_penalties"] += 1
        p["coins"] += 15
        add_xp(user.id, 35)
        save()
        await update.message.reply_text("✅ حکم ثبت شد! +35 XP و +15 🪙")
    else:
        # Keep group chatter untouched; only answer in private chat.
        if chat.type == ChatType.PRIVATE:
            await update.message.reply_text("از منوی پایین یک گزینه انتخاب کن 👇", reply_markup=main_keyboard(is_admin(user.id)))


# ------------------------------------------------------------
# Startup
# ------------------------------------------------------------
async def post_init(application: Application):
    await application.bot.set_my_commands([
        # Telegram requires Latin command identifiers; UI remains Persian.
        BotCommand("start", "شروع ربات"),
        BotCommand("menu", "منوی بازی"),
        BotCommand("profile", "پروفایل من"),
        BotCommand("rank", "رتبه‌بندی"),
        BotCommand("help", "راهنما"),
        BotCommand("id", "شناسه من"),
    ])
    log.info("Bot commands configured")


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    return app


def validate_config() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing")
    if ADMIN_ID is None:
        log.warning("ADMIN_ID is not set: admin panel will be unavailable")


def main() -> None:
    validate_config()
    start_health_server()
    app = build_app()
    log.info("Night Game Bot starting...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
