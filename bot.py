import asyncio
import json
import os
import random
import re
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# ApexRival 3.0
# A social game engine for Telegram group chats.
# Single-file edition, JSON persistence, Render-friendly.
# ============================================================

BOT_NAME = "ApexRival"
BOT_VERSION = "3.0"
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
PORT = int(os.getenv("PORT", "10000") or 10000)
DATA_FILE = os.getenv("DATA_FILE", "game_data.json")
SAVE_EVERY_SECONDS = 12

# -----------------------------
# Content banks
# -----------------------------
TRUTHS = [
    "آخرین سوتی‌ای که هنوز یادت می‌آید چیست؟",
    "کدام عادتت را دوست داری کمتر دیده شود؟",
    "بامزه‌ترین سوءتفاهمی که برایت پیش آمده چه بوده؟",
    "اگر یک هفته جای یکی از افراد گروه بودی، چه کسی را انتخاب می‌کردی و چرا؟",
    "کدام ویژگی شخصیتی در دیگران خیلی سریع توجهت را جلب می‌کند؟",
    "یک تصمیم کوچک که نتیجه بزرگی برایت داشت چیست؟",
    "اگر بتوانی یک قانون خنده‌دار برای گروه اضافه کنی، چیست؟",
    "بدترین بهانه‌ای که برای نرسیدن به کاری آورده‌ای چیست؟",
    "کدام مهارت را دوست داری همین امشب بلد باشی؟",
    "اگر قرار باشد یک لقب به خودت بدهی، چیست؟",
    "کدام آهنگ یا سبک موسیقی سریع حالت را بهتر می‌کند؟",
    "بامزه‌ترین اشتباه تایپی که داشته‌ای چه بوده؟",
    "اگر فقط یک نفر را برای یک سفر هیجانی انتخاب کنی، چه کسی؟",
    "در چه چیزی فکر می‌کنی از چیزی که بقیه تصور می‌کنند بهتر هستی؟",
    "آخرین باری که از خنده نتوانستی جدی بمانی کی بود؟",
    "کدام تصمیم را دوست داری دوباره از اول تجربه کنی؟",
    "سه کلمه برای توصیف خودت چیست؟",
    "چه چیزی می‌تواند در چند ثانیه حالت را خوب کند؟",
    "یک راز کاملاً بی‌خطر و بامزه درباره خودت بگو.",
    "اگر زندگی‌ات یک عنوان فیلم داشت، چه عنوانی می‌گذاشتی؟",
    "از کدام ویژگی خودت بیشتر راضی هستی؟",
    "یک کاری که مدت‌هاست می‌گویی بعداً انجام می‌دهم چیست؟",
    "اگر فقط یک غذای موردعلاقه را تا یک ماه بخوری، چه انتخابی می‌کنی؟",
    "کدام رفتار در چت گروهی سریعاً حوصله‌ات را سر می‌برد؟",
    "بدترین ترکیب غذایی که امتحان کرده‌ای چیست؟",
    "اگر بتوانی یک روز نامرئی شوی، یک کار بی‌خطر و بامزه چه می‌کنی؟",
    "چه چیزی بیشتر از بقیه باعث خجالتت می‌شود؟",
    "کدام بازی گروهی را بیشتر از همه دوست داری؟",
    "اگر یک نفر در گروه را برای مسابقه اطلاعات عمومی انتخاب کنی، چه کسی؟",
    "چه چیزی هست که همیشه قول می‌دهی زود انجامش بدهی ولی طول می‌کشد؟",
]

DARES = [
    "با لحن گوینده اخبار، آخرین چیزی که خوردی را گزارش کن.",
    "۳۰ ثانیه فقط با ایموجی جواب بده.",
    "یک تبلیغ ۱۵ ثانیه‌ای برای خودت بنویس.",
    "سه تعریف واقعی و محترمانه از سه نفر گروه بنویس.",
    "یک داستان سه‌جمله‌ای بساز که هر جمله با یک کلمه مشخص شروع شود.",
    "یک ویس کوتاه با لحن گوینده رادیو بفرست.",
    "بدون استفاده از کلمه «من» یک جمله درباره خودت بنویس.",
    "یک شعار عجیب برای ApexRival بساز.",
    "یک پیام کاملاً رسمی درباره یک موضوع مسخره بنویس.",
    "با پنج ایموجی حال امروزت را تعریف کن و معنی‌شان را نگو.",
    "برای نفر سمت راستت یک لقب محترمانه و بامزه پیشنهاد بده.",
    "یک جمله بنویس که هم تعریف باشد و هم خنده‌دار.",
    "در سه پیام پشت سر هم فقط یک کلمه در هر پیام بفرست و یک داستان بساز.",
    "یک شعار تبلیغاتی برای بازنده این دور طراحی کن.",
    "اسم یک فیلم خیالی درباره این گروه بساز.",
    "در یک پیام خودت را مثل یک شخصیت بازی ویدیویی معرفی کن.",
    "یک چیستان کوتاه بساز و بقیه را به چالش بکش.",
    "یک جمله انگیزشی خیلی اغراق‌آمیز برای گروه بنویس.",
    "یک جواب خیلی جدی به یک سؤال کاملاً خنده‌دار بده.",
    "یک اسم مستعار موقت برای خودت انتخاب کن و تا پایان دور استفاده کن.",
]

FLIRTY = [
    "یک تعریف محترمانه و واقعی از یک نفر در گروه بگو؛ طرف مقابل حق رد کردن دارد.",
    "یک لقب بامزه و محترمانه برای یک نفر انتخاب کن؛ بدون توهین یا کنایه.",
    "یک جمله شروع گفت‌وگوی رمانتیکِ محترمانه بنویس، بدون خطاب اجباری به شخص خاص.",
    "یک ویژگی شخصیتی جذاب را نام ببر و توضیح بده چرا برایت جذاب است.",
    "اگر دوست داشتی، درباره استایل یا انرژی یکی از اعضا یک تعریف کوتاه بگو.",
    "یک سناریوی آشنایی محترمانه و کوتاه بساز؛ انتخاب طرف مقابل کاملاً آزاد است.",
    "بگو چه چیزی باعث می‌شود یک گفت‌وگوی رمانتیک از نظر تو جذاب و محترمانه باشد.",
    "یک جمله خیلی کوتاه و بامزه برای شروع یک قرار فرضی بنویس.",
    "یک تعریف غیرظاهری درباره شخصیت یک نفر در گروه بگو.",
    "اگر بخواهی برای یک قرار ایده‌آل یک قانون بگذاری، چیست؟",
]

ADULT_SAFE = [
    "۱۸+: در یک رابطه سالم، مهم‌ترین مرز شخصی از نظر تو چیست؟",
    "۱۸+: یک سؤال صمیمی اما غیرجنسی از گروه بپرس؛ هرکس می‌تواند رد کند.",
    "۱۸+: یک ویژگی شخصیتی جذاب را نام ببر و توضیح بده چرا.",
    "۱۸+: درباره یک قرار ایده‌آل، فقط در حد غیرصریح و محترمانه، یک سناریوی کوتاه بگو.",
    "۱۸+: بگو چه چیزی باعث می‌شود یک رابطه برایت امن و قابل اعتماد باشد.",
    "۱۸+: یک «اگر مجبور بودی...» درباره رابطه سالم و بدون جزئیات جنسی مطرح کن.",
    "۱۸+: درباره اهمیت رضایت و مرزهای شخصی در یک رابطه یک جمله بگو.",
    "۱۸+: چه ویژگی غیرظاهری در یک فرد برایت جذاب‌تر است؟",
]

PENALTIES = [
    "یک پیام خنده‌دار با سه ایموجی تصادفی بفرست.",
    "برای دو دقیقه یک لقب بامزه و محترمانه داشته باش.",
    "یک تعریف واقعی از سه نفر گروه بنویس.",
    "یک جمله کاملاً رسمی درباره یک موضوع خنده‌دار بنویس.",
    "یک ویس کوتاه با لحن گوینده اخبار بفرست.",
    "یک شعار خنده‌دار برای بازیکن برنده بساز.",
    "سه کلمه تعیین‌شده توسط سرگروه را در یک جمله بی‌خطر استفاده کن.",
    "یک حرکت نمایشی بی‌خطر را فقط با ایموجی توضیح بده.",
    "یک داستان دو خطی بساز که پایانش را گروه انتخاب کند.",
    "تا دو پیام بعدی فقط با سؤال جواب بده.",
    "یک لقب برای Boss بساز.",
    "یک جمله را با سه لحن متفاوت بنویس: رسمی، جدی، خنده‌دار.",
    "یک مینی‌تبلیغ برای برنده این دور بساز.",
    "یک سؤال سخت ولی محترمانه از گروه بپرس.",
]

QUESTIONS = [
    "چه کسی در این گروه احتمالاً در یک مسابقه عجیب برنده می‌شود؟",
    "چه کسی بیشتر از همه می‌تواند یک راز را نگه دارد؟",
    "چه کسی احتمالاً بدون برنامه قبلی یک سفر ناگهانی می‌رود؟",
    "چه کسی احتمالاً دیرتر از همه خوابش می‌برد؟",
    "چه کسی در یک مسابقه خنده‌دار جدی‌ترین رقیب می‌شود؟",
    "چه کسی اگر مشهور شود کمتر تغییر می‌کند؟",
    "چه کسی در حل معما بهتر عمل می‌کند؟",
    "چه کسی احتمالاً بهترین اسم برای یک تیم پیدا می‌کند؟",
    "چه کسی در مذاکره سخت‌تر تسلیم می‌شود؟",
    "چه کسی احتمالاً بیشتر از بقیه ریسک حساب‌شده می‌کند؟",
    "چه کسی احتمالاً زودتر یک بازی جدید یاد می‌گیرد؟",
    "چه کسی احتمالاً یک شوخی را بیش از حد ادامه می‌دهد؟",
]

BOSS_CHALLENGES = [
    "اولین بازیکنی که «APEX» را دقیقاً بفرستد +۵ XP می‌گیرد.",
    "هرکس یک کلمه بفرستد؛ سرگروه خلاق‌ترین ترکیب را انتخاب کند و +۵ XP بدهد.",
    "سرگروه یک عدد ۱ تا ۹ انتخاب کند؛ نزدیک‌ترین حدس +۵ XP بگیرد.",
    "همه یک ایموجی می‌فرستند؛ سرگروه یک پاسخ را برای +۳ XP انتخاب کند.",
    "یک معمای کوتاه مطرح می‌شود؛ اولین پاسخ درست +۷ XP می‌گیرد.",
]

EVENTS = [
    ("✨ دو برابر XP", "XP مرحله بعد دو برابر می‌شود."),
    ("🛡 سپر طلایی", "یک بازیکن تصادفی یک سپر می‌گیرد."),
    ("💰 باران سکه", "سه بازیکن تصادفی +۳ سکه می‌گیرند."),
    ("🎯 مأموریت فوری", "یک بازیکن تصادفی مأموریت کوتاه می‌گیرد."),
    ("🔥 دور سرعت", "مرحله بعد به مسابقه سرعت تبدیل می‌شود."),
    ("🎲 هرج‌ومرج", "مرحله بعد به انتخاب تصادفی بازی می‌شود."),
]

ACHIEVEMENTS = {
    "first_win": ("🏆 اولین برد", "اولین برد خودت را ثبت کن."),
    "ten_wins": ("⚔️ ۱۰ برد", "۱۰ برد بگیر."),
    "streak5": ("🔥 استریک ۵", "۵ برد پیاپی بگیر."),
    "coins100": ("💰 ثروتمند", "به ۱۰۰ سکه برس."),
    "xp500": ("⭐ استاد", "به ۵۰۰ XP برس."),
    "games20": ("🎮 معتاد بازی", "۲۰ بازی تجربه کن."),
    "missions10": ("🤫 مأمور مخفی", "۱۰ مأموریت کامل کن."),
    "boss5": ("👑 Boss Hunter", "۵ Boss Round را بازی کن."),
    "duels10": ("⚔️ Duelist", "۱۰ دوئل انجام بده."),
    "votes10": ("🗳 رأی‌دهنده", "۱۰ رأی‌گیری انجام بده."),
}

SHOP = {
    "shield": {"name": "🛡 سپر", "price": 20, "desc": "یک مجازات را رد می‌کند."},
    "reroll": {"name": "🎲 ریرول", "price": 15, "desc": "محتوای مرحله جاری را یک‌بار عوض می‌کند."},
    "double_xp": {"name": "⚡ XP×2", "price": 35, "desc": "پاداش XP دور بعد دو برابر می‌شود."},
    "pass": {"name": "🎫 پاس", "price": 30, "desc": "یک چالش شخصی را رد می‌کند."},
    "lucky": {"name": "🍀 شانس", "price": 25, "desc": "شانس برد پاداش مرحله بعد را کمی بهتر می‌کند."},
}

DEFAULT_USER = {
    "name": "کاربر",
    "xp": 0,
    "coins": 0,
    "wins": 0,
    "losses": 0,
    "games": 0,
    "streak": 0,
    "best_streak": 0,
    "duels": 0,
    "votes": 0,
    "missions": 0,
    "boss": 0,
    "level": 1,
    "banned": False,
    "achievements": [],
    "inventory": {k: 0 for k in SHOP},
    "stats": {"truth": 0, "dare": 0, "flirty": 0, "adult": 0, "speed": 0, "roulette": 0, "vote": 0, "secret": 0},
    "created_at": 0,
    "adult_ok": False,
}

DEFAULT_GROUP = {
    "enabled": True,
    "adult_mode": False,
    "max_players": 20,
    "min_players": 2,
    "active_game": None,
    "created_games": 0,
    "settings": {
        "xp_multiplier": 1,
        "coins_multiplier": 1,
        "allow_flirty": True,
        "allow_random_events": True,
        "allow_vote": True,
        "allow_duel": True,
        "allow_secret": True,
        "allow_boss": True,
        "penalty_deadline": 300,
        "auto_end_minutes": 90,
    },
    "content": {},
}

DATA: dict[str, Any] = {}
LOCK = threading.RLock()
LAST_SAVE = 0.0

# -----------------------------
# Persistence / migration
# -----------------------------

def now_ts() -> int:
    return int(time.time())


def default_data() -> dict[str, Any]:
    return {
        "schema": 3,
        "users": {},
        "groups": {},
        "games": {},
        "broadcast_log": [],
        "audit": [],
        "settings": {
            "max_players_default": 20,
            "adult_default": False,
            "xp_multiplier": 1,
            "coins_multiplier": 1,
        },
    }


def merge_defaults(target: dict[str, Any], template: dict[str, Any]) -> None:
    for key, value in template.items():
        if key not in target:
            target[key] = deepcopy(value)
        elif isinstance(value, dict) and isinstance(target[key], dict):
            merge_defaults(target[key], value)


def load_data() -> dict[str, Any]:
    data = default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            data.update(raw)
    except Exception:
        pass
    data.setdefault("users", {})
    data.setdefault("groups", {})
    data.setdefault("games", {})
    data.setdefault("audit", [])
    data.setdefault("broadcast_log", [])
    data.setdefault("global_content", {})
    data.setdefault("settings", {})
    merge_defaults(data["settings"], default_data()["settings"])
    for user in data["users"].values():
        merge_defaults(user, DEFAULT_USER)
        merge_defaults(user["inventory"], DEFAULT_USER["inventory"])
        merge_defaults(user["stats"], DEFAULT_USER["stats"])
    for group in data["groups"].values():
        merge_defaults(group, DEFAULT_GROUP)
        merge_defaults(group["settings"], DEFAULT_GROUP["settings"])
        group.setdefault("content", {})
    return data


DATA = load_data()


def save_data(force: bool = False) -> None:
    global LAST_SAVE
    current = time.time()
    if not force and current - LAST_SAVE < SAVE_EVERY_SECONDS:
        return
    tmp = DATA_FILE + ".tmp"
    with LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
        LAST_SAVE = current


def audit(action: str, actor: int, chat_id: int | None = None, details: str = "") -> None:
    with LOCK:
        DATA["audit"].append({
            "ts": now_ts(),
            "action": action,
            "actor": actor,
            "chat": chat_id,
            "details": details[:500],
        })
        DATA["audit"] = DATA["audit"][-500:]

# -----------------------------
# Data helpers
# -----------------------------

def user_key(uid: int) -> str:
    return str(uid)


def group_key(cid: int) -> str:
    return str(cid)


def get_user(uid: int, name: str = "کاربر") -> dict[str, Any]:
    with LOCK:
        user = DATA["users"].setdefault(user_key(uid), deepcopy(DEFAULT_USER))
        if user.get("created_at", 0) == 0:
            user["created_at"] = now_ts()
        if name:
            user["name"] = name
        merge_defaults(user, DEFAULT_USER)
        merge_defaults(user["inventory"], DEFAULT_USER["inventory"])
        merge_defaults(user["stats"], DEFAULT_USER["stats"])
        return user


def get_group(chat_id: int) -> dict[str, Any]:
    with LOCK:
        group = DATA["groups"].setdefault(group_key(chat_id), deepcopy(DEFAULT_GROUP))
        merge_defaults(group, DEFAULT_GROUP)
        merge_defaults(group["settings"], DEFAULT_GROUP["settings"])
        group.setdefault("content", {})
        return group


def is_admin(uid: int) -> bool:
    return bool(ADMIN_ID and uid == ADMIN_ID)


def is_banned(uid: int) -> bool:
    return bool(get_user(uid).get("banned", False))


def level_for_xp(xp: int) -> int:
    return max(1, min(100, 1 + xp // 100))


def title_for(xp: int) -> str:
    if xp >= 2500:
        return "👑 Apex Legend"
    if xp >= 1500:
        return "🔥 سلطان میدان"
    if xp >= 900:
        return "⚔️ رقیب نخبه"
    if xp >= 500:
        return "💀 کابوس گروه"
    if xp >= 250:
        return "🎯 بازیکن حرفه‌ای"
    if xp >= 100:
        return "🧨 دردسرساز"
    if xp >= 50:
        return "⭐ رقیب جوان"
    return "🌱 تازه‌وارد"


def add_xp(uid: int, amount: int, name: str = "کاربر", group_mult: int = 1) -> int:
    user = get_user(uid, name)
    amount = max(0, int(amount)) * max(1, int(group_mult))
    before_level = level_for_xp(int(user["xp"]))
    user["xp"] = max(0, int(user["xp"]) + amount)
    user["level"] = level_for_xp(int(user["xp"]))
    after_level = user["level"]
    check_achievements(uid)
    return after_level - before_level


def add_coins(uid: int, amount: int, name: str = "کاربر", group_mult: int = 1) -> None:
    user = get_user(uid, name)
    amount = int(amount) * max(1, int(group_mult))
    user["coins"] = max(0, int(user["coins"]) + amount)
    check_achievements(uid)


def spend_coins(uid: int, amount: int) -> bool:
    user = get_user(uid)
    amount = max(0, int(amount))
    if int(user["coins"]) < amount:
        return False
    user["coins"] -= amount
    return True


def inventory(uid: int) -> dict[str, int]:
    return get_user(uid)["inventory"]


def grant_item(uid: int, item: str, amount: int = 1) -> None:
    if item not in SHOP:
        return
    inventory(uid)[item] = max(0, int(inventory(uid).get(item, 0)) + int(amount))


def take_item(uid: int, item: str, amount: int = 1) -> bool:
    inv = inventory(uid)
    if int(inv.get(item, 0)) < amount:
        return False
    inv[item] -= amount
    return True


def check_achievements(uid: int) -> list[str]:
    user = get_user(uid)
    unlocked = []
    current = set(user.get("achievements", []))
    checks = {
        "first_win": user["wins"] >= 1,
        "ten_wins": user["wins"] >= 10,
        "streak5": user["best_streak"] >= 5,
        "coins100": user["coins"] >= 100,
        "xp500": user["xp"] >= 500,
        "games20": user["games"] >= 20,
        "missions10": user["missions"] >= 10,
        "boss5": user["boss"] >= 5,
        "duels10": user["duels"] >= 10,
        "votes10": user["votes"] >= 10,
    }
    for key, ok in checks.items():
        if ok and key not in current:
            user["achievements"].append(key)
            unlocked.append(key)
    return unlocked


def game_title(uid: int) -> str:
    return title_for(int(get_user(uid).get("xp", 0)))


def mention_user(uid: int, name: str) -> str:
    return f'<a href="tg://user?id={int(uid)}">{escape(name or "بازیکن")}</a>'


def name_of(uid: int, game: dict[str, Any] | None = None) -> str:
    if game:
        n = game.get("names", {}).get(str(uid))
        if n:
            return str(n)
    return str(get_user(uid).get("name", "بازیکن"))


def active_game(chat_id: int) -> dict[str, Any] | None:
    gid = get_group(chat_id).get("active_game")
    if not gid:
        return None
    game = DATA["games"].get(gid)
    if not game:
        get_group(chat_id)["active_game"] = None
    return game


def make_game(chat_id: int, leader_id: int, leader_name: str) -> dict[str, Any]:
    g = get_group(chat_id)
    gid = f"{chat_id}:{now_ts()}:{random.randint(1000, 9999)}"
    game = {
        "id": gid,
        "chat_id": chat_id,
        "leader_id": leader_id,
        "leader_name": leader_name,
        "status": "lobby",
        "phase": "lobby",
        "round": 0,
        "created_at": now_ts(),
        "started_at": 0,
        "last_activity": now_ts(),
        "players": [leader_id],
        "names": {str(leader_id): leader_name},
        "round_scores": {},
        "pending_penalties": {},
        "completed_missions": {},
        "duel": None,
        "speed": None,
        "vote": None,
        "secret": None,
        "spy": None,
        "boss": None,
        "event": None,
        "used_content": {},
        "settings": {
            "max_players": int(g["max_players"]),
            "min_players": int(g["min_players"]),
        },
    }
    DATA["games"][gid] = game
    g["active_game"] = gid
    g["created_games"] = int(g.get("created_games", 0)) + 1
    audit("create_game", leader_id, chat_id, gid)
    return game


def touch_game(game: dict[str, Any]) -> None:
    game["last_activity"] = now_ts()


def end_game(game: dict[str, Any], reason: str = "پایان توسط سرگروه") -> None:
    game["status"] = "finished"
    game["phase"] = "finished"
    game["finished_at"] = now_ts()
    game["finish_reason"] = reason
    chat_id = int(game["chat_id"])
    group = get_group(chat_id)
    if group.get("active_game") == game["id"]:
        group["active_game"] = None
    audit("end_game", int(game["leader_id"]), chat_id, reason)


def choose_content(game: dict[str, Any], key: str, bank: list[str]) -> str:
    group = get_group(int(game["chat_id"]))
    custom = group.get("content", {}).get(key, [])
    global_custom = DATA.get("global_content", {}).get(key, [])
    pool = [*custom, *global_custom, *bank]
    if not pool:
        return "محتوایی برای این مرحله موجود نیست."
    used = set(game.get("used_content", {}).get(key, []))
    candidates = [x for x in pool if x not in used] or pool
    pick = random.choice(candidates)
    game.setdefault("used_content", {}).setdefault(key, []).append(pick)
    game["used_content"][key] = game["used_content"][key][-50:]
    return pick


def group_multiplier(chat_id: int, key: str) -> int:
    g = get_group(chat_id)
    return max(1, int(g.get("settings", {}).get(key, 1)))


def valid_player(game: dict[str, Any], uid: int) -> bool:
    return uid in [int(x) for x in game.get("players", [])]


def leader_of(game: dict[str, Any], uid: int) -> bool:
    return is_admin(uid) or int(game.get("leader_id", 0)) == uid


def min_players_ok(game: dict[str, Any]) -> bool:
    return len(game.get("players", [])) >= int(game.get("settings", {}).get("min_players", 2))

# -----------------------------
# Keyboards / UI
# -----------------------------

MAIN_BUTTONS = [
    ["🎮 بازی‌ها", "🎯 حالت‌ها", "👤 پروفایل من"],
    ["⚔️ دوئل", "🎰 گردونه", "⚡ سرعت"],
    ["🤫 مأموریت", "🕵️ جاسوس", "🗳 رأی‌گیری"],
    ["☠️ حکم من", "🛒 فروشگاه", "🏆 رتبه‌بندی"],
    ["🏅 دستاوردها", "📜 قوانین", "❓ راهنما"],
]


def main_keyboard(uid: int) -> ReplyKeyboardMarkup:
    rows = [r[:] for r in MAIN_BUTTONS]
    if is_admin(uid):
        rows.append(["👑 پنل Super Admin"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def lobby_keyboard(gid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟 ثبت‌نام", callback_data=f"join|{gid}"), InlineKeyboardButton("❌ خروج", callback_data=f"leave|{gid}")],
        [InlineKeyboardButton("👥 بازیکنان", callback_data=f"players|{gid}"), InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"refresh|{gid}")],
        [InlineKeyboardButton("▶️ شروع بازی", callback_data=f"start|{gid}"), InlineKeyboardButton("🛑 لغو", callback_data=f"cancel|{gid}")],
        [InlineKeyboardButton("⚙️ تنظیمات لابی", callback_data=f"lset|{gid}"), InlineKeyboardButton("❓ قوانین", callback_data="rules")],
    ])


def lobby_settings_keyboard(gid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ حداکثر +1", callback_data=f"maxup|{gid}"), InlineKeyboardButton("➖ حداکثر -1", callback_data=f"maxdown|{gid}")],
        [InlineKeyboardButton("➕ حداقل +1", callback_data=f"minup|{gid}"), InlineKeyboardButton("➖ حداقل -1", callback_data=f"mindown|{gid}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"refresh|{gid}")],
    ])


def game_keyboard(game: dict[str, Any]) -> InlineKeyboardMarkup:
    chat_id = int(game["chat_id"])
    gs = get_group(chat_id).get("settings", {})
    rows = [
        [InlineKeyboardButton("🕵️ اعتراف", callback_data="play|truth"), InlineKeyboardButton("🔥 جرئت", callback_data="play|dare")],
        [InlineKeyboardButton("💘 فلرت", callback_data="play|flirty"), InlineKeyboardButton("🧠 سؤال", callback_data="play|question")],
        [InlineKeyboardButton("⚔️ دوئل", callback_data="mode|duel"), InlineKeyboardButton("🎰 گردونه", callback_data="mode|roulette")],
        [InlineKeyboardButton("⚡ سرعت", callback_data="mode|speed"), InlineKeyboardButton("🤫 مأموریت", callback_data="mode|secret")],
        [InlineKeyboardButton("🕵️ جاسوس", callback_data="mode|spy"), InlineKeyboardButton("🗳 رأی‌گیری", callback_data="mode|vote")],
        [InlineKeyboardButton("👑 Boss", callback_data="mode|boss"), InlineKeyboardButton("🎲 رویداد", callback_data="mode|event")],
        [InlineKeyboardButton("☠️ حکم من", callback_data="penalty|mine"), InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("📊 وضعیت دست", callback_data="gameinfo"), InlineKeyboardButton("⏭ دور بعد", callback_data="leader|next")],
        [InlineKeyboardButton("🛑 پایان بازی", callback_data="end")],
    ]
    if get_group(chat_id).get("adult_mode"):
        rows.insert(2, [InlineKeyboardButton("🔞 +18 غیرصریح", callback_data="play|adult")])
    if not gs.get("allow_duel", True):
        rows = [r for r in rows if not any("دوئل" in (b.text or "") for b in r)]
    return InlineKeyboardMarkup(rows)


def host_keyboard(game: dict[str, Any]) -> InlineKeyboardMarkup:
    gid = game["id"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 حالت تصادفی", callback_data="leader|random"), InlineKeyboardButton("☠️ حکم تصادفی", callback_data="leader|penalty")],
        [InlineKeyboardButton("🛠 کنترل بازی", callback_data=f"host|{gid}"), InlineKeyboardButton("📊 آمار دست", callback_data="gameinfo")],
        [InlineKeyboardButton("🛑 پایان بازی", callback_data="end")],
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار کلی", callback_data="admin|stats"), InlineKeyboardButton("👥 کاربران", callback_data="admin|users")],
        [InlineKeyboardButton("🎮 بازی‌های فعال", callback_data="admin|games"), InlineKeyboardButton("🌐 گروه‌ها", callback_data="admin|groups")],
        [InlineKeyboardButton("⚙️ تنظیمات سراسری", callback_data="admin|settings"), InlineKeyboardButton("🔞 +18 گروه", callback_data="admin|adult")],
        [InlineKeyboardButton("📝 محتوای بازی", callback_data="admin|content"), InlineKeyboardButton("🛒 فروشگاه", callback_data="admin|shop")],
        [InlineKeyboardButton("🧹 پاکسازی", callback_data="admin|cleanup"), InlineKeyboardButton("💾 ذخیره فوری", callback_data="admin|save")],
        [InlineKeyboardButton("📜 Audit Log", callback_data="admin|audit"), InlineKeyboardButton("📣 Broadcast", callback_data="admin|broadcast")],
        [InlineKeyboardButton("🏆 کاربران برتر", callback_data="admin|top"), InlineKeyboardButton("🔧 راهنما", callback_data="admin|help")],
    ])

# -----------------------------
# Text renderers
# -----------------------------

def lobby_text(game: dict[str, Any]) -> str:
    players = game.get("players", [])
    lines = []
    for i, uid in enumerate(players, 1):
        lines.append(f"{i}. {mention_user(uid, name_of(uid, game))}")
    max_p = game["settings"]["max_players"]
    min_p = game["settings"]["min_players"]
    return (
        f"🎮 <b>ApexRival — لابی جدید</b>\n\n"
        f"👑 سرگروه: {mention_user(game['leader_id'], game['leader_name'])}\n"
        f"👥 بازیکنان: <b>{len(players)}/{max_p}</b>\n"
        f"🔢 حداقل برای شروع: <b>{min_p}</b>\n\n"
        f"<b>بازیکنان ثبت‌نام‌شده:</b>\n" + "\n".join(lines) +
        "\n\n🔒 تا وقتی سرگروه «شروع بازی» را نزند، هیچ مرحله‌ای اجرا نمی‌شود."
    )


def game_info_text(game: dict[str, Any]) -> str:
    scores = []
    for uid in game.get("players", []):
        scores.append((int(game.get("round_scores", {}).get(str(uid), 0)), int(uid)))
    scores.sort(reverse=True)
    lines = [f"{i+1}. {name_of(uid, game)} — {score} امتیاز" for i, (score, uid) in enumerate(scores)]
    return (
        f"📊 <b>وضعیت ApexRival</b>\n\n"
        f"🎮 وضعیت: {'فعال' if game['status'] == 'active' else game['status']}\n"
        f"🔢 دور: <b>{game.get('round', 0)}</b>\n"
        f"👥 بازیکنان: <b>{len(game.get('players', []))}</b>\n\n"
        f"<b>امتیاز دست:</b>\n" + ("\n".join(lines) if lines else "هنوز امتیازی ثبت نشده.")
    )

# -----------------------------
# Game result helpers
# -----------------------------

def reward_player(game: dict[str, Any], uid: int, xp: int, coins: int, win: bool = False, loss: bool = False, reason: str = "") -> None:
    uid = int(uid)
    user = get_user(uid, name_of(uid, game))
    mult_xp = group_multiplier(int(game["chat_id"]), "xp_multiplier")
    mult_coins = group_multiplier(int(game["chat_id"]), "coins_multiplier")
    bonus_xp_item = take_item(uid, "double_xp")
    if bonus_xp_item:
        xp *= 2
    add_xp(uid, xp, name_of(uid, game), mult_xp)
    add_coins(uid, coins, name_of(uid, game), mult_coins)
    user["games"] = int(user.get("games", 0)) + 1
    if win:
        user["wins"] += 1
        user["streak"] += 1
        user["best_streak"] = max(user["best_streak"], user["streak"])
    if loss:
        user["losses"] += 1
        user["streak"] = 0
    game["round_scores"][str(uid)] = int(game["round_scores"].get(str(uid), 0)) + (xp if win else max(0, xp // 2))
    check_achievements(uid)


def assign_penalty(game: dict[str, Any], uid: int, text: str | None = None, source: str = "بازی") -> dict[str, Any]:
    uid = int(uid)
    penalty_text = text or choose_content(game, "penalty", PENALTIES)
    deadline = now_ts() + int(get_group(int(game["chat_id"]))["settings"].get("penalty_deadline", 300))
    item = {
        "text": penalty_text,
        "source": source,
        "created_at": now_ts(),
        "deadline": deadline,
        "done": False,
        "skipped": False,
        "shielded": False,
    }
    game.setdefault("pending_penalties", {})[str(uid)] = item
    return item


def penalty_text(game: dict[str, Any], uid: int) -> str:
    p = game.get("pending_penalties", {}).get(str(uid))
    if not p or p.get("done") or p.get("skipped"):
        return "☠️ برای تو حکم فعالی ثبت نشده."
    remain = max(0, int(p.get("deadline", now_ts())) - now_ts())
    mins = remain // 60
    secs = remain % 60
    return (
        f"☠️ <b>حکم فعال</b>\n\n{escape(p['text'])}\n\n"
        f"⏳ مهلت: <b>{mins:02d}:{secs:02d}</b>\n"
        f"🎯 منبع: {escape(p.get('source', 'بازی'))}"
    )

# -----------------------------
# Checks
# -----------------------------

async def ensure_allowed(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    get_user(user.id, user.first_name or user.username or "کاربر")
    if is_banned(user.id) and not is_admin(user.id):
        if update.callback_query:
            await update.callback_query.answer("🚫 دسترسی شما مسدود است.", show_alert=True)
        elif update.message:
            await update.message.reply_text("🚫 دسترسی شما به ApexRival مسدود شده است.")
        return False
    return True


async def require_game(chat_id: int, update: Update) -> dict[str, Any] | None:
    game = active_game(chat_id)
    if not game or game.get("status") != "active":
        if update.callback_query:
            await update.callback_query.answer("⛔ هنوز بازی فعالی وجود ندارد.", show_alert=True)
        elif update.message:
            await update.message.reply_text("⛔ هنوز بازی فعالی وجود ندارد. ابتدا یک لابی بسازید.")
        return None
    return game

# -----------------------------
# Commands
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    user = update.effective_user
    u = get_user(user.id, user.first_name or user.username or "کاربر")
    await update.message.reply_text(
        f"🎮 <b>{BOT_NAME}</b>\n\n"
        f"سلام {escape(user.first_name or 'بازیکن')}!\n"
        f"⭐ سطح: {u['level']} | XP: {u['xp']}\n"
        f"💰 سکه: {u['coins']}\n"
        f"🏅 عنوان: {title_for(u['xp'])}\n\n"
        "برای بازی گروهی، ربات را به گروه اضافه کنید و در همان گروه /game را بزنید.",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(user.id),
    )


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("🎮 /game را داخل گروه اجرا کن.")
        return
    group = get_group(chat.id)
    if not group.get("enabled", True) and not is_admin(user.id):
        await update.message.reply_text("🚫 ApexRival در این گروه غیرفعال است.")
        return
    if active_game(chat.id):
        game = active_game(chat.id)
        await update.message.reply_text(lobby_text(game) if game["status"] == "lobby" else game_info_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game["id"]) if game["status"] == "lobby" else game_keyboard(game))
        return
    game = make_game(chat.id, user.id, user.first_name or "سرگروه")
    save_data(force=True)
    await update.message.reply_text(lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game["id"]))


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    await update.message.reply_text("🎮 منوی ApexRival", reply_markup=main_keyboard(update.effective_user.id))


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    user = get_user(update.effective_user.id, update.effective_user.first_name or "بازیکن")
    unlocked = len(user.get("achievements", []))
    inv = user["inventory"]
    text = (
        f"👤 <b>پروفایل {escape(user['name'])}</b>\n\n"
        f"🏅 عنوان: {title_for(user['xp'])}\n"
        f"⭐ سطح: <b>{user['level']}</b>\n"
        f"✨ XP: <b>{user['xp']}</b>\n"
        f"💰 سکه: <b>{user['coins']}</b>\n"
        f"🏆 برد: {user['wins']} | باخت: {user['losses']}\n"
        f"🔥 استریک: {user['streak']} | رکورد: {user['best_streak']}\n"
        f"🎮 بازی‌ها: {user['games']}\n"
        f"🤫 مأموریت کامل: {user['missions']}\n"
        f"🏅 دستاوردها: {unlocked}/{len(ACHIEVEMENTS)}\n\n"
        f"🧰 موجودی: 🛡{inv['shield']} | 🎲{inv['reroll']} | ⚡{inv['double_xp']} | 🎫{inv['pass']} | 🍀{inv['lucky']}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🏅 دستاوردها", callback_data="achievements"), InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
    ]))


async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    rows = sorted(DATA["users"].items(), key=lambda item: int(item[1].get("xp", 0)), reverse=True)[:15]
    lines = []
    for i, (_, u) in enumerate(rows, 1):
        lines.append(f"{i}. {escape(str(u.get('name', 'کاربر')))} — ⭐ {u.get('xp', 0)} | 🏆 {u.get('wins', 0)}")
    await update.message.reply_text("🏆 <b>رتبه‌بندی ApexRival</b>\n\n" + ("\n".join(lines) or "هنوز کسی بازی نکرده."), parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    text = (
        "❓ <b>راهنمای ApexRival</b>\n\n"
        "1️⃣ داخل گروه /game را بزن.\n"
        "2️⃣ افراد با «ثبت‌نام» وارد Lobby می‌شوند.\n"
        "3️⃣ فقط سرگروه می‌تواند بازی را شروع کند.\n"
        "4️⃣ پس از شروع، حالت‌های بازی فعال می‌شوند.\n"
        "5️⃣ بعضی شکست‌ها به حکم و مجازات منجر می‌شوند.\n"
        "6️⃣ XP و سکه در پروفایل ذخیره می‌شوند.\n\n"
        "🔒 رضایت، احترام و امنیت همیشه اولویت دارند. هیچ مرحله‌ای نباید شامل خطر، تهدید، اجبار، آزار یا افشای اطلاعات خصوصی باشد."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🆔 User ID: <code>{update.effective_user.id}</code>\n💬 Chat ID: <code>{update.effective_chat.id}</code>", parse_mode=ParseMode.HTML)


async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    await send_shop(update.message, update.effective_user.id)


async def achievements_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    user = get_user(update.effective_user.id)
    owned = set(user.get("achievements", []))
    lines = []
    for key, (title, desc) in ACHIEVEMENTS.items():
        lines.append(f"{'✅' if key in owned else '🔒'} {title} — {desc}")
    await update.message.reply_text("🏅 <b>دستاوردها</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)


async def adult_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 فقط Super Admin می‌تواند +18 گروه را تغییر دهد.")
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("این دستور باید داخل گروه اجرا شود.")
        return
    group = get_group(update.effective_chat.id)
    group["adult_mode"] = not group["adult_mode"]
    audit("toggle_adult", update.effective_user.id, update.effective_chat.id, str(group["adult_mode"]))
    save_data(force=True)
    await update.message.reply_text(f"🔞 +18 غیرصریح: <b>{'فعال' if group['adult_mode'] else 'خاموش'}</b>", parse_mode=ParseMode.HTML)

# -----------------------------
# Lobby callbacks
# -----------------------------

async def join_lobby(query, game: dict[str, Any]) -> None:
    uid = query.from_user.id
    if game["status"] != "lobby":
        await query.answer("⛔ ثبت‌نام بسته شده.", show_alert=True); return
    if valid_player(game, uid):
        await query.answer("تو همین الان داخل لابی هستی.", show_alert=True); return
    max_p = int(game["settings"]["max_players"])
    if len(game["players"]) >= max_p:
        await query.answer("ظرفیت لابی پر شده.", show_alert=True); return
    game["players"].append(uid)
    game["names"][str(uid)] = query.from_user.first_name or "بازیکن"
    audit("join_lobby", uid, game["chat_id"], game["id"])
    touch_game(game); save_data(force=True)
    await query.answer("✅ ثبت‌نام شدی.")
    await query.edit_message_text(lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game["id"]))


async def leave_lobby(query, game: dict[str, Any]) -> None:
    uid = query.from_user.id
    if uid == int(game["leader_id"]):
        await query.answer("سرگروه باید ابتدا بازی را لغو کند.", show_alert=True); return
    if not valid_player(game, uid):
        await query.answer("تو داخل لابی نیستی.", show_alert=True); return
    game["players"].remove(uid)
    game["names"].pop(str(uid), None)
    touch_game(game); save_data(force=True)
    await query.answer("از لابی خارج شدی.")
    await query.edit_message_text(lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game["id"]))


async def start_lobby(query, game: dict[str, Any]) -> None:
    uid = query.from_user.id
    if not leader_of(game, uid):
        await query.answer("فقط سرگروه می‌تواند بازی را شروع کند.", show_alert=True); return
    if not min_players_ok(game):
        await query.answer(f"حداقل {game['settings']['min_players']} بازیکن لازم است.", show_alert=True); return
    game["status"] = "active"
    game["phase"] = "free"
    game["started_at"] = now_ts()
    game["round"] = 0
    for player in game["players"]:
        get_user(int(player), name_of(int(player), game))["games"] += 0
    audit("start_game", uid, game["chat_id"], game["id"])
    save_data(force=True)
    await query.answer("🎮 بازی شروع شد!")
    await query.edit_message_text(
        f"🟢 <b>ApexRival شروع شد!</b>\n\n👑 سرگروه: {mention_user(game['leader_id'], game['leader_name'])}\n👥 بازیکنان: <b>{len(game['players'])}</b>\n\nحالا حالت‌های بازی فعال‌اند.",
        parse_mode=ParseMode.HTML,
        reply_markup=game_keyboard(game),
    )


async def cancel_lobby(query, game: dict[str, Any]) -> None:
    if not leader_of(game, query.from_user.id):
        await query.answer("فقط سرگروه می‌تواند لغو کند.", show_alert=True); return
    end_game(game, "لغو توسط سرگروه")
    save_data(force=True)
    await query.answer("لابی لغو شد.")
    await query.edit_message_text("🛑 <b>لابی لغو شد.</b>", parse_mode=ParseMode.HTML)

# -----------------------------
# Modes
# -----------------------------

async def send_truth_or_dare(message, game, kind: str) -> None:
    key = kind
    bank = TRUTHS if kind == "truth" else DARES
    icon = "🕵️" if kind == "truth" else "🔥"
    title = "اعتراف" if kind == "truth" else "جرئت"
    text = choose_content(game, key, bank)
    game["round"] += 1
    game["phase"] = kind
    touch_game(game)
    save_data()
    await message.reply_text(
        f"{icon} <b>{title}</b> — دور {game['round']}\n\n{escape(text)}\n\nهر بازیکن می‌تواند با رعایت قوانین بازی شرکت کند.",
        parse_mode=ParseMode.HTML,
        reply_markup=game_keyboard(game),
    )


async def send_flirty(message, game) -> None:
    if not get_group(game["chat_id"])["settings"].get("allow_flirty", True):
        await message.reply_text("💘 فلرت در این گروه غیرفعال است."); return
    text = choose_content(game, "flirty", FLIRTY)
    game["round"] += 1
    game["phase"] = "flirty"
    touch_game(game); save_data()
    await message.reply_text(f"💘 <b>فلرت محترمانه</b>\n\n{escape(text)}\n\n❗ رضایت کامل و امکان رد کردن حفظ می‌شود.", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))


async def send_adult(message, game) -> None:
    if not get_group(game["chat_id"]).get("adult_mode"):
        await message.reply_text("🔒 +18 فعال نیست."); return
    text = choose_content(game, "adult", ADULT_SAFE)
    game["round"] += 1
    game["phase"] = "adult"
    touch_game(game); save_data()
    await message.reply_text(f"🔞 <b>+18 غیرصریح</b>\n\n{escape(text)}\n\n✅ غیرصریح، داوطلبانه و قابل رد کردن.", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))


async def send_question(message, game) -> None:
    text = choose_content(game, "question", QUESTIONS)
    game["round"] += 1
    game["phase"] = "question"
    touch_game(game); save_data()
    await message.reply_text(f"🧠 <b>سؤال گروهی</b>\n\n{escape(text)}", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))


async def roulette(message, game) -> None:
    players = game["players"]
    if len(players) < 2:
        await message.reply_text("حداقل دو بازیکن لازم است."); return
    target = random.choice(players)
    penalty = assign_penalty(game, target, source="🎰 گردونه")
    game["round"] += 1
    game["phase"] = "roulette"
    get_user(target)["losses"] += 1
    add_coins(target, 1, name_of(target, game))
    touch_game(game); save_data(force=True)
    await message.reply_text(
        f"🎰 <b>گردونه چرخید!</b>\n\n🎯 انتخاب: {mention_user(target, name_of(target, game))}\n\n☠️ <b>حکم:</b> {escape(penalty['text'])}",
        parse_mode=ParseMode.HTML,
        reply_markup=game_keyboard(game),
    )


async def speed(message, game) -> None:
    if game.get("speed"):
        await message.reply_text("⚡ یک مسابقه سرعت همین الان فعال است."); return
    answer = random.randint(10, 99)
    duration = random.randint(8, 15)
    game["speed"] = {"answer": answer, "expires": time.time() + duration, "started": now_ts()}
    game["round"] += 1
    game["phase"] = "speed"
    touch_game(game); save_data(force=True)
    await message.reply_text(f"⚡ <b>مسابقه سرعت!</b>\n\nاولین بازیکن ثبت‌نام‌شده که عدد <b>{answer}</b> را دقیقاً بفرستد برنده است.\n⏱ {duration} ثانیه", parse_mode=ParseMode.HTML)


async def create_vote(message, game) -> None:
    if len(game["players"]) < 3:
        await message.reply_text("🗳 برای رأی‌گیری حداقل ۳ بازیکن لازم است."); return
    candidates = random.sample(game["players"], min(len(game["players"]), 5))
    game["vote"] = {"candidates": candidates, "votes": {}, "expires": time.time() + 45}
    game["round"] += 1
    game["phase"] = "vote"
    touch_game(game); save_data(force=True)
    rows = []
    for uid in candidates:
        rows.append([InlineKeyboardButton(name_of(uid, game), callback_data=f"vote|{game['id']}|{uid}")])
    rows.append([InlineKeyboardButton("📊 نتیجه فعلی", callback_data="voteinfo")])
    await message.reply_text("🗳 <b>چه کسی...؟</b>\n\nیک نفر را انتخاب کنید. هر بازیکن فقط یک رأی دارد.\n⏱ ۴۵ ثانیه", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))


async def create_secret_mission(message, game, bot) -> None:
    target = random.choice(game["players"])
    mission = random.choice([
        "کاری کن یکی از بازیکنان در پیام بعدی از کلمه «باشه» استفاده کند.",
        "یک سؤال بپرس که حداقل دو نفر جواب دهند، بدون اینکه دلیل واقعی را بگویی.",
        "در دو پیام بعدی یک ایموجی مشترک را استفاده کن.",
        "یکی از بازیکنان را وادار کن یک سؤال از تو بپرسد.",
        "یک تعریف واقعی بگو و سعی کن طرف مقابل یک کلمه خاص را بگوید.",
    ])
    game["secret"] = {"target": target, "mission": mission, "expires": time.time() + 180, "done": False}
    game["round"] += 1
    game["phase"] = "secret"
    get_user(target)["stats"]["secret"] += 1
    touch_game(game); save_data(force=True)
    try:
        await bot.send_message(chat_id=target, text=f"🤫 <b>مأموریت مخفی ApexRival</b>\n\n{escape(mission)}\n\n⏱ حدود ۳ دقیقه\nوقتی انجام شد، در گروه از دکمه «✅ انجام شد» استفاده کن.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ انجام شد", callback_data="secret_done")]]))
        public = f"🤫 <b>یک مأموریت مخفی فعال شد.</b>\n\nحدود ۳ دقیقه زمان دارد."
    except Exception:
        public = "🤫 مأموریت مخفی ساخته شد، اما ارسال پیام خصوصی ممکن نشد. بازیکن باید یک‌بار /start را در چت خصوصی ربات زده باشد."
    await message.reply_text(public, parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))


async def create_spy(message, game, bot) -> None:
    if len(game["players"]) < 4:
        await message.reply_text("🕵️ برای بازی جاسوس حداقل ۴ بازیکن لازم است."); return
    spy = random.choice(game["players"])
    location = random.choice(["کافه", "فرودگاه", "سینما", "مدرسه", "پارک", "هتل", "رستوران", "استادیوم"])
    game["spy"] = {"spy": spy, "location": location, "started": now_ts(), "votes": {}}
    game["round"] += 1
    game["phase"] = "spy"
    for uid in game["players"]:
        try:
            if int(uid) == int(spy):
                await bot.send_message(chat_id=int(uid), text="🕵️ <b>نقش تو: جاسوس</b>\n\nلوکیشن را نمی‌دانی. با سؤال‌های غیرمستقیم حدس بزن و لو نرو.", parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(chat_id=int(uid), text=f"🕵️ <b>بازی جاسوس</b>\n\n📍 لوکیشن: <b>{escape(location)}</b>\n\nجاسوس را پیدا کن.", parse_mode=ParseMode.HTML)
        except Exception:
            pass
    touch_game(game); save_data(force=True)
    await message.reply_text("🕵️ <b>بازی جاسوس شروع شد.</b>\nنقش‌ها خصوصی ارسال شدند؛ هرکس باید آماده باشد.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗳 رأی نهایی", callback_data="spyvote")], [InlineKeyboardButton("🛑 پایان جاسوسی", callback_data="endmode")]]))


async def duel_start(message, game) -> None:
    if game.get("duel") and game["duel"].get("status") in ("pending", "active"):
        await message.reply_text("⚔️ یک دوئل در حال انجام است."); return
    players = [int(x) for x in game["players"]]
    challenger = random.choice(players)
    targets = [x for x in players if x != challenger]
    target = random.choice(targets)
    game["duel"] = {"status": "pending", "challenger": challenger, "target": target, "round": 0, "choices": {}}
    game["round"] += 1
    game["phase"] = "duel_pending"
    save_data(force=True)
    await message.reply_text(
        f"⚔️ <b>دوئل</b>\n\n{mention_user(challenger, name_of(challenger, game))} حریف {mention_user(target, name_of(target, game))} را به چالش کشید.\n\nطرف مقابل می‌تواند قبول یا رد کند.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ قبول", callback_data=f"duelaccept|{game['id']}"), InlineKeyboardButton("❌ رد", callback_data=f"dueldecline|{game['id']}")]]),
    )


async def duel_accept(query, game) -> None:
    duel = game.get("duel") or {}
    if query.from_user.id != int(duel.get("target", 0)):
        await query.answer("فقط حریف دعوت‌شده می‌تواند پاسخ دهد.", show_alert=True); return
    duel["status"] = "active"
    duel["round"] = 1
    duel["choices"] = {}
    save_data(force=True)
    await query.answer("دوئل شروع شد!")
    await query.edit_message_text(
        "⚔️ <b>دوئل شروع شد!</b>\n\nهر دو نفر یکی از گزینه‌ها را بزنند.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟥 سنگ", callback_data="duelpick|rock"), InlineKeyboardButton("📄 کاغذ", callback_data="duelpick|paper"), InlineKeyboardButton("✂️ قیچی", callback_data="duelpick|scissors")],
        ]),
    )


async def duel_pick(query, game, choice: str) -> None:
    duel = game.get("duel") or {}
    uid = query.from_user.id
    if duel.get("status") != "active" or uid not in (int(duel.get("challenger", 0)), int(duel.get("target", 0))):
        await query.answer("این دوئل برای تو نیست.", show_alert=True); return
    duel.setdefault("choices", {})[str(uid)] = choice
    if len(duel["choices"]) < 2:
        await query.answer("انتخابت ثبت شد؛ منتظر حریف باش.")
        return
    a = int(duel["challenger"]); b = int(duel["target"])
    ca = duel["choices"][str(a)]; cb = duel["choices"][str(b)]
    if ca == cb:
        result = "مساوی! دوباره انتخاب کنید."
        duel["choices"] = {}
        await query.edit_message_text(result, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 دور دوم", callback_data="duelagain")]]))
        save_data(force=True)
        return
    beats = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    winner, loser = (a, b) if beats[ca] == cb else (b, a)
    get_user(winner)["duels"] += 1
    get_user(loser)["duels"] += 1
    reward_player(game, winner, 12, 5, win=True)
    reward_player(game, loser, 3, 1, loss=True)
    penalty = assign_penalty(game, loser, source="⚔️ شکست دوئل")
    duel["status"] = "finished"
    touch_game(game); save_data(force=True)
    await query.edit_message_text(
        f"⚔️ <b>نتیجه دوئل</b>\n\n🏆 برنده: {mention_user(winner, name_of(winner, game))}\n☠️ بازنده: {mention_user(loser, name_of(loser, game))}\n\n🎁 برنده: +۱۲ XP +۵ سکه\n☠️ حکم بازنده: {escape(penalty['text'])}",
        parse_mode=ParseMode.HTML,
        reply_markup=game_keyboard(game),
    )

# -----------------------------
# Shop / penalties / achievements
# -----------------------------

async def send_shop(message, uid: int) -> None:
    user = get_user(uid)
    lines = [f"💰 موجودی: <b>{user['coins']} سکه</b>\n"]
    rows = []
    for key, item in SHOP.items():
        lines.append(f"{item['name']} — {item['price']} سکه\n{item['desc']} | موجودی: {inventory(uid)[key]}")
        rows.append([InlineKeyboardButton(f"🛒 خرید {item['name']} ({item['price']})", callback_data=f"buy|{key}")])
    await message.reply_text("🛒 <b>فروشگاه ApexRival</b>\n\n" + "\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))


async def penalty_mine(query, game) -> None:
    uid = query.from_user.id
    await query.answer()
    await query.edit_message_text(penalty_text(game, uid), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ انجام شد", callback_data="penaltydone|1"), InlineKeyboardButton("🛡 استفاده از سپر", callback_data="penaltyshield|1")],
        [InlineKeyboardButton("🎫 استفاده از پاس", callback_data="penaltypass|1")],
    ]))


async def complete_penalty(query, game) -> None:
    uid = query.from_user.id
    p = game.get("pending_penalties", {}).get(str(uid))
    if not p or p.get("done") or p.get("skipped"):
        await query.answer("حکم فعالی نداری.", show_alert=True); return
    p["done"] = True
    add_xp(uid, 4, name_of(uid, game))
    add_coins(uid, 2, name_of(uid, game))
    get_user(uid)["missions"] += 1 if p.get("source", "").startswith("🤫") else 0
    touch_game(game); save_data(force=True)
    await query.answer("✅ حکم انجام شد! +۴ XP")
    await query.edit_message_text("✅ <b>حکم ثبت شد.</b>\n+۴ XP و +۲ سکه", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))


async def shield_penalty(query, game) -> None:
    uid = query.from_user.id
    p = game.get("pending_penalties", {}).get(str(uid))
    if not p or p.get("done") or p.get("skipped"):
        await query.answer("حکم فعالی نداری.", show_alert=True); return
    if not take_item(uid, "shield"):
        await query.answer("🛡 سپر نداری.", show_alert=True); return
    p["skipped"] = True; p["shielded"] = True
    save_data(force=True)
    await query.answer("🛡 حکم با سپر رد شد.")
    await query.edit_message_text("🛡 <b>حکم با سپر رد شد.</b>", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))


async def pass_penalty(query, game) -> None:
    uid = query.from_user.id
    p = game.get("pending_penalties", {}).get(str(uid))
    if not p or p.get("done") or p.get("skipped"):
        await query.answer("حکم فعالی نداری.", show_alert=True); return
    if not take_item(uid, "pass"):
        await query.answer("🎫 پاس نداری.", show_alert=True); return
    p["skipped"] = True
    save_data(force=True)
    await query.answer("🎫 حکم با پاس رد شد.")
    await query.edit_message_text("🎫 <b>حکم با پاس رد شد.</b>", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))

# -----------------------------
# Admin
# -----------------------------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("🚫 فقط Super Admin.", show_alert=True)
        else:
            await update.message.reply_text("🚫 فقط Super Admin.")
        return
    text = (
        f"👑 <b>پنل Super Admin — {BOT_NAME} {BOT_VERSION}</b>\n\n"
        f"👥 کاربران: {len(DATA['users'])}\n"
        f"🌐 گروه‌ها: {len(DATA['groups'])}\n"
        f"🎮 کل بازی‌های ذخیره‌شده: {len(DATA['games'])}\n"
        f"📜 Audit: {len(DATA['audit'])}\n\n"
        "تو از اینجا به تنظیمات سراسری، محتوای بازی، کاربران، گروه‌ها، اقتصاد و داده‌ها دسترسی داری."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_stats(query) -> None:
    active = sum(1 for g in DATA["groups"].values() if g.get("active_game"))
    total_xp = sum(int(u.get("xp", 0)) for u in DATA["users"].values())
    total_coins = sum(int(u.get("coins", 0)) for u in DATA["users"].values())
    text = f"📊 <b>آمار کلی</b>\n\n👥 کاربران: {len(DATA['users'])}\n🌐 گروه‌ها: {len(DATA['groups'])}\n🎮 بازی فعال: {active}\n✨ مجموع XP: {total_xp}\n💰 مجموع سکه: {total_coins}"
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_users(query) -> None:
    users = sorted(DATA["users"].values(), key=lambda u: int(u.get("xp", 0)), reverse=True)[:20]
    lines = [f"{i+1}. {escape(str(u.get('name','کاربر')))} | {u.get('xp',0)} XP | {u.get('coins',0)} 🪙 | {'BAN' if u.get('banned') else 'OK'}" for i, u in enumerate(users)]
    await query.edit_message_text("👥 <b>کاربران برتر/وضعیت</b>\n\n" + ("\n".join(lines) or "خالی"), parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_games(query) -> None:
    lines = []
    for game in DATA["games"].values():
        if game.get("status") == "active":
            lines.append(f"🎮 {game['chat_id']} | {len(game['players'])} نفر | دور {game['round']} | لیدر {escape(game['leader_name'])}")
    await query.edit_message_text("🎮 <b>بازی‌های فعال</b>\n\n" + ("\n".join(lines) or "هیچ بازی فعالی وجود ندارد."), parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_groups(query) -> None:
    lines = []
    for cid, group in list(DATA["groups"].items())[:30]:
        lines.append(f"🌐 {cid} | {'فعال' if group.get('enabled', True) else 'خاموش'} | adult={'ON' if group.get('adult_mode') else 'OFF'}")
    await query.edit_message_text("🌐 <b>گروه‌ها</b>\n\n" + ("\n".join(lines) or "هیچ گروهی ثبت نشده."), parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_settings(query) -> None:
    s = DATA["settings"]
    text = f"⚙️ <b>تنظیمات سراسری</b>\n\nMax Players: {s['max_players_default']}\nAdult default: {s['adult_default']}\nXP multiplier: {s['xp_multiplier']}\nCoins multiplier: {s['coins_multiplier']}"
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("XP ×2", callback_data="adminset|xp2"), InlineKeyboardButton("XP ×1", callback_data="adminset|xp1")],
        [InlineKeyboardButton("Coins ×2", callback_data="adminset|coin2"), InlineKeyboardButton("Coins ×1", callback_data="adminset|coin1")],
        [InlineKeyboardButton("Max +5", callback_data="adminset|maxup"), InlineKeyboardButton("Max -5", callback_data="adminset|maxdown")],
        [InlineKeyboardButton("🔙 پنل", callback_data="admin|home")],
    ]))


async def admin_content(query) -> None:
    text = (
        "📝 <b>مدیریت محتوا</b>\n\n"
        "/addq متن — اعتراف/سؤال\n/addd متن — جرئت\n/addf متن — فلرت\n/addp متن — مجازات\n\n"
        "محتوای سفارشی به بانک عمومی اضافه می‌شود و در انتخاب مراحل وارد چرخه می‌شود."
    )
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_shop(query) -> None:
    await query.edit_message_text("🛒 <b>فروشگاه سراسری</b>\n\nآیتم‌ها از دیکشنری SHOP کنترل می‌شوند. قیمت‌ها در نسخه فایل‌محور قابل تغییرند.", parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_audit(query) -> None:
    rows = DATA["audit"][-15:][::-1]
    lines = [f"{datetime.fromtimestamp(a['ts'], timezone.utc).strftime('%H:%M:%S')} | {a['action']} | {a['actor']} | {a.get('chat')}" for a in rows]
    await query.edit_message_text("📜 <b>آخرین Auditها</b>\n\n" + ("\n".join(lines) or "خالی"), parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())


async def admin_cleanup(query) -> None:
    cutoff = now_ts() - 3 * 86400
    removed = 0
    for gid, game in list(DATA["games"].items()):
        if game.get("status") != "active" and int(game.get("finished_at", game.get("created_at", 0))) < cutoff:
            DATA["games"].pop(gid, None); removed += 1
    save_data(force=True)
    await query.edit_message_text(f"🧹 پاکسازی انجام شد. {removed} بازی قدیمی حذف شد.", reply_markup=admin_keyboard())

# -----------------------------
# Generic command tools
# -----------------------------

async def add_content(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 فقط Super Admin."); return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text(f"فرمت: /add_{key} متن")
        return
    # global custom content in settings; game chooser reads group content first, so store global fallback.
    DATA.setdefault("global_content", {}).setdefault(key, []).append(text[:500])
    save_data(force=True)
    await update.message.reply_text(f"✅ محتوای جدید به {key} اضافه شد.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("فرمت: /broadcast متن")
        return
    ok = fail = 0
    for uid in list(DATA["users"]):
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📣 <b>{BOT_NAME}</b>\n\n{escape(text)}", parse_mode=ParseMode.HTML)
            ok += 1
        except Exception:
            fail += 1
    DATA["broadcast_log"].append({"ts": now_ts(), "actor": update.effective_user.id, "ok": ok, "fail": fail})
    save_data(force=True)
    await update.message.reply_text(f"📣 Broadcast انجام شد. ✅ {ok} | ❌ {fail}")


async def user_mod(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(f"فرمت: /{action} USER_ID [AMOUNT]")
        return
    try:
        target = int(context.args[0])
    except Exception:
        await update.message.reply_text("USER_ID باید عدد باشد."); return
    user = get_user(target)
    if action == "ban": user["banned"] = True
    elif action == "unban": user["banned"] = False
    elif action == "reset": DATA["users"][str(target)] = deepcopy(DEFAULT_USER)
    elif action == "addxp":
        amount = int(context.args[1]); user["xp"] = max(0, user["xp"] + amount); user["level"] = level_for_xp(user["xp"])
    elif action == "addcoins": user["coins"] = max(0, user["coins"] + int(context.args[1]))
    elif action == "giveitem":
        if len(context.args) < 3 or context.args[1] not in SHOP:
            await update.message.reply_text("فرمت: /giveitem USER_ID ITEM COUNT"); return
        grant_item(target, context.args[1], int(context.args[2]))
    elif action == "setlevel":
        user["level"] = max(1, min(100, int(context.args[1])))
    audit(action, update.effective_user.id, None, str(target))
    save_data(force=True)
    await update.message.reply_text(f"✅ انجام شد: {action} → {target}")


async def set_global_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    try:
        value = max(2, min(100, int(context.args[0])))
    except Exception:
        await update.message.reply_text("فرمت: /setmaxglobal 30")
        return
    DATA["settings"]["max_players_default"] = value
    save_data(force=True)
    await update.message.reply_text(f"✅ حداکثر بازیکن پیش‌فرض شد {value}.")


async def group_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, enabled: bool) -> None:
    if not is_admin(update.effective_user.id):
        return
    try:
        chat_id = int(context.args[0]) if context.args else update.effective_chat.id
    except Exception:
        await update.message.reply_text("CHAT_ID باید عدد باشد.")
        return
    group = get_group(chat_id)
    group["enabled"] = enabled
    audit("group_on" if enabled else "group_off", update.effective_user.id, chat_id)
    save_data(force=True)
    await update.message.reply_text(f"🌐 گروه {chat_id}: {'فعال' if enabled else 'غیرفعال'} شد.")


async def force_end_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("فرمت: /endgame CHAT_ID")
        return
    try:
        chat_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("CHAT_ID باید عدد باشد.")
        return
    game = active_game(chat_id)
    if not game:
        await update.message.reply_text("🎮 بازی فعالی در این گروه نیست.")
        return
    end_game(game, "توقف اجباری توسط Super Admin")
    audit("force_end_game", update.effective_user.id, chat_id, game["id"])
    save_data(force=True)
    await update.message.reply_text(f"🛑 بازی گروه {chat_id} متوقف شد.")


async def group_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("فرمت: /setgroupmax CHAT_ID N")
        return
    try:
        chat_id = int(context.args[0]); value = max(2, min(100, int(context.args[1])))
    except Exception:
        await update.message.reply_text("CHAT_ID و N باید عدد باشند.")
        return
    get_group(chat_id)["max_players"] = value
    save_data(force=True)
    await update.message.reply_text(f"✅ حداکثر بازیکن گروه {chat_id}: {value}")


async def group_min(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("فرمت: /setgroupmin CHAT_ID N")
        return
    try:
        chat_id = int(context.args[0]); value = max(2, min(10, int(context.args[1])))
    except Exception:
        await update.message.reply_text("CHAT_ID و N باید عدد باشند.")
        return
    get_group(chat_id)["min_players"] = value
    save_data(force=True)
    await update.message.reply_text(f"✅ حداقل بازیکن گروه {chat_id}: {value}")


def normalize_command_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", name.lower())

# -----------------------------
# Callback router
# -----------------------------

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update):
        return
    query = update.callback_query
    data = query.data or ""
    parts = data.split("|")
    action = parts[0]
    chat_id = update.effective_chat.id

    if action == "rules":
        await query.answer("✅ احترام، رضایت، بدون اجبار و بدون رفتار خطرناک.", show_alert=True); return

    if action == "join" or action == "leave" or action == "start" or action == "cancel" or action == "refresh" or action == "players" or action == "lset" or action in ("maxup", "maxdown", "minup", "mindown"):
        gid = parts[1] if len(parts) > 1 else ""
        game = DATA["games"].get(gid)
        if not game or int(game.get("chat_id", 0)) != chat_id:
            await query.answer("این لابی دیگر معتبر نیست.", show_alert=True); return
        if action == "join": await join_lobby(query, game); return
        if action == "leave": await leave_lobby(query, game); return
        if action == "start": await start_lobby(query, game); return
        if action == "cancel": await cancel_lobby(query, game); return
        if action in ("refresh", "players"):
            await query.edit_message_text(lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game["id"])); return
        if action == "lset":
            if not leader_of(game, query.from_user.id): await query.answer("فقط سرگروه.", show_alert=True); return
            await query.edit_message_text(f"⚙️ <b>تنظیمات لابی</b>\nحداقل: {game['settings']['min_players']}\nحداکثر: {game['settings']['max_players']}", parse_mode=ParseMode.HTML, reply_markup=lobby_settings_keyboard(game["id"])); return
        if action in ("maxup", "maxdown", "minup", "mindown"):
            if not leader_of(game, query.from_user.id): await query.answer("فقط سرگروه.", show_alert=True); return
            if action == "maxup": game["settings"]["max_players"] = min(100, int(game["settings"]["max_players"]) + 1)
            if action == "maxdown": game["settings"]["max_players"] = max(2, int(game["settings"]["max_players"]) - 1)
            if action == "minup": game["settings"]["min_players"] = min(10, int(game["settings"]["min_players"]) + 1)
            if action == "mindown": game["settings"]["min_players"] = max(2, int(game["settings"]["min_players"]) - 1)
            if game["settings"]["min_players"] > game["settings"]["max_players"]:
                game["settings"]["min_players"] = game["settings"]["max_players"]
            save_data(force=True)
            await query.edit_message_text(f"⚙️ <b>تنظیمات لابی</b>\nحداقل: {game['settings']['min_players']}\nحداکثر: {game['settings']['max_players']}", parse_mode=ParseMode.HTML, reply_markup=lobby_settings_keyboard(game["id"])); return

    if action == "play":
        game = await require_game(chat_id, update)
        if not game: return
        kind = parts[1] if len(parts) > 1 else ""
        if kind == "truth": await send_truth_or_dare(query.message, game, "truth")
        elif kind == "dare": await send_truth_or_dare(query.message, game, "dare")
        elif kind == "flirty": await send_flirty(query.message, game)
        elif kind == "adult":
            if not get_user(query.from_user.id).get("adult_ok", False):
                await query.message.reply_text("🔞 برای ورود به +18 غیرصریح، تأیید کنید که ۱۸+ هستید و می‌توانید هر مرحله‌ای را رد کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید +18", callback_data="adultok")]]))
            else:
                await send_adult(query.message, game)
        elif kind == "question": await send_question(query.message, game)
        save_data()
        return

    if action == "mode":
        game = await require_game(chat_id, update)
        if not game: return
        if not valid_player(game, query.from_user.id) and not is_admin(query.from_user.id):
            await query.answer("فقط بازیکنان ثبت‌نام‌شده می‌توانند این مرحله را اجرا کنند.", show_alert=True); return
        kind = parts[1] if len(parts) > 1 else ""
        if kind == "duel": await duel_start(query.message, game)
        elif kind == "roulette": await roulette(query.message, game)
        elif kind == "speed": await speed(query.message, game)
        elif kind == "secret": await create_secret_mission(query.message, game, context.bot)
        elif kind == "spy": await create_spy(query.message, game, context.bot)
        elif kind == "vote": await create_vote(query.message, game)
        elif kind == "boss":
            text = choose_content(game, "boss", BOSS_CHALLENGES)
            game["boss"] = {"text": text, "created": now_ts()}; game["round"] += 1; get_user(query.from_user.id)["boss"] += 1
            await query.message.reply_text(f"👑 <b>Boss Round</b>\n\n{escape(text)}", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))
        elif kind == "event":
            title, desc = random.choice(EVENTS); game["event"] = {"title": title, "desc": desc, "created": now_ts()}; game["round"] += 1
            if title == "🛡 سپر طلایی":
                target = random.choice(game["players"]); grant_item(target, "shield"); desc += f"\n🎁 {name_of(target, game)} یک سپر گرفت."
            elif title == "💰 باران سکه":
                for target in random.sample(game["players"], min(3, len(game["players"]))): add_coins(target, 3, name_of(target, game))
            await query.message.reply_text(f"🎲 <b>{escape(title)}</b>\n\n{escape(desc)}", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))
        save_data(force=True); return

    if action == "duelaccept":
        game = await require_game(chat_id, update)
        if game: await duel_accept(query, game)
        return

    if action == "dueldecline":
        game = await require_game(chat_id, update)
        if not game: return
        duel = game.get("duel") or {}
        if query.from_user.id != int(duel.get("target", 0)):
            await query.answer("فقط حریف دعوت‌شده.", show_alert=True); return
        game["duel"] = None; save_data(force=True)
        await query.edit_message_text("❌ دعوت دوئل رد شد.", reply_markup=game_keyboard(game)); return

    if action == "duelpick":
        game = await require_game(chat_id, update)
        if game: await duel_pick(query, game, parts[1] if len(parts) > 1 else "")
        return

    if action == "duelagain":
        game = await require_game(chat_id, update)
        if game: await query.edit_message_text("⚔️ یک دور جدید دوئل آماده است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🟥 سنگ", callback_data="duelpick|rock"), InlineKeyboardButton("📄 کاغذ", callback_data="duelpick|paper"), InlineKeyboardButton("✂️ قیچی", callback_data="duelpick|scissors")]]))
        return

    if action == "vote":
        game = await require_game(chat_id, update)
        if not game or not game.get("vote"): return
        uid = query.from_user.id
        if not valid_player(game, uid): await query.answer("فقط بازیکنان ثبت‌نام‌شده.", show_alert=True); return
        if time.time() > float(game["vote"].get("expires", 0)):
            await query.answer("زمان رأی‌گیری تمام شده.", show_alert=True); return
        if str(uid) in game["vote"]["votes"]:
            await query.answer("رأی تو قبلاً ثبت شده.", show_alert=True); return
        target = int(parts[2])
        if target not in game["vote"]["candidates"]: return
        game["vote"]["votes"][str(uid)] = target
        get_user(uid)["votes"] += 1
        if len(game["vote"]["votes"]) >= len(game["players"]):
            counts: dict[int, int] = {}
            for t in game["vote"]["votes"].values(): counts[int(t)] = counts.get(int(t), 0) + 1
            target = max(counts.items(), key=lambda x: x[1])[0]
            penalty = assign_penalty(game, target, source="🗳 رأی‌گیری")
            game["vote"]["result"] = target
            save_data(force=True)
            await query.edit_message_text(f"🗳 <b>رأی‌گیری تمام شد.</b>\n\n🎯 انتخاب گروه: {mention_user(target, name_of(target, game))}\n☠️ حکم: {escape(penalty['text'])}", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game))
        else:
            await query.answer("✅ رأی ثبت شد.")
        save_data(force=True); return

    if action == "voteinfo":
        game = await require_game(chat_id, update)
        if not game or not game.get("vote"): return
        counts = {}
        for t in game["vote"]["votes"].values(): counts[str(t)] = counts.get(str(t), 0) + 1
        lines = [f"{name_of(int(uid), game)}: {count}" for uid, count in counts.items()]
        await query.answer(" | ".join(lines) if lines else "هنوز رأیی ثبت نشده.", show_alert=True); return

    if action == "secret_done":
        game = active_game(chat_id)
        if not game or not game.get("secret"): await query.answer("مأموریت فعال نیست.", show_alert=True); return
        secret = game["secret"]
        if query.from_user.id != int(secret["target"]): await query.answer("این مأموریت برای تو نیست.", show_alert=True); return
        secret["done"] = True
        get_user(query.from_user.id)["missions"] += 1
        reward_player(game, query.from_user.id, 10, 6, win=True)
        penalty = game.get("pending_penalties", {}).get(str(query.from_user.id))
        if penalty and penalty.get("source", "").startswith("🤫"):
            penalty["done"] = True
        save_data(force=True)
        await query.edit_message_text("🤫 ✅ <b>مأموریت موفق شد!</b> +۱۰ XP و +۶ سکه", parse_mode=ParseMode.HTML); return

    if action == "spyvote":
        game = await require_game(chat_id, update)
        if not game or not game.get("spy"): return
        rows = [[InlineKeyboardButton(name_of(uid, game), callback_data=f"spyguess|{game['id']}|{uid}")] for uid in game["players"]]
        await query.edit_message_text("🕵️ <b>چه کسی جاسوس است؟</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows)); return

    if action == "spyguess":
        game = await require_game(chat_id, update)
        if not game or not game.get("spy"): return
        if not valid_player(game, query.from_user.id): await query.answer("فقط بازیکنان.", show_alert=True); return
        guess = int(parts[2])
        spy = int(game["spy"]["spy"])
        if guess == spy:
            reward_player(game, query.from_user.id, 10, 5, win=True)
            penalty = assign_penalty(game, spy, source="🕵️ جاسوس")
            text = f"🎯 درست حدس زدی!\nجاسوس: {name_of(spy, game)}\n☠️ حکم جاسوس: {penalty['text']}"
        else:
            reward_player(game, query.from_user.id, 2, 1, loss=True)
            text = f"❌ حدس اشتباه بود. جاسوس {name_of(spy, game)} نبود که گفتی."
        game["spy"] = None
        save_data(force=True)
        await query.edit_message_text(text, reply_markup=game_keyboard(game)); return

    if action == "penalty":
        game = await require_game(chat_id, update)
        if game: await penalty_mine(query, game)
        return

    if action in ("penaltydone", "penaltyshield", "penaltypass"):
        game = await require_game(chat_id, update)
        if not game: return
        if action == "penaltydone": await complete_penalty(query, game)
        elif action == "penaltyshield": await shield_penalty(query, game)
        else: await pass_penalty(query, game)
        return

    if action == "adultok":
        if not get_group(chat_id).get("adult_mode"):
            await query.answer("🔒 +18 فعال نیست.", show_alert=True)
            return
        get_user(query.from_user.id)["adult_ok"] = True
        save_data(force=True)
        await query.edit_message_text("✅ تأیید شد. اکنون می‌توانید محتوای +18 غیرصریح را مشاهده کنید.")
        return

    if action == "buy":
        item = parts[1] if len(parts) > 1 else ""
        if item not in SHOP: return
        price = SHOP[item]["price"]
        if not spend_coins(query.from_user.id, price): await query.answer("💸 سکه کافی نیست.", show_alert=True); return
        grant_item(query.from_user.id, item)
        save_data(force=True)
        await query.answer(f"✅ {SHOP[item]['name']} خریداری شد.", show_alert=True); return

    if action == "shop":
        await send_shop(query.message, query.from_user.id); return

    if action == "achievements":
        u = get_user(query.from_user.id); owned = set(u.get("achievements", [])); lines = [f"{'✅' if k in owned else '🔒'} {v[0]}" for k,v in ACHIEVEMENTS.items()]
        await query.edit_message_text("🏅 <b>دستاوردها</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML); return

    if action == "gameinfo":
        game = active_game(chat_id)
        if game: await query.edit_message_text(game_info_text(game), parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game));
        return

    if action == "leader":
        game = await require_game(chat_id, update)
        if not game or not leader_of(game, query.from_user.id): await query.answer("فقط سرگروه.", show_alert=True); return
        sub = parts[1] if len(parts) > 1 else ""
        if sub == "random":
            kinds = ["truth", "dare", "question", "roulette", "speed", "secret", "vote", "duel"]
            chosen = random.choice(kinds)
            await query.message.reply_text(f"🎯 حالت تصادفی انتخاب شد: <b>{chosen}</b>", parse_mode=ParseMode.HTML)
            if chosen == "truth": await send_truth_or_dare(query.message, game, "truth")
            elif chosen == "dare": await send_truth_or_dare(query.message, game, "dare")
            elif chosen == "question": await send_question(query.message, game)
            elif chosen == "roulette": await roulette(query.message, game)
            elif chosen == "speed": await speed(query.message, game)
            elif chosen == "secret": await create_secret_mission(query.message, game, context.bot)
            elif chosen == "vote": await create_vote(query.message, game)
            elif chosen == "duel": await duel_start(query.message, game)
        elif sub == "penalty":
            target = random.choice(game["players"]); p = assign_penalty(game, target, source="👑 حکم سرگروه")
            await query.message.reply_text(f"👑 سرگروه حکم تصادفی داد به {mention_user(target, name_of(target, game))}:\n☠️ {escape(p['text'])}", parse_mode=ParseMode.HTML)
        elif sub == "next":
            game["phase"] = "free"; game["round"] += 1; touch_game(game); save_data(force=True)
            await query.edit_message_text("⏭ <b>دور بعد آماده است.</b>", parse_mode=ParseMode.HTML, reply_markup=game_keyboard(game));
        return

    if action == "host":
        game = await require_game(chat_id, update)
        if game and leader_of(game, query.from_user.id):
            await query.edit_message_text("🛠 <b>کنترل سرگروه</b>\n\nاز اینجا می‌توانی مرحله بعدی را انتخاب کنی یا بازی را متوقف کنی.", parse_mode=ParseMode.HTML, reply_markup=host_keyboard(game))
        return

    if action == "endmode":
        game = await require_game(chat_id, update)
        if game and leader_of(game, query.from_user.id): game["spy"] = None; save_data(force=True); await query.edit_message_text("🛑 حالت جاسوس تمام شد.", reply_markup=game_keyboard(game))
        return

    if action == "end":
        game = active_game(chat_id)
        if not game: await query.answer("بازی فعالی نیست.", show_alert=True); return
        if not leader_of(game, query.from_user.id): await query.answer("فقط سرگروه یا Super Admin.", show_alert=True); return
        end_game(game, "پایان توسط سرگروه")
        save_data(force=True)
        await query.edit_message_text("🏁 <b>بازی به پایان رسید.</b>\n\nنتایج در رتبه‌بندی و پروفایل‌ها ثبت شدند.", parse_mode=ParseMode.HTML); return

    if action == "admin":
        if not is_admin(query.from_user.id): await query.answer("فقط Super Admin.", show_alert=True); return
        sub = parts[1] if len(parts) > 1 else "home"
        if sub == "home": await admin_panel(update, context)
        elif sub == "stats": await admin_stats(query)
        elif sub == "users": await admin_users(query)
        elif sub == "games": await admin_games(query)
        elif sub == "groups": await admin_groups(query)
        elif sub == "settings": await admin_settings(query)
        elif sub == "content": await admin_content(query)
        elif sub == "shop": await admin_shop(query)
        elif sub == "cleanup": await admin_cleanup(query)
        elif sub == "save": save_data(force=True); await query.edit_message_text("💾 ذخیره فوری انجام شد.", reply_markup=admin_keyboard())
        elif sub == "audit": await admin_audit(query)
        elif sub == "top": await admin_users(query)
        elif sub == "help":
            help_text = (
                "🔧 <b>فرمان‌های Super Admin</b>\n\n"
                "/ban USER_ID\n/unban USER_ID\n/reset USER_ID\n"
                "/addxp USER_ID AMOUNT\n/addcoins USER_ID AMOUNT\n"
                "/giveitem USER_ID ITEM COUNT\n/setlevel USER_ID LEVEL\n"
                "/broadcast TEXT\n/setmaxglobal N\n"
                "/group_on CHAT_ID\n/group_off CHAT_ID\n/endgame CHAT_ID\n"
                "/setgroupmax CHAT_ID N\n/setgroupmin CHAT_ID N\n"
                "/adult (داخل گروه)\n/addq /addd /addf /addp"
            )
            await query.edit_message_text(help_text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())
        return

    if action == "adminset":
        if not is_admin(query.from_user.id): await query.answer("فقط Super Admin.", show_alert=True); return
        sub = parts[1]
        if sub == "xp2": DATA["settings"]["xp_multiplier"] = 2
        elif sub == "xp1": DATA["settings"]["xp_multiplier"] = 1
        elif sub == "coin2": DATA["settings"]["coins_multiplier"] = 2
        elif sub == "coin1": DATA["settings"]["coins_multiplier"] = 1
        elif sub == "maxup": DATA["settings"]["max_players_default"] = min(100, DATA["settings"]["max_players_default"] + 5)
        elif sub == "maxdown": DATA["settings"]["max_players_default"] = max(2, DATA["settings"]["max_players_default"] - 5)
        save_data(force=True); await admin_settings(query); return

# -----------------------------
# Text router
# -----------------------------

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    text = (update.message.text or "").strip()
    uid = update.effective_user.id
    chat = update.effective_chat
    if text == "👑 پنل Super Admin": await admin_panel(update, context); return
    if text == "🎮 بازی‌ها":
        game = active_game(chat.id) if chat.type in ("group", "supergroup") else None
        if not game: await update.message.reply_text("⛔ بازی فعالی نیست. /game را داخل گروه بزن.")
        elif game["status"] == "lobby": await update.message.reply_text(lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game["id"]))
        else: await update.message.reply_text("🎮 حالت‌های بازی", reply_markup=game_keyboard(game))
        return
    if text == "🎯 حالت‌ها":
        await update.message.reply_text("🎯 انتخاب حالت از منوی بازی انجام می‌شود.")
        return
    if text == "👤 پروفایل من": await profile(update, context); return
    if text == "🏆 رتبه‌بندی": await rank(update, context); return
    if text == "🛒 فروشگاه": await shop_cmd(update, context); return
    if text == "🏅 دستاوردها": await achievements_cmd(update, context); return
    if text == "📜 قوانین": await help_cmd(update, context); return
    if text == "❓ راهنما": await help_cmd(update, context); return
    mapping = {
        "⚔️ دوئل": "duel", "🎰 گردونه": "roulette", "⚡ سرعت": "speed",
        "🤫 مأموریت": "secret", "🕵️ جاسوس": "spy", "🗳 رأی‌گیری": "vote",
        "🕵️ اعتراف": "truth", "🔥 جرئت": "dare",
    }
    if text in mapping:
        game = await require_game(chat.id, update) if chat.type in ("group", "supergroup") else None
        if not game: return
        if not valid_player(game, uid) and not is_admin(uid):
            await update.message.reply_text("🔒 فقط بازیکنان ثبت‌نام‌شده می‌توانند مرحله اجرا کنند."); return
        kind = mapping[text]
        if kind in ("truth", "dare"): await send_truth_or_dare(update.message, game, kind)
        elif kind == "duel": await duel_start(update.message, game)
        elif kind == "roulette": await roulette(update.message, game)
        elif kind == "speed": await speed(update.message, game)
        elif kind == "secret": await create_secret_mission(update.message, game, context.bot)
        elif kind == "spy": await create_spy(update.message, game, context.bot)
        elif kind == "vote": await create_vote(update.message, game)
        return
    if text == "☠️ حکم من":
        game = active_game(chat.id) if chat.type in ("group", "supergroup") else None
        if game: await update.message.reply_text(penalty_text(game, uid), parse_mode=ParseMode.HTML)
        return

# -----------------------------
# Maintenance / health
# -----------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"{BOT_NAME} OK | v{BOT_VERSION}".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def start_health_server() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True, name="ApexRivalHealth").start()


async def cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    changed = False
    now = now_ts()
    for game in list(DATA["games"].values()):
        if game.get("status") == "active":
            auto_end = int(get_group(int(game["chat_id"]))["settings"].get("auto_end_minutes", 90)) * 60
            if now - int(game.get("last_activity", now)) > auto_end:
                end_game(game, "پایان خودکار به علت بی‌فعالیتی")
                changed = True
            if game.get("speed") and time.time() > float(game["speed"].get("expires", 0)):
                game["speed"] = None; changed = True
            if game.get("vote") and time.time() > float(game["vote"].get("expires", 0)):
                game["vote"] = None; changed = True
            if game.get("secret") and time.time() > float(game["secret"].get("expires", 0)):
                game["secret"] = None; changed = True
            for uid, p in game.get("pending_penalties", {}).items():
                if not p.get("done") and not p.get("skipped") and now > int(p.get("deadline", now)):
                    # Deadline is recorded rather than forcing a harmful action.
                    p["expired"] = True; changed = True
    if changed:
        save_data(force=True)
    else:
        save_data()


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        ("start", "شروع ربات"),
        ("game", "ساخت لابی بازی"),
        ("menu", "منوی ApexRival"),
        ("profile", "پروفایل"),
        ("rank", "رتبه‌بندی"),
        ("shop", "فروشگاه"),
        ("achievements", "دستاوردها"),
        ("help", "راهنما"),
        ("id", "آیدی"),
        ("admin", "پنل Super Admin"),
    ])
    if app.job_queue:
        app.job_queue.run_repeating(cleanup_job, interval=30, first=30, name="apex_cleanup")


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
    app.add_handler(CommandHandler("shop", shop_cmd))
    app.add_handler(CommandHandler("achievements", achievements_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("adult", adult_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("setmaxglobal", set_global_max))
    app.add_handler(CommandHandler("group_on", lambda u, c: group_toggle(u, c, True)))
    app.add_handler(CommandHandler("group_off", lambda u, c: group_toggle(u, c, False)))
    app.add_handler(CommandHandler("endgame", force_end_group))
    app.add_handler(CommandHandler("setgroupmax", group_max))
    app.add_handler(CommandHandler("setgroupmin", group_min))
    app.add_handler(CommandHandler("ban", lambda u, c: user_mod(u, c, "ban")))
    app.add_handler(CommandHandler("unban", lambda u, c: user_mod(u, c, "unban")))
    app.add_handler(CommandHandler("reset", lambda u, c: user_mod(u, c, "reset")))
    app.add_handler(CommandHandler("addxp", lambda u, c: user_mod(u, c, "addxp")))
    app.add_handler(CommandHandler("addcoins", lambda u, c: user_mod(u, c, "addcoins")))
    app.add_handler(CommandHandler("giveitem", lambda u, c: user_mod(u, c, "giveitem")))
    app.add_handler(CommandHandler("setlevel", lambda u, c: user_mod(u, c, "setlevel")))
    app.add_handler(CommandHandler("addq", lambda u, c: add_content(u, c, "truth")))
    app.add_handler(CommandHandler("addd", lambda u, c: add_content(u, c, "dare")))
    app.add_handler(CommandHandler("addf", lambda u, c: add_content(u, c, "flirty")))
    app.add_handler(CommandHandler("addp", lambda u, c: add_content(u, c, "penalty")))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print(f"{BOT_NAME} {BOT_VERSION} starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
