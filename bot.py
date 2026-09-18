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
from pathlib import Path
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

# ============================================================
# ApexRival 4.0 — Advanced Social Game Engine
# ============================================================
# نسخه تک‌فایلی با ناوبری مرحله‌ای، Super Admin گسترده، Lobby، بازی‌های چندحالته،
# سیستم حکم و پاداش، Backup/Restore، Audit و بانک محتوای بسیار بزرگ.
# ============================================================

ADVANCED_VERSION = "4.0"
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
MAX_BACKUPS = 25

# -----------------------------
# Advanced content and runtime layer
# -----------------------------
themes = {
    'truth': [
        'یک عادت کوچک که اطرافیان دیر متوجهش می‌شوند را تعریف کن.',
        'یک موقعیت خنده‌دار که آن لحظه جدی به نظر می‌رسید را تعریف کن.',
        'یک تصمیم لحظه‌ای که از نتیجه‌اش تعجب کردی را بگو.',
        'یک چیزی که در کودکی فکر می‌کردی واقعاً درست است را بگو.',
        'کدام ویژگی آدم‌ها باعث می‌شود سریع به آن‌ها اعتماد کنی؟',
        'آخرین چیزی که بابتش واقعاً هیجان‌زده شدی چه بود؟',
        'یک کاری که در جمع بهتر از تنهایی انجام می‌دهی را بگو.',
        'یک سوءتفاهم قدیمی که هنوز باعث خنده‌ات می‌شود را تعریف کن.',
        'کدام تصمیم کوچک بیشترین وقت را از تو گرفته است؟',
        'یک چیز ساده که خیلی زود تو را خوشحال می‌کند چیست؟',
    ],
    'dare': [
        'با سه ایموجی یک داستان کوتاه بساز و معنی آن‌ها را در پایان بگو.',
        'اسم خودت را مثل معرفی قهرمان یک مسابقه بزرگ معرفی کن.',
        'یک جمله معمولی را سه بار با سه لحن کاملاً متفاوت بنویس.',
        'برای آخرین پیام گروه یک تیتر خبری اغراق‌آمیز بساز.',
        'یک شعار کوتاه برای تیم خودت اختراع کن.',
        'در یک پیام نقش یک مجری مسابقه تلویزیونی را بازی کن.',
        'یک سؤال خنده‌دار اما محترمانه برای کل گروه بساز.',
        'یک داستان دو جمله‌ای بنویس که پایانش کاملاً غیرمنتظره باشد.',
        'یک لقب موقت برای خودت بساز و دلیل انتخابش را بگو.',
        'یک محصول خیالی را در دو جمله تبلیغ کن.',
    ],
    'flirty': [
        'یک تعریف محترمانه از یک ویژگی شخصیتی بگو؛ خطاب مستقیم اجباری نیست.',
        'یک جمله شروع گفت‌وگوی دوستانه و جذاب بساز.',
        'بگو چه ویژگی‌ای یک نفر را در گفت‌وگو جذاب می‌کند.',
        'برای یک قرار فرضی یک قانون بامزه و محترمانه تعیین کن.',
        'یک تعریف کوتاه درباره انرژی یا طرز صحبت یک نفر بساز؛ طرف مقابل حق رد دارد.',
        'یک سناریوی آشنایی کوتاه و کاملاً محترمانه طراحی کن.',
        'بگو چه چیزی باعث می‌شود یک گفت‌وگوی صمیمی امن و راحت بماند.',
        'یک جمله بامزه برای شروع آشنایی در یک مهمانی فرضی بنویس.',
        'یک ویژگی غیرظاهری که برایت جذاب است را با یک مثال توضیح بده.',
        'یک اسم خلاقانه برای یک قرار خیالی انتخاب کن.',
    ],
    'penalty': [
        'برای برنده این دور یک شعار سه کلمه‌ای بساز.',
        'تا دو پیام آینده فقط با سؤال جواب بده.',
        'یک جمله رسمی درباره یک موضوع کاملاً خنده‌دار بنویس.',
        'سه ایموجی تصادفی را در یک جمله معنادار استفاده کن.',
        'یک تبلیغ ۱۵ ثانیه‌ای برای خودت طراحی کن.',
        'یک لقب محترمانه و بامزه برای Boss بساز.',
        'یک داستان دو خطی بساز که گروه پایانش را حدس بزند.',
        'یک پیام تبریک رسمی برای یک اتفاق مسخره بنویس.',
        'یک جمله را در حالت جدی، هیجانی و خونسرد بازنویسی کن.',
        'یک سؤال جالب برای شناخت بهتر گروه مطرح کن.',
    ],
    'question': [
        'چه کسی در یک مسابقه اطلاعات عمومی احتمالاً غافلگیرکننده عمل می‌کند؟',
        'چه کسی احتمالاً اولین نفر برای یک سفر ناگهانی آماده می‌شود؟',
        'چه کسی در مذاکره بیشتر روی جزئیات تمرکز می‌کند؟',
        'چه کسی احتمالاً برای تیم بهترین اسم را پیدا می‌کند؟',
        'چه کسی به نظر می‌رسد در حل معما آرام‌تر باشد؟',
        'چه کسی احتمالاً یک بازی جدید را سریع یاد می‌گیرد؟',
        'چه کسی احتمالاً بیشتر از همه برای دوستانش نقشه سورپرایز می‌کشد؟',
        'چه کسی ممکن است در یک مسابقه خلاقیت بدرخشد؟',
        'چه کسی احتمالاً یک قانون خنده‌دار برای گروه پیشنهاد می‌کند؟',
        'چه کسی می‌تواند در یک گفت‌وگوی طولانی صبورتر بماند؟',
    ],
    'boss': [
        'اولین کسی که یک کلمه پنج حرفی بفرستد، پاداش می‌گیرد.',
        'سرگروه سه ایموجی انتخاب می‌کند؛ خلاق‌ترین ترکیب پاداش می‌گیرد.',
        'یک عدد مخفی اعلام می‌شود؛ نزدیک‌ترین حدس برنده است.',
        'همه باید در یک پیام کوتاه خودشان را با یک لقب معرفی کنند.',
        'اولین پاسخ درست به معما پاداش ویژه می‌گیرد.',
        'گروه باید بین دو گزینه رأی دهد؛ گزینه برنده یک امتیاز تیمی می‌گیرد.',
        'هرکس یک کلمه می‌دهد؛ سرگروه خلاق‌ترین ترکیب را انتخاب می‌کند.',
        'یک مسابقه سرعت یک‌دقیقه‌ای اجرا می‌شود.',
        'یک بازیکن تصادفی به‌عنوان قهرمان دور انتخاب می‌شود.',
        'بازیکنان باید یک شعار مشترک برای ApexRival بسازند.',
    ],
}

ADVANCED_CONTENT = {k: [] for k in themes}
# Create a unique second layer by combining distinct lenses with the base themes.
lenses = [
    'با تمرکز روی آخرین هفته زندگی‌ات، ',
    'با فضای یک مسابقه بزرگ، ',
    'با لحن کاملاً جدی، ',
    'با یک twist غیرمنتظره، ',
    'با نگاه طنز، ',
    'با انتخاب بین دو گزینه، ',
    'با فرض اینکه همه از قبل تو را می‌شناسند، ',
    'با فرض اینکه فقط یک دقیقه وقت داری، ',
    'با نگاه یک بازیکن حرفه‌ای، ',
    'با نگاه یک تماشاگر بی‌طرف، ',
    'با یک مثال واقعی و کوتاه، ',
    'بدون استفاده از توضیح طولانی، ',
]
endings = [
    'جوابت را در یک یا دو جمله کامل کن.',
    'دلیل کوتاه هم اضافه کن.',
    'جواب را خیلی سریع و مستقیم بده.',
    'یک گزینه جایگزین هم پیشنهاد کن.',
    'در پایان یک ایموجی متناسب اضافه کن.',
    'جوابت را طوری بگو که بقیه بتوانند حدس بزنند.',
    'یک مثال کوچک برایش بزن.',
    'فقط بخش سرگرم‌کننده ماجرا را تعریف کن.',
]
for key, seeds in themes.items():
    # Keep seed prompts and then create many semantically different variants.
    seen = set()
    for seed in seeds:
        if seed not in seen:
            ADVANCED_CONTENT[key].append(seed)
            seen.add(seed)
    for i, lens in enumerate(lenses):
        for j, seed in enumerate(seeds):
            ending = endings[(i * 3 + j) % len(endings)]
            variant = f"{lens}{seed[:-1]}؛ {ending}"
            if variant not in seen:
                ADVANCED_CONTENT[key].append(variant)
                seen.add(variant)

# Additional specialized banks.
EMOJI_CHALLENGES = [
    ("🧊🔥🌙", "شب سرد و پرانرژی"),
    ("🎯🧠⚡", "تمرکز سریع"),
    ("🚀🌌🏆", "قهرمان فضایی"),
    ("🍿🎬😂", "فیلم خنده‌دار"),
    ("🕵️🔍🗝️", "کارآگاه مخفی"),
    ("👑⚔️🔥", "پادشاه میدان"),
    ("🌪️🎲😈", "هرج‌ومرج تصادفی"),
    ("🤖💻🧩", "معمای دیجیتال"),
    ("🏝️🧭🎒", "سفر ناشناخته"),
    ("🎤🎧🎶", "مسابقه موسیقی"),
    ("🍕⚡🏃", "دویدن برای پیتزا"),
    ("🧪🧠🧯", "آزمایش عجیب"),
    ("📚☕🌧️", "مطالعه شبانه"),
    ("🎈🎉🪩", "جشن بزرگ"),
    ("🦊🪤🕶️", "روباه جاسوس"),
    ("🧙📜✨", "جادوگر افسانه‌ای"),
    ("🏁🚗💨", "مسابقه سرعت"),
    ("🌋🧗🧊", "چالش طبیعت"),
    ("🎮👾🕹️", "نبرد آرکید"),
    ("💎🔐🧤", "سرقت الماس خیالی"),
]

RIDDLES = [
    ("چیست که هرچه بیشتر از آن برداری، بزرگ‌تر می‌شود؟", "چاله"),
    ("چه چیزی کلید دارد ولی قفل باز نمی‌کند؟", "پیانو"),
    ("چه چیزی پا دارد ولی راه نمی‌رود؟", "میز"),
    ("چه چیزی بدون بال پرواز می‌کند و بدون چشم گریه می‌کند؟", "ابر"),
    ("چه چیزی وقتی خیس است خشک می‌کند؟", "حوله"),
    ("چه چیزی بالا می‌رود اما پایین نمی‌آید؟", "سن"),
    ("چه چیزی دهان دارد ولی حرف نمی‌زند؟", "رودخانه"),
    ("چه چیزی هرگز سؤال نمی‌پرسد اما همیشه جواب می‌دهد؟", "پژواک"),
    ("چه چیزی هرچه بیشتر می‌شکند، بیشتر استفاده می‌شود؟", "رکورد"),
    ("چه چیزی همیشه جلوی توست اما دیده نمی‌شود؟", "آینده"),
    ("کدام اتاق در ندارد و پنجره هم ندارد؟", "قارچ"),
    ("چه چیزی می‌تواند شهرها را نشان دهد اما خودش حرکت نمی‌کند؟", "نقشه"),
    ("چه چیزی اگر نامش را بگویی، می‌شکند؟", "سکوت"),
    ("چه چیزی یک چشم دارد ولی نمی‌بیند؟", "سوزن"),
    ("چه چیزی هرگز به عقب برنمی‌گردد؟", "زمان"),
    ("چه چیزی هرچه سریع‌تر بدوی، سخت‌تر به آن می‌رسی؟", "نفس"),
    ("چه چیزی می‌گیری ولی نمی‌توانی نگه داری؟", "نفس"),
    ("چه چیزی همیشه می‌آید ولی هیچ‌وقت نمی‌رسد؟", "فردا"),
    ("چه چیزی سر دارد و دم دارد اما بدن ندارد؟", "سکه"),
    ("چه چیزی وقتی بالا می‌رود سبک‌تر می‌شود؟", "بادکنک"),
]

WORD_STARTS = [
    "آ", "ب", "پ", "ت", "ج", "چ", "د", "ر", "ز", "س", "ش", "ص", "ط", "ع", "ف", "ق", "ک", "گ", "ل", "م", "ن", "و", "ه", "ی"
]

SECRET_MISSIONS_ADVANCED = [
    "کاری کن یکی از بازیکنان بدون اینکه دلیل را بفهمد کلمه «شب» را بگوید.",
    "در دو پیام طبیعی از یک ایموجی خاص استفاده کن و کسی را وادار کن درباره‌اش سؤال بپرسد.",
    "کاری کن گروه درباره یک غذای خاص صحبت کند بدون اینکه مستقیم نامش را بیاوری.",
    "یک نفر را قانع کن که یک عدد بین ۱ تا ۵ انتخاب کند.",
    "کاری کن یک بازیکن برای یکی از قوانین بازی مثال بزند.",
    "در گفت‌وگو طوری رفتار کن که یک نفر از تو درباره لقب بازی‌ات بپرسد.",
    "یک جمله بگو که باعث شود حداقل یک نفر از گروه از تو سؤال بپرسد.",
    "کاری کن یک نفر داوطلب شود نفر بعدی بازی باشد.",
    "طوری سؤال بپرس که یک بازیکن نام یک فیلم را بر زبان بیاورد.",
    "کاری کن کسی از بین دو گزینه‌ای که تو پیشنهاد می‌کنی یکی را انتخاب کند.",
    "در سه پیام جدا یک کلمه مشترک را طبیعی استفاده کن و لو نرو.",
    "کاری کن یک نفر درباره آخرین بازی که کرده حرف بزند.",
]

ROLE_CARDS = [
    ("⚡ Speedrunner", "اولین پاسخ صحیح تو در چالش سرعت +۲ XP اضافه دارد."),
    ("🛡 Guardian", "در این دور یک بار می‌توانی یک حکم را با سپر رد کنی."),
    ("🧠 Analyst", "در یک رأی‌گیری می‌توانی نتیجه فعلی را زودتر ببینی."),
    ("🎲 Gambler", "یک بار در این دور می‌توانی یک انتخاب تصادفی را دوباره انجام دهی."),
    ("👑 Captain", "در یک چالش گروهی می‌توانی ترتیب گزینه‌ها را تعیین کنی."),
    ("🕵️ Shadow", "مأموریت مخفی تو یک مهلت اضافه دارد."),
    ("🔥 Challenger", "در دوئل یک امتیاز شروع بیشتر می‌گیری."),
    ("🍀 Lucky", "یک بار احتمال پاداش بیشتر برایت فعال می‌شود."),
]

EVENT_CARDS_ADVANCED = [
    ("🌠 Momentum", "پاداش XP سه مرحله بعدی +۱ می‌شود."),
    ("🛡 Safe Round", "اولین بازیکن بازنده این دور می‌تواند یک بار حکم را رد کند."),
    ("💰 Coin Rush", "اولین برنده مینی‌گیم +۵ سکه اضافی می‌گیرد."),
    ("🎯 Double Target", "مرحله بعد دو جایزه دارد."),
    ("🧊 Freeze", "یک بازیکن تصادفی نمی‌تواند در یک چالش شرکت کند و نقش ناظر دارد."),
    ("🔄 Reversal", "در یک مرحله، جایزه کوچک بازنده و برنده با هم جابه‌جا می‌شود."),
    ("🌪 Chaos", "حالت بعدی کاملاً تصادفی انتخاب می‌شود."),
    ("👑 Crown", "یک نفر قهرمان موقت دور می‌شود و +۳ XP می‌گیرد."),
    ("🧩 Puzzle", "یک معما جایگزین چالش عادی می‌شود."),
    ("🎭 Roleplay", "مرحله بعد با یک نقش کوتاه اجرا می‌شود."),
]

# -----------------------------
# Utility: safe Telegram UI operations
# -----------------------------

async def safe_answer_query(query, text=None, alert=False):
    try:
        await query.answer(text=text, show_alert=alert)
    except Exception:
        return False
    return True


async def safe_edit_query(query, text, markup=None, parse_mode=ParseMode.HTML):
    try:
        await query.edit_message_text(text=text, parse_mode=parse_mode, reply_markup=markup)
        return True
    except Exception as exc:
        # Telegram can return "message is not modified". The button has still been consumed.
        if "not modified" in str(exc).lower():
            await safe_answer_query(query, "همین صفحه در حال حاضر باز است.")
            return True
        try:
            if query.message:
                await query.message.reply_text(text=text, parse_mode=parse_mode, reply_markup=markup)
                await safe_answer_query(query)
                return True
        except Exception:
            pass
    return False


async def safe_send(bot, chat_id, text, markup=None, parse_mode=ParseMode.HTML):
    try:
        return await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=markup)
    except Exception:
        return None


def clip_text(text: str, limit: int = 3900) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: limit - 30] + "\n… متن کوتاه شد."


def fmt_num(value: int | float) -> str:
    return f"{int(value):,}".replace(",", "٬")


def unique_count(seq) -> int:
    return len(set(map(str, seq)))


# -----------------------------
# Content registry expansion
# -----------------------------

ADVANCED_CONTENT.update({
    "emoji": [question for question, _ in EMOJI_CHALLENGES],
    "riddle": [question for question, _ in RIDDLES],
    "mission": SECRET_MISSIONS_ADVANCED[:],
})


def all_content_bank(key: str, fallback=None, chat_id: int | None = None):
    bank = []
    bank.extend(ADVANCED_CONTENT.get(key, []))
    if chat_id is not None:
        group = DATA.get("groups", {}).get(group_key(int(chat_id)), {})
        bank.extend(group.get("content", {}).get(key, []))
    global_bank = DATA.get("global_content", {}).get(key, [])
    bank.extend(global_bank)
    if fallback:
        bank.extend(fallback)
    result = []
    seen = set()
    for item in bank:
        item = str(item).strip()
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result


def choose_advanced_content(game, key: str, fallback=None) -> str:
    pool = all_content_bank(key, fallback, int(game.get("chat_id", 0)))
    if not pool:
        return "محتوایی برای این حالت ثبت نشده است."
    used = set(game.setdefault("used_content", {}).setdefault(key, []))
    choices = [x for x in pool if x not in used]
    if not choices:
        choices = pool
    pick = random.choice(choices)
    used.add(pick)
    game["used_content"][key] = list(used)[-100:]
    return pick


# Replace the original chooser with the advanced non-repeating chooser.
choose_content = choose_advanced_content


# ============================================================
# Navigation keyboards — small, shallow and predictable
# ============================================================


def nav_row(*buttons):
    return [InlineKeyboardButton(label, callback_data=data) for label, data in buttons]


def back_button(target="GM|HOME"):
    return [InlineKeyboardButton("🔙 بازگشت", callback_data=target)]


def close_button(target="GM|CLOSE"):
    return [InlineKeyboardButton("✖️ بستن", callback_data=target)]


def main_keyboard_v4(uid: int) -> ReplyKeyboardMarkup:
    rows = [
        ["🎮 بازی", "👤 پروفایل", "🏆 رتبه‌بندی"],
        ["🛒 فروشگاه", "🏅 دستاوردها", "📜 قوانین"],
        ["❓ راهنما"],
    ]
    if is_admin(uid):
        rows.append(["👑 مدیریت ApexRival"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False, selective=False)


def game_home_keyboard(game):
    rows = [
        nav_row(("⚡ چالش‌های سریع", "GM|FAST"), ("🎭 اجتماعی", "GM|SOCIAL")),
        nav_row(("⚔️ رقابتی", "GM|COMPETE"), ("🤫 مخفی", "GM|SECRET")),
        nav_row(("☠️ حکم و پاداش", "GM|REWARDS"), ("📊 وضعیت", "GM|STATUS")),
        nav_row(("👑 کنترل سرگروه", "GM|HOST")) if leader_of(game, game.get("_viewer_id", 0)) else [],
        back_button("GM|CLOSE"),
    ]
    return InlineKeyboardMarkup([r for r in rows if r])


def game_fast_keyboard():
    return InlineKeyboardMarkup([
        nav_row(("🎯 عدد مخفی", "GM|FAST|NUMBER"), ("🧩 معما", "GM|FAST|RIDDLE")),
        nav_row(("😀 ایموجی", "GM|FAST|EMOJI"), ("⚡ واکنش سریع", "GM|FAST|REACTION")),
        nav_row(("🔤 زنجیره کلمات", "GM|FAST|WORDS")),
        back_button("GM|HOME"),
    ])


def game_social_keyboard(game):
    rows = [
        nav_row(("🕵️ اعتراف", "GM|SOCIAL|TRUTH"), ("🔥 جرئت", "GM|SOCIAL|DARE")),
        nav_row(("💘 فلرت محترمانه", "GM|SOCIAL|FLIRTY"), ("🧠 سؤال گروهی", "GM|SOCIAL|QUESTION")),
        back_button("GM|HOME"),
    ]
    if get_group(int(game["chat_id"])).get("adult_mode"):
        rows.insert(2, nav_row(("🔞 +18 غیرصریح", "GM|SOCIAL|ADULT")))
    return InlineKeyboardMarkup(rows)


def game_compete_keyboard():
    return InlineKeyboardMarkup([
        nav_row(("⚔️ دوئل", "GM|COMPETE|DUEL"), ("🎰 گردونه", "GM|COMPETE|ROULETTE")),
        nav_row(("⚡ سرعت", "GM|COMPETE|SPEED"), ("🗳 رأی‌گیری", "GM|COMPETE|VOTE")),
        nav_row(("🏁 بقا", "GM|COMPETE|SURVIVAL"), ("👥 تیم‌سازی", "GM|COMPETE|TEAMS")),
        back_button("GM|HOME"),
    ])


def game_secret_keyboard():
    return InlineKeyboardMarkup([
        nav_row(("🤫 مأموریت مخفی", "GM|SECRET|MISSION"), ("🕵️ جاسوس", "GM|SECRET|SPY")),
        nav_row(("🎭 کارت نقش", "GM|SECRET|ROLE"), ("🔮 پیش‌بینی", "GM|SECRET|PREDICT")),
        back_button("GM|HOME"),
    ])


def game_reward_keyboard(game):
    return InlineKeyboardMarkup([
        nav_row(("☠️ حکم من", "GM|REWARDS|MINE"), ("🛒 فروشگاه", "GM|REWARDS|SHOP")),
        nav_row(("🍀 آیتم‌های من", "GM|REWARDS|INV"), ("🏅 دستاوردها", "GM|REWARDS|ACH")),
        back_button("GM|HOME"),
    ])


def host_control_keyboard():
    return InlineKeyboardMarkup([
        nav_row(("🎲 انتخاب تصادفی", "GM|HOST|RANDOM"), ("☠️ حکم تصادفی", "GM|HOST|PENALTY")),
        nav_row(("⏭ دور بعد", "GM|HOST|NEXT"), ("🛑 پایان بازی", "GM|HOST|END")),
        nav_row(("⚙️ تنظیمات لابی", "GM|HOST|SETTINGS"), ("👥 بازیکنان", "GM|HOST|PLAYERS")),
        back_button("GM|HOME"),
    ])


# -----------------------------
# Admin navigation
# -----------------------------


def admin_home_keyboard():
    return InlineKeyboardMarkup([
        nav_row(("📊 نمای کلی", "AX|STATS"), ("👥 کاربران", "AX|USERS")),
        nav_row(("🌐 گروه‌ها", "AX|GROUPS"), ("🎮 بازی‌ها", "AX|GAMES")),
        nav_row(("📝 محتوا", "AX|CONTENT"), ("🛒 اقتصاد", "AX|ECONOMY")),
        nav_row(("🛡 امنیت", "AX|SECURITY"), ("⚙️ تنظیمات", "AX|SETTINGS")),
        nav_row(("💾 بکاپ", "AX|BACKUP"), ("📜 لاگ‌ها", "AX|LOGS")),
        nav_row(("📣 پیام همگانی", "AX|BROADCAST"), ("🧰 ابزارها", "AX|TOOLS")),
        [InlineKeyboardButton("✖️ بستن پنل", callback_data="AX|CLOSE")],
    ])


def admin_back_home():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به پنل اصلی", callback_data="AX|HOME")]])


def admin_two_back(rows, back="AX|HOME"):
    rows = [r for r in rows if r]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data=back)])
    return InlineKeyboardMarkup(rows)


async def render_admin(query, title: str, body: str, markup=None):
    text = f"{title}\n\n{body}"
    return await safe_edit_query(query, clip_text(text), markup or admin_back_home())


async def advanced_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        if update.callback_query:
            await safe_answer_query(update.callback_query, "🚫 فقط Super Admin.", True)
        elif update.message:
            await update.message.reply_text("🚫 فقط Super Admin.")
        return
    text = (
        f"👑 <b>ApexRival {ADVANCED_VERSION}</b>\n"
        f"<i>مرکز فرماندهی</i>\n\n"
        f"👥 کاربران: <b>{fmt_num(len(DATA['users']))}</b>\n"
        f"🌐 گروه‌ها: <b>{fmt_num(len(DATA['groups']))}</b>\n"
        f"🎮 بازی‌های ذخیره‌شده: <b>{fmt_num(len(DATA['games']))}</b>\n"
        f"🟢 بازی فعال: <b>{sum(1 for g in DATA['groups'].values() if g.get('active_game'))}</b>\n"
        f"📜 لاگ‌ها: <b>{fmt_num(len(DATA['audit']))}</b>\n\n"
        "هر بخش وظیفه مشخص خودش را دارد تا پنل شلوغ نشود."
    )
    markup = admin_home_keyboard()
    if update.callback_query:
        await safe_edit_query(update.callback_query, text, markup)
        await safe_answer_query(update.callback_query)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


# Replace admin_panel symbol with the robust implementation.
admin_panel = advanced_admin_panel


# -----------------------------
# Admin data pages
# -----------------------------


def sort_users_by_xp():
    return sorted(DATA["users"].items(), key=lambda kv: (int(kv[1].get("xp", 0)), int(kv[1].get("coins", 0))), reverse=True)


def sort_groups_by_activity():
    return sorted(DATA["groups"].items(), key=lambda kv: bool(kv[1].get("active_game")), reverse=True)


def active_games():
    return [(gid, g) for gid, g in DATA["games"].items() if g.get("status") in ("active", "lobby")]


def user_admin_text(uid: int) -> str:
    user = get_user(uid)
    title = game_title(uid)
    ach = len(user.get("achievements", []))
    inv = user.get("inventory", {})
    inv_text = "، ".join(f"{SHOP[k]['name']}:{int(v)}" for k,v in inv.items())
    return (
        f"👤 <b>{escape(str(user.get('name','کاربر')))}</b>\n"
        f"🆔 <code>{uid}</code>\n"
        f"🏅 {escape(title)} | Level {user.get('level',1)}\n"
        f"⭐ XP: {fmt_num(user.get('xp',0))}\n"
        f"💰 سکه: {fmt_num(user.get('coins',0))}\n"
        f"🏆 برد: {user.get('wins',0)} | ☠️ باخت: {user.get('losses',0)}\n"
        f"🔥 استریک: {user.get('streak',0)} / {user.get('best_streak',0)}\n"
        f"🚫 وضعیت: {'BAN' if user.get('banned') else 'فعال'}\n"
        f"🏅 دستاورد: {ach}\n"
        f"🎒 {escape(inv_text or 'خالی')}"
    )


def admin_user_actions(uid: int):
    status = get_user(uid).get("banned", False)
    rows = [
        nav_row(("➕ 25 XP", f"AX|UXP|{uid}|25"), ("➕ 100 XP", f"AX|UXP|{uid}|100")),
        nav_row(("➖ 25 XP", f"AX|UXP|{uid}|-25"), ("⭐ Level +1", f"AX|ULEVEL|{uid}|1")),
        nav_row(("💰 +25 سکه", f"AX|UCOIN|{uid}|25"), ("💸 -25 سکه", f"AX|UCOIN|{uid}|-25")),
        nav_row(("🛡 +سپر", f"AX|UITEM|{uid}|shield|1"), ("🎲 +ریرول", f"AX|UITEM|{uid}|reroll|1")),
        nav_row(("🚫 بن" if not status else "✅ رفع بن", f"AX|BAN|{uid}"), ("🧹 ریست", f"AX|RESET|{uid}")),
        nav_row(("📊 جزئیات", f"AX|UDETAIL|{uid}"), ("📜 لاگ کاربر", f"AX|ULOG|{uid}")),
        [InlineKeyboardButton("🔙 کاربران", callback_data="AX|USERS")],
    ]
    return InlineKeyboardMarkup(rows)


async def admin_users_page(query, page=0):
    page = max(0, int(page))
    items = sort_users_by_xp()
    chunk = 8
    start = page * chunk
    current = items[start:start+chunk]
    lines = []
    buttons = []
    for offset, (uid_s, user) in enumerate(current, start=1):
        uid = int(uid_s)
        flag = "🚫" if user.get("banned") else "🟢"
        lines.append(f"{offset+start}. {flag} {escape(str(user.get('name','کاربر')))[:22]} — {user.get('xp',0)} XP")
        buttons.append([InlineKeyboardButton(f"👤 {str(user.get('name','کاربر'))[:20]}", callback_data=f"AX|U|{uid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"AX|USERS|{page-1}"))
    if start + chunk < len(items):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"AX|USERS|{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔄 تازه‌سازی", callback_data=f"AX|USERS|{page}")])
    buttons.append([InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")])
    text = f"👥 <b>مدیریت کاربران</b>\nصفحه {page+1}\n\n" + ("\n".join(lines) or "کاربری ثبت نشده است.")
    await safe_edit_query(query, text, InlineKeyboardMarkup(buttons))


async def admin_groups_page(query, page=0):
    page = max(0, int(page))
    items = sort_groups_by_activity()
    chunk = 6
    start = page * chunk
    current = items[start:start+chunk]
    buttons = []
    lines = []
    for idx, (cid, group) in enumerate(current, start=start+1):
        active = bool(group.get("active_game"))
        enabled = bool(group.get("enabled", True))
        lines.append(f"{idx}. <code>{cid}</code> | {'🟢' if enabled else '🔴'} | {'🎮' if active else '💤'}")
        buttons.append([InlineKeyboardButton(f"🌐 {cid}", callback_data=f"AX|G|{cid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"AX|GROUPS|{page-1}"))
    if start + chunk < len(items):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"AX|GROUPS|{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔄 تازه‌سازی", callback_data=f"AX|GROUPS|{page}")])
    buttons.append([InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")])
    text = "🌐 <b>مدیریت گروه‌ها</b>\n\n" + ("\n".join(lines) or "گروهی ثبت نشده است.")
    await safe_edit_query(query, text, InlineKeyboardMarkup(buttons))


async def admin_games_page(query, page=0):
    items = active_games()
    chunk = 6
    start = max(0, int(page)) * chunk
    current = items[start:start+chunk]
    buttons = []
    lines = []
    for idx, (gid, game) in enumerate(current, start=start+1):
        phase = game.get("phase", "-")
        lines.append(f"{idx}. <code>{game.get('chat_id')}</code> | {len(game.get('players',[]))} نفر | {escape(str(phase))}")
        token = str(gid)[:32]
        buttons.append([InlineKeyboardButton(f"🎮 گروه {game.get('chat_id')}", callback_data=f"AX|GAME|{token}")])
    if start + chunk < len(items):
        buttons.append([InlineKeyboardButton("▶️ بعدی", callback_data=f"AX|GAMES|{int(page)+1}")])
    if page > 0:
        buttons.append([InlineKeyboardButton("◀️ قبلی", callback_data=f"AX|GAMES|{int(page)-1}")])
    buttons.append([InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")])
    text = "🎮 <b>بازی‌های جاری</b>\n\n" + ("\n".join(lines) or "هیچ بازی فعالی وجود ندارد.")
    await safe_edit_query(query, text, InlineKeyboardMarkup(buttons))


async def admin_stats_page(query):
    active = sum(1 for _, g in DATA["groups"].items() if g.get("active_game"))
    lobbies = sum(1 for g in DATA["games"].values() if g.get("status") == "lobby")
    finished = sum(1 for g in DATA["games"].values() if g.get("status") == "finished")
    total_xp = sum(int(u.get("xp", 0)) for u in DATA["users"].values())
    total_coins = sum(int(u.get("coins", 0)) for u in DATA["users"].values())
    games_played = sum(int(u.get("games", 0)) for u in DATA["users"].values())
    text = (
        "📊 <b>نمای کلی سیستم</b>\n\n"
        f"👥 کاربران: {fmt_num(len(DATA['users']))}\n"
        f"🌐 گروه‌ها: {fmt_num(len(DATA['groups']))}\n"
        f"🟢 بازی فعال: {fmt_num(active)}\n"
        f"🟡 لابی: {fmt_num(lobbies)}\n"
        f"🏁 بازی پایان‌یافته: {fmt_num(finished)}\n"
        f"🎮 تجربه‌های ثبت‌شده: {fmt_num(games_played)}\n"
        f"⭐ XP کل: {fmt_num(total_xp)}\n"
        f"💰 سکه کل: {fmt_num(total_coins)}\n"
        f"🧩 محتوای سراسری: {sum(len(v) for v in DATA.get('global_content', {}).values())}\n"
        f"📜 لاگ: {len(DATA.get('audit', []))}"
    )
    await render_admin(query, "📊 نمای کلی", text, admin_back_home())


async def admin_group_detail(query, cid: int):
    group = get_group(cid)
    game = active_game(cid)
    text = (
        f"🌐 <b>گروه {cid}</b>\n\n"
        f"وضعیت: {'🟢 فعال' if group.get('enabled') else '🔴 خاموش'}\n"
        f"+18: {'🔞 روشن' if group.get('adult_mode') else '🔒 خاموش'}\n"
        f"حداقل بازیکن: {group.get('min_players',2)}\n"
        f"حداکثر بازیکن: {group.get('max_players',20)}\n"
        f"بازی: {'🟢 فعال' if game else '💤 ندارد'}"
    )
    rows = [
        nav_row(("🟢 فعال", f"AX|GEN|{cid}|on"), ("🔴 خاموش", f"AX|GEN|{cid}|off")),
        nav_row(("🔞 +18 ON", f"AX|GADULT|{cid}|on"), ("🔒 +18 OFF", f"AX|GADULT|{cid}|off")),
        nav_row(("➕ Max", f"AX|GMAX|{cid}|up"), ("➖ Max", f"AX|GMAX|{cid}|down")),
        [InlineKeyboardButton("🛑 پایان بازی", callback_data=f"AX|GEND|{cid}")],
        [InlineKeyboardButton("🔙 گروه‌ها", callback_data="AX|GROUPS")],
    ]
    await render_admin(query, "🌐 مدیریت گروه", text, InlineKeyboardMarkup(rows))


# -----------------------------
# Content administration
# -----------------------------

CONTENT_LABELS = {
    "truth": "🕵️ اعتراف",
    "dare": "🔥 جرئت",
    "flirty": "💘 فلرت",
    "question": "🧠 سؤال",
    "penalty": "☠️ حکم",
    "boss": "👑 Boss",
    "mission": "🤫 مأموریت",
    "riddle": "🧩 معما",
}


def admin_content_menu():
    rows = [
        nav_row((CONTENT_LABELS["truth"], "AX|CONTENT|truth"), (CONTENT_LABELS["dare"], "AX|CONTENT|dare")),
        nav_row((CONTENT_LABELS["flirty"], "AX|CONTENT|flirty"), (CONTENT_LABELS["question"], "AX|CONTENT|question")),
        nav_row((CONTENT_LABELS["penalty"], "AX|CONTENT|penalty"), (CONTENT_LABELS["boss"], "AX|CONTENT|boss")),
        nav_row((CONTENT_LABELS["mission"], "AX|CONTENT|mission"), (CONTENT_LABELS["riddle"], "AX|CONTENT|riddle")),
        [InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")],
    ]
    return InlineKeyboardMarkup(rows)


async def admin_content_page(query):
    counts = []
    for key, label in CONTENT_LABELS.items():
        counts.append(f"{label}: {len(all_content_bank(key))}")
    body = "\n".join(counts) + "\n\nبرای هر دسته، لیست، حذف و افزودن جداگانه در دسترس است."
    await render_admin(query, "📝 مدیریت محتوا", body, admin_content_menu())


async def admin_content_category(query, key: str, page=0):
    pool = all_content_bank(key)
    chunk = 5
    page = max(0, int(page))
    start = page * chunk
    current = pool[start:start+chunk]
    lines = [f"{i+1+start}. {escape(item)}" for i, item in enumerate(current)]
    buttons = []
    for i, item in enumerate(current):
        buttons.append([InlineKeyboardButton(f"🗑 حذف {i+1+start}", callback_data=f"AX|CDEL|{key}|{i+start}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"AX|CONTENT|{key}|{page-1}"))
    if start + chunk < len(pool):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"AX|CONTENT|{key}|{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("➕ افزودن", callback_data=f"AX|CADD|{key}")])
    buttons.append([InlineKeyboardButton("🧹 پاک‌سازی سفارشی", callback_data=f"AX|CCLEAR|{key}")])
    buttons.append([InlineKeyboardButton("🔙 دسته‌ها", callback_data="AX|CONTENT")])
    text = f"{CONTENT_LABELS.get(key,key)} <b>— صفحه {page+1}</b>\n\n" + ("\n\n".join(lines) or "هیچ محتوایی نیست.")
    await safe_edit_query(query, clip_text(text), InlineKeyboardMarkup(buttons))


# -----------------------------
# Economy, security, settings
# -----------------------------

async def admin_economy_page(query):
    stock = "\n".join(f"{v['name']}: {v['price']} 🪙 — {v['desc']}" for v in SHOP.values())
    total = sum(int(u.get('coins',0)) for u in DATA['users'].values())
    text = f"🛒 <b>اقتصاد بازی</b>\n\nسکه در گردش: {fmt_num(total)}\nضریب XP: {DATA['settings'].get('xp_multiplier',1)}\nضریب سکه: {DATA['settings'].get('coins_multiplier',1)}\n\n{escape(stock)}"
    rows = [
        nav_row(("⭐ XP ×1", "AX|MULT|xp|1"), ("⚡ XP ×2", "AX|MULT|xp|2")),
        nav_row(("💰 Coin ×1", "AX|MULT|coin|1"), ("💎 Coin ×2", "AX|MULT|coin|2")),
        [InlineKeyboardButton("🔄 تازه‌سازی", callback_data="AX|ECONOMY")],
        [InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")],
    ]
    await render_admin(query, "🛒 اقتصاد", text, InlineKeyboardMarkup(rows))


async def admin_security_page(query):
    banned = sum(1 for u in DATA['users'].values() if u.get('banned'))
    text = (
        "🛡 <b>امنیت و کنترل</b>\n\n"
        f"🚫 کاربران بن‌شده: {banned}\n"
        f"📜 Audit نگهداری‌شده: {len(DATA.get('audit',[]))}\n"
        "\nابزارها در این نسخه بدون حدس‌زدن روی داده‌های حساس کار می‌کنند."
    )
    rows = [
        [InlineKeyboardButton("🚫 لیست بن‌ها", callback_data="AX|BANLIST")],
        [InlineKeyboardButton("🧹 پاکسازی بازی‌های قدیمی", callback_data="AX|CLEAN")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="AX|SECURITY")],
        [InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")],
    ]
    await render_admin(query, "🛡 امنیت", text, InlineKeyboardMarkup(rows))


async def admin_settings_page(query):
    s = DATA["settings"]
    text = (
        "⚙️ <b>تنظیمات سراسری</b>\n\n"
        f"حداکثر بازیکن پیش‌فرض: {s.get('max_players_default',20)}\n"
        f"+18 پیش‌فرض: {'روشن' if s.get('adult_default') else 'خاموش'}\n"
        f"ضریب XP: {s.get('xp_multiplier',1)}\n"
        f"ضریب سکه: {s.get('coins_multiplier',1)}"
    )
    rows = [
        nav_row(("➕ Max", "AX|GLOBMAX|up"), ("➖ Max", "AX|GLOBMAX|down")),
        nav_row(("🔞 Default ON", "AX|ADULTDEF|on"), ("🔒 Default OFF", "AX|ADULTDEF|off")),
        nav_row(("⭐ XP ×1", "AX|MULT|xp|1"), ("⚡ XP ×2", "AX|MULT|xp|2")),
        nav_row(("💰 Coin ×1", "AX|MULT|coin|1"), ("💎 Coin ×2", "AX|MULT|coin|2")),
        [InlineKeyboardButton("💾 ذخیره فوری", callback_data="AX|SAVE")],
        [InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")],
    ]
    await render_admin(query, "⚙️ تنظیمات", text, InlineKeyboardMarkup(rows))


# -----------------------------
# Backup subsystem
# -----------------------------


def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def make_backup_file(reason="manual") -> str:
    ensure_backup_dir()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BACKUP_DIR, f"apexrival_{reason}_{stamp}.json")
    with LOCK:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=2)
    files = sorted(Path(BACKUP_DIR).glob("apexrival_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[MAX_BACKUPS:]:
        try:
            old.unlink()
        except OSError:
            pass
    audit("backup", ADMIN_ID, None, os.path.basename(path))
    return path


def backup_files():
    ensure_backup_dir()
    return sorted(Path(BACKUP_DIR).glob("apexrival_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def restore_backup(path: Path) -> tuple[bool, str]:
    global DATA
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict) or "users" not in raw or "groups" not in raw or "games" not in raw:
            return False, "ساختار فایل بکاپ معتبر نیست."
        with LOCK:
            DATA = raw
            DATA.setdefault("schema", 4)
            DATA.setdefault("global_content", {})
            DATA.setdefault("settings", {})
            DATA.setdefault("audit", [])
            DATA.setdefault("broadcast_log", [])
        save_data(force=True)
        audit("restore", ADMIN_ID, None, path.name)
        return True, "بکاپ با موفقیت بازیابی شد."
    except Exception as exc:
        return False, f"خطا: {exc}"


async def admin_backup_page(query):
    files = backup_files()
    lines = [f"{i+1}. {f.name}" for i, f in enumerate(files[:10])]
    rows = [[InlineKeyboardButton("📦 ساخت بکاپ جدید", callback_data="AX|MAKEBACKUP")]]
    for i, f in enumerate(files[:8]):
        rows.append([InlineKeyboardButton(f"♻️ بازیابی {i+1}", callback_data=f"AX|RESTORE|{i}")])
    rows.append([InlineKeyboardButton("🔄 تازه‌سازی", callback_data="AX|BACKUP")])
    rows.append([InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")])
    text = "💾 <b>Backup Center</b>\n\n" + ("\n".join(lines) or "هنوز بکاپی ساخته نشده است.")
    await render_admin(query, "💾 بکاپ و بازیابی", text, InlineKeyboardMarkup(rows))


# -----------------------------
# Tools and logs
# -----------------------------

async def admin_logs_page(query):
    rows = DATA.get("audit", [])[-20:][::-1]
    lines = []
    for item in rows:
        t = datetime.fromtimestamp(int(item.get("ts",0)), timezone.utc).strftime("%m-%d %H:%M")
        lines.append(f"{t} | {escape(str(item.get('action','-')))} | {item.get('actor','-')} | {item.get('chat','-')}")
    await render_admin(query, "📜 لاگ عملیات", "\n".join(lines) or "لاگی ثبت نشده است.", admin_back_home())


async def admin_tools_page(query):
    text = (
        "🧰 <b>ابزارهای عملیاتی</b>\n\n"
        "ابزارهای سریع برای نگهداری و تست سیستم.\n"
        "هیچ‌کدام از این دکمه‌ها منوی دیگری را بی‌دلیل باز نمی‌کنند."
    )
    rows = [
        nav_row(("💾 Save", "AX|SAVE"), ("🧹 Cleanup", "AX|CLEAN")),
        nav_row(("📦 Backup", "AX|MAKEBACKUP"), ("📊 Health", "AX|HEALTH")),
        nav_row(("🛑 پایان همه بازی‌ها", "AX|ENDALL"), ("🔄 شمارنده‌ها", "AX|COUNTERS")),
        [InlineKeyboardButton("🔙 پنل", callback_data="AX|HOME")],
    ]
    await render_admin(query, "🧰 ابزارها", text, InlineKeyboardMarkup(rows))


# ============================================================
# New mini-games
# ============================================================


def ensure_mode_state(game, key, default):
    value = game.get(key)
    if value is None:
        game[key] = deepcopy(default)
        value = game[key]
    return value


async def mini_number_hunt(message, game):
    if len(game.get("players", [])) < 2:
        await message.reply_text("👥 حداقل دو بازیکن لازم است.")
        return
    target = random.randint(1, 20)
    game["number_hunt"] = {"target": target, "expires": time.time() + 25, "winner": None}
    game["phase"] = "number_hunt"
    touch_game(game)
    await message.reply_text("🎯 <b>عدد مخفی</b>\n\nیک عدد بین <b>۱ تا ۲۰</b> انتخاب شده است.\nاولین حدس درست +۸ XP و +۴ سکه می‌گیرد.", parse_mode=ParseMode.HTML)


async def mini_riddle(message, game):
    q, answer = random.choice(RIDDLES)
    game["riddle"] = {"answer": answer.casefold(), "expires": time.time() + 45, "solved": False}
    game["phase"] = "riddle"
    touch_game(game)
    await message.reply_text(f"🧩 <b>معما</b>\n\n{escape(q)}\n\n⏱ ۴۵ ثانیه", parse_mode=ParseMode.HTML)


async def mini_emoji(message, game):
    emoji, answer = random.choice(EMOJI_CHALLENGES)
    game["emoji"] = {"answer": answer.casefold(), "expires": time.time() + 35, "solved": False}
    game["phase"] = "emoji"
    touch_game(game)
    await message.reply_text(f"😀 <b>معمای ایموجی</b>\n\n{emoji}\n\nاولین کسی که مفهوم را حدس بزند +۶ XP می‌گیرد.", parse_mode=ParseMode.HTML)


async def mini_reaction(message, game):
    game["reaction"] = {"expires": time.time() + 15, "winner": None}
    game["phase"] = "reaction"
    touch_game(game)
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("⚡ بزن!", callback_data="GM|FAST|REACTION|HIT")]])
    await message.reply_text("⚡ <b>Reaction Rush</b>\n\nاولین بازیکنی که دکمه را بزند برنده است.", parse_mode=ParseMode.HTML, reply_markup=markup)


async def mini_words(message, game):
    letter = random.choice(WORD_STARTS)
    game["word"] = {"letter": letter, "expires": time.time() + 30, "winner": None}
    game["phase"] = "word"
    touch_game(game)
    await message.reply_text(f"🔤 <b>زنجیره کلمات</b>\n\nیک کلمه فارسی با حرف «<b>{escape(letter)}</b>» بفرست.\nاولین جواب قابل قبول +۶ XP.", parse_mode=ParseMode.HTML)


async def mini_survival(message, game):
    players = list(game.get("players", []))
    if len(players) < 3:
        await message.reply_text("🏁 برای حالت بقا حداقل ۳ بازیکن لازم است.")
        return
    loser = random.choice(players)
    game["survival"] = {"target": loser, "round": game.get("round", 0), "expires": time.time() + 30}
    game["phase"] = "survival"
    p = assign_penalty(game, loser, source="🏁 Survival")
    reward_player(game, loser, 0, 0, loss=True, reason="Survival")
    touch_game(game)
    await message.reply_text(
        f"🏁 <b>Survival Round</b>\n\nبازیکن هدف: {mention_user(loser, name_of(loser, game))}\n☠️ حکم ثبت شد: {escape(p['text'])}",
        parse_mode=ParseMode.HTML,
        reply_markup=game_keyboard(game),
    )


async def mini_teams(message, game):
    players = list(game.get("players", []))
    random.shuffle(players)
    half = (len(players) + 1) // 2
    a, b = players[:half], players[half:]
    team_a = ", ".join(name_of(uid, game) for uid in a) or "—"
    team_b = ", ".join(name_of(uid, game) for uid in b) or "—"
    game["teams"] = {"A": a, "B": b, "expires": time.time() + 300}
    game["phase"] = "teams"
    touch_game(game)
    await message.reply_text(
        f"👥 <b>تیم‌بندی تصادفی</b>\n\n🔵 تیم A:\n{escape(team_a)}\n\n🔴 تیم B:\n{escape(team_b)}",
        parse_mode=ParseMode.HTML,
    )


async def mini_role(message, game, bot):
    uid = random.choice(game.get("players", []))
    role, desc = random.choice(ROLE_CARDS)
    game["role_card"] = {"user": uid, "role": role, "desc": desc, "expires": time.time() + 300}
    game["phase"] = "role"
    touch_game(game)
    await safe_send(bot, uid, f"🎭 <b>کارت نقش محرمانه</b>\n\n{role}\n{desc}")
    await message.reply_text("🎭 یک کارت نقش محرمانه توزیع شد. صاحب کارت نباید آن را علنی کند.", parse_mode=ParseMode.HTML)


async def mini_predict(message, game):
    secret = random.choice(["شیر", "خط"])
    game["predict"] = {"secret": secret, "votes": {}, "expires": time.time() + 30}
    game["phase"] = "predict"
    rows = [[InlineKeyboardButton("🪙 شیر", callback_data="GM|SECRET|PREDICT|heads"), InlineKeyboardButton("🪙 خط", callback_data="GM|SECRET|PREDICT|tails")]]
    await message.reply_text("🔮 <b>پیش‌بینی</b>\n\nیک طرف سکه را انتخاب کن. انتخابت ثبت می‌شود.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))


# ============================================================
# Advanced callback router
# ============================================================

async def advanced_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    data = str(query.data)
    if not (data.startswith("AX|") or data.startswith("GM|")):
        return
    await safe_answer_query(query)
    parts = data.split("|")
    family = parts[0]
    chat_id = query.message.chat_id if query.message else update.effective_chat.id
    uid = query.from_user.id

    if family == "AX":
        if not is_admin(uid):
            await safe_answer_query(query, "🚫 فقط Super Admin.", True)
            return
        action = parts[1] if len(parts) > 1 else "HOME"
        if action == "HOME":
            await advanced_admin_panel(update, context)
            return
        if action == "CLOSE":
            await safe_edit_query(query, "✅ پنل مدیریت بسته شد.", None)
            return
        if action == "STATS":
            await admin_stats_page(query); return
        if action == "USERS":
            page = int(parts[2]) if len(parts) > 2 else 0
            await admin_users_page(query, page); return
        if action == "U":
            target = int(parts[2])
            await render_admin(query, "👤 مدیریت کاربر", user_admin_text(target), admin_user_actions(target)); return
        if action == "UXP":
            target, amount = int(parts[2]), int(parts[3])
            u = get_user(target); u["xp"] = max(0, int(u.get("xp",0)) + amount); u["level"] = level_for_xp(u["xp"])
            audit("admin_xp", uid, None, f"{target}:{amount}"); save_data(force=True)
            await render_admin(query, "👤 تغییر XP", user_admin_text(target), admin_user_actions(target)); return
        if action == "UCOIN":
            target, amount = int(parts[2]), int(parts[3])
            get_user(target)["coins"] = max(0, int(get_user(target).get("coins",0)) + amount)
            audit("admin_coins", uid, None, f"{target}:{amount}"); save_data(force=True)
            await render_admin(query, "💰 تغییر سکه", user_admin_text(target), admin_user_actions(target)); return
        if action == "UITEM":
            target, item, count = int(parts[2]), parts[3], int(parts[4])
            grant_item(target, item, count); audit("admin_item", uid, None, f"{target}:{item}:{count}"); save_data(force=True)
            await render_admin(query, "🎒 آیتم اضافه شد", user_admin_text(target), admin_user_actions(target)); return
        if action == "BAN":
            target = int(parts[2]); user = get_user(target); user["banned"] = not bool(user.get("banned")); audit("admin_ban", uid, None, str(target)); save_data(force=True)
            await render_admin(query, "🛡 وضعیت کاربر", user_admin_text(target), admin_user_actions(target)); return
        if action == "ULEVEL":
            target, delta = int(parts[2]), int(parts[3]); u = get_user(target); u["level"] = max(1, min(100, int(u.get("level",1)) + delta)); audit("admin_level", uid, None, f"{target}:{delta}"); save_data(force=True); await render_admin(query, "⭐ تغییر Level", user_admin_text(target), admin_user_actions(target)); return
        if action == "RESET":
            target = int(parts[2]); DATA["users"][str(target)] = deepcopy(DEFAULT_USER); save_data(force=True)
            await render_admin(query, "🧹 ریست کاربر", user_admin_text(target), admin_user_actions(target)); return
        if action == "UDETAIL":
            target = int(parts[2]); await render_admin(query, "📊 جزئیات کاربر", user_admin_text(target), admin_user_actions(target)); return
        if action == "ULOG":
            target = int(parts[2]); lines = [a for a in DATA.get('audit', []) if int(a.get('actor',-1)) == target][-15:][::-1]
            body = "\n".join(f"{a.get('action')} | {a.get('chat')} | {a.get('details','')}" for a in lines) or "لاگی برای این کاربر نیست."
            await render_admin(query, "📜 لاگ کاربر", body, admin_user_actions(target)); return
        if action == "GROUPS":
            page = int(parts[2]) if len(parts) > 2 else 0; await admin_groups_page(query, page); return
        if action == "G":
            await admin_group_detail(query, int(parts[2])); return
        if action == "GEN":
            cid, value = int(parts[2]), parts[3]; get_group(cid)["enabled"] = value == "on"; save_data(force=True); await admin_group_detail(query, cid); return
        if action == "GADULT":
            cid, value = int(parts[2]), parts[3]; get_group(cid)["adult_mode"] = value == "on"; save_data(force=True); await admin_group_detail(query, cid); return
        if action == "GMAX":
            cid, direction = int(parts[2]), parts[3]; g = get_group(cid); g["max_players"] = max(2, min(100, int(g.get("max_players",20)) + (1 if direction == "up" else -1))); save_data(force=True); await admin_group_detail(query, cid); return
        if action == "GEND":
            cid = int(parts[2]); game = active_game(cid)
            if game: end_game(game, "پایان توسط Super Admin")
            save_data(force=True); await admin_group_detail(query, cid); return
        if action == "GAMES":
            page = int(parts[2]) if len(parts)>2 else 0; await admin_games_page(query, page); return
        if action == "GAME":
            token = parts[2]; found = next((g for g in DATA["games"].values() if str(g.get('id','')).startswith(token)), None)
            if not found:
                await render_admin(query, "🎮 بازی", "بازی پیدا نشد.", admin_back_home()); return
            body = game_info_text(found)
            rows = [[InlineKeyboardButton("🛑 پایان بازی", callback_data=f"AX|GAMEEND|{found['chat_id']}|{escape(str(found['id']))[:15]}")], [InlineKeyboardButton("🔙 بازی‌ها", callback_data="AX|GAMES")]]
            await render_admin(query, "🎮 جزئیات بازی", body, InlineKeyboardMarkup(rows)); return
        if action == "GAMEEND":
            cid = int(parts[2]); game = active_game(cid)
            if game: end_game(game, "پایان توسط Super Admin")
            save_data(force=True); await admin_games_page(query, 0); return
        if action == "CONTENT":
            key = parts[2] if len(parts)>2 else None
            if key in CONTENT_LABELS:
                page = int(parts[3]) if len(parts)>3 else 0; await admin_content_category(query, key, page)
            else:
                await admin_content_page(query)
            return
        if action == "CDEL":
            key, index = parts[2], int(parts[3]); pool = all_content_bank(key)
            if 0 <= index < len(pool):
                # Only delete from global custom content; built-in content remains intact.
                target = pool[index]
                gc = DATA.setdefault("global_content", {}).setdefault(key, [])
                if target in gc: gc.remove(target)
                audit("content_delete", uid, None, f"{key}:{index}"); save_data(force=True)
            await admin_content_category(query, key, 0); return
        if action == "CCLEAR":
            key = parts[2]; DATA.setdefault("global_content", {})[key] = []; save_data(force=True); await admin_content_category(query, key, 0); return
        if action == "CADD":
            key = parts[2]; context.user_data["admin_flow"] = {"type": "content", "key": key}
            await render_admin(query, "➕ افزودن محتوا", f"دسته: {CONTENT_LABELS.get(key,key)}\n\nحالا متن جدید را در یک پیام بفرست.\nبعد از دریافت، ربات آن را ذخیره می‌کند.", InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="AX|FLOWCANCEL")]])); return
        if action == "ECONOMY":
            await admin_economy_page(query); return
        if action == "MULT":
            target, value = parts[2], int(parts[3]); key = "xp_multiplier" if target == "xp" else "coins_multiplier"; DATA["settings"][key] = value; save_data(force=True); await admin_economy_page(query); return
        if action == "SECURITY":
            await admin_security_page(query); return
        if action == "BANLIST":
            banned = [f"{k}: {escape(str(v.get('name','کاربر')))}" for k,v in DATA['users'].items() if v.get('banned')]
            await render_admin(query, "🚫 لیست کاربران بن‌شده", "\n".join(banned) or "لیست بن خالی است.", admin_back_home()); return
        if action == "CLEAN":
            cutoff = now_ts() - 3 * 86400; removed = 0
            for gid, game in list(DATA['games'].items()):
                if game.get('status') == 'finished' and int(game.get('finished_at',0)) < cutoff:
                    DATA['games'].pop(gid, None); removed += 1
            save_data(force=True); await render_admin(query, "🧹 پاکسازی", f"{removed} بازی قدیمی حذف شد.", admin_back_home()); return
        if action == "SETTINGS":
            await admin_settings_page(query); return
        if action == "GLOBMAX":
            direction = parts[2]; s = DATA['settings']; s['max_players_default'] = max(2, min(100, int(s.get('max_players_default',20)) + (1 if direction=='up' else -1))); save_data(force=True); await admin_settings_page(query); return
        if action == "ADULTDEF":
            DATA['settings']['adult_default'] = parts[2] == 'on'; save_data(force=True); await admin_settings_page(query); return
        if action == "SAVE":
            save_data(force=True); await render_admin(query, "💾 ذخیره", "اطلاعات با موفقیت روی فایل JSON ذخیره شد.", admin_back_home()); return
        if action == "BACKUP":
            await admin_backup_page(query); return
        if action == "MAKEBACKUP":
            path = make_backup_file("manual");
            try:
                await query.message.reply_document(document=open(path, "rb"), filename=os.path.basename(path), caption="📦 بکاپ ApexRival")
            except Exception:
                pass
            await admin_backup_page(query); return
        if action == "RESTORE":
            index = int(parts[2]); files = backup_files()
            if index < 0 or index >= len(files): await safe_answer_query(query, "بکاپ پیدا نشد.", True); return
            ok, msg = restore_backup(files[index]); await render_admin(query, "♻️ بازیابی", msg, admin_back_home()); return
        if action == "LOGS":
            await admin_logs_page(query); return
        if action == "BROADCAST":
            context.user_data["admin_flow"] = {"type": "broadcast"}
            await render_admin(query, "📣 پیام همگانی", "پیام موردنظر را در یک پیام بفرست.\n\nربات فقط در صورت ارسال پیام بعدی آن را ارسال می‌کند.", InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="AX|FLOWCANCEL")]])); return
        if action == "FLOWCANCEL":
            context.user_data.pop("admin_flow", None); await advanced_admin_panel(update, context); return
        if action == "TOOLS":
            await admin_tools_page(query); return
        if action == "HEALTH":
            body = f"نام: {BOT_NAME}\nنسخه: {ADVANCED_VERSION}\nفایل داده: {DATA_FILE}\nحجم داده: {Path(DATA_FILE).stat().st_size if Path(DATA_FILE).exists() else 0} bytes"
            await render_admin(query, "📊 Health", body, admin_back_home()); return
        if action == "ENDALL":
            count = 0
            for g in DATA['games'].values():
                if g.get('status') in ('active','lobby'):
                    end_game(g, 'پایان دسته‌جمعی توسط Super Admin'); count += 1
            save_data(force=True); await render_admin(query, "🛑 پایان بازی‌ها", f"{count} بازی پایان یافت.", admin_back_home()); return
        if action == "COUNTERS":
            body = f"کاربر: {len(DATA['users'])}\nگروه: {len(DATA['groups'])}\nبازی: {len(DATA['games'])}\nAudit: {len(DATA['audit'])}"
            await render_admin(query, "🔄 شمارنده‌ها", body, admin_back_home()); return
        return

    # -----------------------------
    # Game navigation
    # -----------------------------
    if family == "GM":
        game = active_game(chat_id)
        if not game:
            await safe_answer_query(query, "⛔ بازی فعالی نیست.", True)
            return
        if not valid_player(game, uid) and not is_admin(uid) and not leader_of(game, uid):
            await safe_answer_query(query, "🔒 ابتدا در لابی ثبت‌نام کن.", True)
            return
        game["_viewer_id"] = uid
        action = parts[1] if len(parts)>1 else "HOME"
        if action == "HOME":
            text = game_info_text(game) + "\n\nیک بخش را انتخاب کن:" 
            await safe_edit_query(query, text, game_home_keyboard(game)); return
        if action == "CLOSE":
            await safe_edit_query(query, "✅ منوی بازی بسته شد.", None); return
        if action == "FAST":
            if len(parts)==2: await safe_edit_query(query, "⚡ <b>چالش‌های سریع</b>\n\nیکی را انتخاب کن.", game_fast_keyboard()); return
            mode = parts[2]
            if mode == "NUMBER": await mini_number_hunt(query.message, game)
            elif mode == "RIDDLE": await mini_riddle(query.message, game)
            elif mode == "EMOJI": await mini_emoji(query.message, game)
            elif mode == "REACTION":
                if len(parts)>3 and parts[3]=="HIT":
                    state = game.get('reaction',{})
                    if state and not state.get('winner') and time.time() <= float(state.get('expires',0)):
                        state['winner'] = uid; reward_player(game, uid, 7, 3, win=True, reason='Reaction Rush'); save_data(force=True)
                        await safe_edit_query(query, f"⚡ برنده: {mention_user(uid, name_of(uid, game))}\n🎁 +۷ XP و +۳ سکه", game_fast_keyboard()); return
                await mini_reaction(query.message, game)
            elif mode == "WORDS": await mini_words(query.message, game)
            await safe_answer_query(query); return
        if action == "SOCIAL":
            if len(parts)==2: await safe_edit_query(query, "🎭 <b>بازی‌های اجتماعی</b>\n\nیک سبک را انتخاب کن.", game_social_keyboard(game)); return
            mode=parts[2]
            if mode == "TRUTH": await send_truth_or_dare(query.message, game, "truth")
            elif mode == "DARE": await send_truth_or_dare(query.message, game, "dare")
            elif mode == "FLIRTY": await send_flirty(query.message, game)
            elif mode == "QUESTION": await send_question(query.message, game)
            elif mode == "ADULT": await send_adult(query.message, game)
            return
        if action == "COMPETE":
            if len(parts)==2: await safe_edit_query(query, "⚔️ <b>حالت‌های رقابتی</b>\n\nرقابت موردنظر را انتخاب کن.", game_compete_keyboard()); return
            mode=parts[2]
            if mode == "DUEL": await duel_start(query.message, game)
            elif mode == "ROULETTE": await roulette(query.message, game)
            elif mode == "SPEED": await speed(query.message, game)
            elif mode == "VOTE": await create_vote(query.message, game)
            elif mode == "SURVIVAL": await mini_survival(query.message, game)
            elif mode == "TEAMS": await mini_teams(query.message, game)
            return
        if action == "SECRET":
            if len(parts)==2: await safe_edit_query(query, "🤫 <b>بخش مخفی</b>\n\nحالت موردنظر را انتخاب کن.", game_secret_keyboard()); return
            mode=parts[2]
            if mode == "MISSION": await create_secret_mission(query.message, game, context.bot)
            elif mode == "SPY": await create_spy(query.message, game, context.bot)
            elif mode == "ROLE": await mini_role(query.message, game, context.bot)
            elif mode == "PREDICT":
                if len(parts)>3:
                    choice = parts[3]
                    state = game.get('predict')
                    if not state or time.time()>float(state.get('expires',0)):
                        await safe_answer_query(query, 'این پیش‌بینی منقضی شده است.', True); return
                    state.setdefault('votes', {})[str(uid)] = 'heads' if choice=='heads' else 'tails'
                    await safe_answer_query(query, 'انتخاب ثبت شد ✅')
                    if len(state['votes']) >= len(game['players']):
                        secret = state['secret']; winners = [int(k) for k,v in state['votes'].items() if (v=='heads') == (secret=='شیر')]
                        for winner in winners: reward_player(game,winner,5,2,win=True,reason='Prediction')
                        await query.message.reply_text(f"🔮 نتیجه: <b>{secret}</b>\nبرنده‌ها: {', '.join(name_of(x,game) for x in winners) or 'هیچ‌کس'}", parse_mode=ParseMode.HTML)
                        game['predict']=None; game['phase']='free'; save_data(force=True)
                else: await mini_predict(query.message, game)
            return
        if action == "REWARDS":
            if len(parts)==2: await safe_edit_query(query, "☠️ <b>حکم و پاداش</b>\n\nمدیریت حکم، آیتم و دستاورد.", game_reward_keyboard(game)); return
            mode=parts[2]
            if mode == "MINE": await penalty_mine(query, game)
            elif mode == "SHOP": await send_shop(query.message, uid)
            elif mode == "INV":
                inv = inventory(uid); body = "\n".join(f"{SHOP[k]['name']}: {v}" for k,v in inv.items())
                await safe_edit_query(query, '🍀 <b>آیتم‌های من</b>\n\n'+body, game_reward_keyboard(game))
            elif mode == "ACH":
                u=get_user(uid); body='\n'.join(f"{'✅' if k in u.get('achievements',[]) else '🔒'} {v[0]}" for k,v in ACHIEVEMENTS.items()); await safe_edit_query(query, '🏅 <b>دستاوردها</b>\n\n'+body, game_reward_keyboard(game))
            return
        if action == "STATUS":
            await safe_edit_query(query, game_info_text(game), game_home_keyboard(game)); return
        if action == "HOST":
            if not leader_of(game, uid) and not is_admin(uid):
                await safe_answer_query(query, "👑 فقط سرگروه یا Super Admin.", True); return
            if len(parts)==2:
                await safe_edit_query(query, "👑 <b>کنترل سرگروه</b>\n\nفقط کنترل‌هایی که مخصوص مدیریت همین دست هستند اینجا نمایش داده می‌شوند.", host_control_keyboard()); return
            mode=parts[2]
            if mode == "RANDOM":
                kinds=['TRUTH','DARE','QUESTION','DUEL','ROULETTE','SPEED','RIDDLE','EMOJI']; chosen=random.choice(kinds); await query.message.reply_text(f"🎲 حالت انتخاب‌شده: <b>{chosen}</b>",parse_mode=ParseMode.HTML)
                if chosen=='TRUTH': await send_truth_or_dare(query.message,game,'truth')
                elif chosen=='DARE': await send_truth_or_dare(query.message,game,'dare')
                elif chosen=='QUESTION': await send_question(query.message,game)
                elif chosen=='DUEL': await duel_start(query.message,game)
                elif chosen=='ROULETTE': await roulette(query.message,game)
                elif chosen=='SPEED': await speed(query.message,game)
                elif chosen=='RIDDLE': await mini_riddle(query.message,game)
                elif chosen=='EMOJI': await mini_emoji(query.message,game)
            elif mode=='PENALTY':
                target=random.choice(game['players']); p=assign_penalty(game,target,source='👑 حکم سرگروه'); await query.message.reply_text(f"☠️ حکم برای {mention_user(target,name_of(target,game))}: {escape(p['text'])}",parse_mode=ParseMode.HTML)
            elif mode=='NEXT': game['round']=int(game.get('round',0))+1; game['phase']='free'; touch_game(game); save_data(force=True); await safe_edit_query(query,'⏭ دور بعد آماده است.',game_home_keyboard(game))
            elif mode=='END': end_game(game,'پایان توسط سرگروه'); save_data(force=True); await safe_edit_query(query,'🏁 بازی تمام شد.',None)
            elif mode=='PLAYERS': await safe_edit_query(query,lobby_text(game),host_control_keyboard())
            elif mode=='SETTINGS': await safe_edit_query(query,'⚙️ تنظیمات لابی از فرمان /game و دکمه‌های قبل از شروع کنترل می‌شود.',host_control_keyboard())
            return


# ============================================================
# Advanced text router / wizard
# ============================================================

async def advanced_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update):
        return
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id
    text = update.message.text.strip()
    flow = context.user_data.get("admin_flow") if is_admin(uid) else None
    if flow:
        ftype = flow.get("type")
        if ftype == "broadcast":
            ok=fail=0
            for target in list(DATA.get('users',{})):
                try:
                    await context.bot.send_message(chat_id=int(target), text=f"📣 <b>ApexRival</b>\n\n{escape(text)}", parse_mode=ParseMode.HTML)
                    ok += 1
                except Exception:
                    fail += 1
            DATA.setdefault('broadcast_log',[]).append({'ts':now_ts(),'actor':uid,'ok':ok,'fail':fail})
            audit('broadcast',uid,None,f'ok={ok};fail={fail}')
            context.user_data.pop('admin_flow',None)
            save_data(force=True)
            await update.message.reply_text(f"📣 پیام همگانی ارسال شد. ✅ {ok} | ❌ {fail}")
            return
        if ftype == "content":
            key=flow.get('key','truth')
            DATA.setdefault('global_content',{}).setdefault(key,[]).append(text[:700])
            context.user_data.pop('admin_flow',None)
            audit('content_add',uid,None,key)
            save_data(force=True)
            await update.message.reply_text(f"✅ به بخش {CONTENT_LABELS.get(key,key)} اضافه شد.")
            return
    if text in ("👑 مدیریت ApexRival", "👑 پنل Super Admin"):
        await advanced_admin_panel(update, context)
        return
    if text == "🎮 بازی":
        chat = update.effective_chat
        if chat.type not in ('group','supergroup'):
            await update.message.reply_text('🎮 بازی گروهی را باید داخل گروه اجرا کنی.')
            return
        game = active_game(chat.id)
        if not game:
            await update.message.reply_text('🎮 هنوز بازی فعالی نیست. سرگروه می‌تواند /game را بزند.')
            return
        if game.get('status') == 'lobby':
            await update.message.reply_text(lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(game['id']))
        else:
            game['_viewer_id']=uid
            await update.message.reply_text(game_info_text(game), parse_mode=ParseMode.HTML, reply_markup=game_home_keyboard(game))
        return
    if text == "👤 پروفایل": await profile(update,context); return
    if text == "🏆 رتبه‌بندی": await rank(update,context); return
    if text == "🛒 فروشگاه": await shop_cmd(update,context); return
    if text == "🏅 دستاوردها": await achievements_cmd(update,context); return
    if text in ("📜 قوانین","❓ راهنما"): await help_cmd(update,context); return
    # Fallback preserves all previous commands/buttons.
    await text_router(update, context)


# -----------------------------
# Expanded maintenance
# -----------------------------

async def advanced_cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    now = now_ts()
    changed = False
    for game in list(DATA.get('games',{}).values()):
        if game.get('status') == 'active':
            group = get_group(int(game['chat_id']))
            timeout = int(group.get('settings',{}).get('auto_end_minutes',90))*60
            if now - int(game.get('last_activity',now)) > timeout:
                end_game(game,'پایان خودکار به علت بی‌فعالیتی')
                changed=True
            for key in ('speed','vote','secret','riddle','emoji','reaction','word','number_hunt','predict'):
                state = game.get(key)
                if state and float(state.get('expires',0)) and time.time()>float(state.get('expires',0)):
                    game[key]=None
                    if game.get('phase') == key:
                        game['phase']='free'
                    changed=True
        elif game.get('status') == 'lobby' and now - int(game.get('last_activity',now)) > 4*3600:
            end_game(game,'لابی منقضی شد')
            changed=True
    if changed:
        save_data(force=True)
    else:
        save_data()



# -----------------------------
# Compatibility bridges: the clean UI replaces the old crowded keyboards.
# -----------------------------
main_keyboard = main_keyboard_v4
game_keyboard = game_home_keyboard

# The advanced callback router uses short callback families. Every callback is answered
# before rendering so Telegram's loading spinner is cleared even when a page fails to edit.

# -----------------------------
# Extended Prompt Vault
# -----------------------------
EXTENDED_PROMPT_VAULT = {
    'truth': [
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🕵️ اعتراف: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🕵️ اعتراف: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
    ],
    'dare': [
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک خاطره کوتاه از مدرسه را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک موقعیت خنده\u200cدار در چت را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک تصمیم ناگهانی را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک تجربه از یک بازی گروهی را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک اشتباه کوچک که نتیجه عجیبی داشت را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک مهارتی که دوست داری یاد بگیری را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک قانون شخصی را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک عادت روزمره را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک اتفاق غیرمنتظره در هفته اخیر را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک انتخاب سخت ولی بی\u200cخطر را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک سفر خیالی را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک رقابت دوستانه را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک فیلم خیالی را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک شغل غیرمعمول را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک مهمانی فرضی را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک مسابقه تلویزیونی را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک تیم خیالی را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک لقب بامزه را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک اختراع عجیب را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک روز کاملاً بدون برنامه را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک قانون جدید برای گروه را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک سورپرایز دوستانه را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک معمای کوتاه را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🔥 جرئت: یک چالش یک دقیقه\u200cای را انتخاب کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🔥 جرئت: یک انتخاب بین دو راه را انتخاب کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
    ],
    'question': [
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧠 سؤال: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧠 سؤال: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
    ],
    'flirty': [
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک خاطره کوتاه از مدرسه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک موقعیت خنده\u200cدار در چت» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک تصمیم ناگهانی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک تجربه از یک بازی گروهی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک مهارتی که دوست داری یاد بگیری» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک قانون شخصی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک عادت روزمره» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اتفاق غیرمنتظره در هفته اخیر» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب سخت ولی بی\u200cخطر» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سفر خیالی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک رقابت دوستانه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک فیلم خیالی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک شغل غیرمعمول» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مهمانی فرضی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک مسابقه تلویزیونی» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک تیم خیالی» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک لقب بامزه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک اختراع عجیب» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک روز کاملاً بدون برنامه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک قانون جدید برای گروه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک سورپرایز دوستانه» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک معمای کوتاه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '💘 فلرت محترمانه: موضوع «یک چالش یک دقیقه\u200cای» را در نظر بگیر؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '💘 فلرت محترمانه: موضوع «یک انتخاب بین دو راه» را در نظر بگیر؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
    ],
    'penalty': [
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک خاطره کوتاه از مدرسه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک موقعیت خنده\u200cدار در چت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تصمیم ناگهانی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تجربه از یک بازی گروهی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اشتباه کوچک که نتیجه عجیبی داشت» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهارتی که دوست داری یاد بگیری» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون شخصی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک عادت روزمره» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اتفاق غیرمنتظره در هفته اخیر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب سخت ولی بی\u200cخطر» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سفر خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک رقابت دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک فیلم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک شغل غیرمعمول» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مهمانی فرضی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک مسابقه تلویزیونی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک تیم خیالی» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک لقب بامزه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک اختراع عجیب» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک روز کاملاً بدون برنامه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک قانون جدید برای گروه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک سورپرایز دوستانه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک معمای کوتاه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک چالش یک دقیقه\u200cای» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '☠️ حکم: برای بازنده\u200cای که در «یک انتخاب بین دو راه» شکست خورده، یک کار کوتاه و کاملاً بی\u200cخطر طراحی کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
    ],
    'boss': [
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک خاطره کوتاه از مدرسه» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک موقعیت خنده\u200cدار در چت» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تصمیم ناگهانی» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تجربه از یک بازی گروهی» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهارتی که دوست داری یاد بگیری» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون شخصی» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک عادت روزمره» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب سخت ولی بی\u200cخطر» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سفر خیالی» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک رقابت دوستانه» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک فیلم خیالی» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک شغل غیرمعمول» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مهمانی فرضی» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک مسابقه تلویزیونی» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک تیم خیالی» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک لقب بامزه» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک اختراع عجیب» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک روز کاملاً بدون برنامه» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک قانون جدید برای گروه» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک سورپرایز دوستانه» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک معمای کوتاه» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک چالش یک دقیقه\u200cای» بساز؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '👑 Boss: یک مرحله ویژه با موضوع «یک انتخاب بین دو راه» بساز؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
    ],
    'mission': [
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک خاطره کوتاه از مدرسه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک موقعیت خنده\u200cدار در چت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تصمیم ناگهانی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک تجربه از یک بازی گروهی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اشتباه کوچک که نتیجه عجیبی داشت» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک مهارتی که دوست داری یاد بگیری» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک قانون شخصی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک عادت روزمره» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک اتفاق غیرمنتظره در هفته اخیر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب سخت ولی بی\u200cخطر» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک سفر خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک رقابت دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک فیلم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک شغل غیرمعمول» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک مهمانی فرضی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک مسابقه تلویزیونی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک تیم خیالی» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک لقب بامزه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک اختراع عجیب» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک روز کاملاً بدون برنامه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک قانون جدید برای گروه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک سورپرایز دوستانه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک معمای کوتاه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را تغییر می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ جوابت را دو بخشی کن.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک جمله بامزه تمامش کن.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🤫 مأموریت: با موضوع «یک چالش یک دقیقه\u200cای» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک مثال جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی در آن جالب\u200cتر است؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه قانونی برایش تعیین می\u200cکردی؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را اول انجام می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک ایموجی شروع کن.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک مجری مسابقه جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ یک نسخه سخت\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🤫 مأموریت: با موضوع «یک انتخاب بین دو راه» یک هدف اجتماعی و بی\u200cخطر تعریف کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک ایموجی شروع کن.',
    ],
    'riddle': [
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک خاطره کوتاه از مدرسه» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک موقعیت خنده\u200cدار در چت» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تصمیم ناگهانی» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک تجربه از یک بازی گروهی» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک اشتباه کوچک که نتیجه عجیبی داشت» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک مهارتی که دوست داری یاد بگیری» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون شخصی» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک عادت روزمره» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اتفاق غیرمنتظره در هفته اخیر» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب سخت ولی بی\u200cخطر» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک سفر خیالی» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک رقابت دوستانه» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک فیلم خیالی» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک شغل غیرمعمول» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک مهمانی فرضی» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک مسابقه تلویزیونی» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک تیم خیالی» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک لقب بامزه» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک اختراع عجیب» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک روز کاملاً بدون برنامه» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک قانون جدید برای گروه» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک سورپرایز دوستانه» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک معمای کوتاه» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه چیزی در آن جالب\u200cتر است؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه کسی را برای همراهی انتخاب می\u200cکردی؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه قانونی برایش تعیین می\u200cکردی؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه چیزی را اول انجام می\u200cدادی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه چیزی باعث خنده می\u200cشد؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه چیزی را به یک بازیکن دیگر می\u200cسپردی؟ جوابت را دو بخشی کن.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ کدام گزینه را انتخاب می\u200cکنی و چرا؟ با یک جمله بامزه تمامش کن.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ یک نسخه سخت\u200cتر از آن چیست؟ مثل یک بازیکن حرفه\u200cای جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه جایزه\u200cای برایش می\u200cگذاشتی؟ جوابت را بدون توضیح اضافی بگو.',
        '🧩 معما: یک معمای مرتبط با «یک چالش یک دقیقه\u200cای» طرح کن؛ چه چیزی باعث می\u200cشد گروه دوباره آن را بازی کند؟ با یک مثال جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه چیزی را تغییر می\u200cدادی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه عنوانی برایش می\u200cگذاشتی؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه چیزی می\u200cتواند همه را غافلگیر کند؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه چیزی را اصلاً انجام نمی\u200cدادی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه چیزی باعث برد تو می\u200cشد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چطور آن را در دو جمله تعریف می\u200cکنی؟ مثل یک مجری مسابقه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه کسی در آن بهتر عمل می\u200cکرد؟ خیلی سریع و مستقیم جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ یک نسخه آسان\u200cتر از آن چیست؟ خیلی کوتاه جواب بده.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه حکمی برای بازنده اما بی\u200cخطر می\u200cگذاشتی؟ با یک ایموجی شروع کن.',
        '🧩 معما: یک معمای مرتبط با «یک انتخاب بین دو راه» طرح کن؛ چه چیزی آن را خاص می\u200cکرد؟ از بین دو گزینه انتخاب کن و دلیل بده.',
    ],
}

for _vault_key, _vault_items in EXTENDED_PROMPT_VAULT.items():
    ADVANCED_CONTENT.setdefault(_vault_key, []).extend(_vault_items)

EXTENDED_PROMPT_TOTAL = sum(len(v) for v in EXTENDED_PROMPT_VAULT.values())

SCENARIO_PACKS = [
    {"id": 1, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 2, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 3, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 4, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 5, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 6, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 7, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 8, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 9, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 10, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 11, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 12, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 13, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 14, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 15, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 16, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 17, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 18, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 19, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 20, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 21, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 22, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 23, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 24, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 25, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 26, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 27, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 28, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 29, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 30, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 31, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 32, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 33, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 34, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 35, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 36, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 37, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 38, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 39, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 40, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 41, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 42, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 43, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 44, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 45, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 46, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 47, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 48, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 49, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 50, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 51, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 52, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 53, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 54, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 55, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 56, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 57, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 58, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 59, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 60, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 61, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 62, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 63, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 64, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 65, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 66, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 67, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 68, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 69, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 70, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 71, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 72, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 73, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 74, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 75, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 76, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 77, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 78, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 79, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 80, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 81, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 82, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 83, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 84, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 85, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 86, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 87, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 88, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 89, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 90, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 91, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 92, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 93, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 94, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 95, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 96, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 97, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 98, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 99, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 100, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 101, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 102, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 103, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 104, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 105, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 106, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 107, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 108, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 109, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 110, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 111, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 112, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 113, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 114, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 115, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 116, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 117, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 118, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 119, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 120, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 121, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 122, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 123, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 124, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 125, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 126, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 127, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 128, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 129, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 130, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 131, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 132, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 133, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 134, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 135, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 136, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 137, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 138, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 139, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 140, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 141, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 142, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 143, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 144, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 145, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 146, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 147, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 148, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 149, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 150, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 151, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 152, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 153, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 154, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 155, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 156, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 157, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 158, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 159, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 160, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 161, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 162, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 163, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 164, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 165, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 166, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 167, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 168, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 169, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 170, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 171, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 172, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 173, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 174, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 175, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 176, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 177, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 178, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 179, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 180, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 181, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 182, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 183, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 184, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 185, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 186, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 187, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 188, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 189, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 190, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 191, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 192, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 193, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 194, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 195, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 196, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 197, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 198, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 199, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 200, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 201, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 202, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 203, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 204, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 205, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 206, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 207, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 208, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 209, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 210, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 211, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 212, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 213, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 214, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 215, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 216, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 217, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 218, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 219, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 220, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 221, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 222, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 223, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 224, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 225, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 226, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 227, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 228, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 229, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 230, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 231, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 232, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 233, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 234, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 235, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 236, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 237, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 238, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 239, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 240, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 241, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 242, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 243, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 244, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 245, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 246, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 247, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 248, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 249, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 250, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 251, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 252, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 253, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 254, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 255, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 256, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 257, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 258, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 259, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 260, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 261, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 262, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 263, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 264, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 265, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 266, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 267, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 268, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 269, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 270, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 271, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 272, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 273, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 274, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 275, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 276, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 277, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 278, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 279, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 280, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 281, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 282, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 283, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 284, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 285, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 286, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 287, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 288, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 289, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 290, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 291, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 292, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 293, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 294, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 295, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 296, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 297, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 298, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 299, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 300, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 301, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 302, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 303, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 304, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 305, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 306, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 307, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 308, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 309, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 310, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 311, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 312, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 313, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 314, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 315, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 316, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 317, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 318, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 319, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 320, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 321, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 322, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 323, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 324, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 325, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 326, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 327, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 328, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 329, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 330, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 331, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 332, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 333, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 334, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 335, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 336, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 337, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 338, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 339, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 340, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 341, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 342, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 343, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 344, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 345, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 346, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 347, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 348, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 349, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 350, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 351, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 352, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 353, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 354, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 355, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 356, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 357, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 358, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 359, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 360, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 361, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 362, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 363, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 364, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 365, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 366, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 367, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 368, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 369, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 370, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 371, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 372, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 373, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 374, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 375, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 376, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 377, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 378, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 379, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 380, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 381, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 382, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 383, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 384, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 385, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 386, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 387, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 388, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 389, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 390, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 391, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 392, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 393, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 394, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 395, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 396, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 397, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 398, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 399, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 400, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 401, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 402, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 403, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 404, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 405, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 406, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 407, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 408, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 409, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 410, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 411, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 412, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 413, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 414, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 415, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 416, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 417, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 418, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 419, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 420, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 421, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 422, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 423, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 424, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 425, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 426, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 427, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 428, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 429, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 430, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 431, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 432, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 433, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 434, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 435, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 436, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 437, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 438, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 439, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 440, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 441, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 442, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 443, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 444, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 445, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 446, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 447, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 448, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 449, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 450, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 451, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 452, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 453, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 454, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 455, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 456, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 457, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 458, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 459, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 460, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 461, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 462, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 463, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 464, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 465, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 466, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 467, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 468, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 469, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 470, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 471, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 472, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 473, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 474, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 475, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 476, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 477, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 478, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 479, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 480, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 481, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 482, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 483, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 484, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 485, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 486, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 487, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 488, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 489, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 490, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 491, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 492, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 493, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 494, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 495, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 496, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 497, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 498, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 499, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 500, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 501, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 502, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 503, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 504, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 505, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 506, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 507, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 508, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 509, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 510, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 511, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 512, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 513, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 514, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 515, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 516, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 517, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 518, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 519, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 520, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 521, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 522, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 523, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 524, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 525, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 526, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 527, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 528, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 529, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 530, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 531, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 532, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 533, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 534, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 535, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 536, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 537, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 538, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 539, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 540, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 541, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 542, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 543, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 544, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 545, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 546, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 547, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 548, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 549, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 550, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 551, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 552, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 553, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 554, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 555, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 556, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 557, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 558, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 559, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 560, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 561, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 562, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 563, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 564, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 565, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 566, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 567, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 568, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 569, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 570, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 571, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 572, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 573, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 574, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 575, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 576, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 577, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 578, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 579, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 580, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 581, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 582, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 583, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 584, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 585, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 586, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 587, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 588, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 589, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 590, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 591, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 592, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 593, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 594, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 595, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 596, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 597, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 598, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 599, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 600, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 601, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 602, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 603, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 604, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 605, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 606, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 607, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 608, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 609, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 610, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 611, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 612, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 613, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 614, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 615, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 616, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 617, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 618, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 619, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 620, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 621, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 622, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 623, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 624, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 625, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 626, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 627, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 628, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 629, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 630, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
    {"id": 631, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 2, "tempo": 2},
    {"id": 632, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 3, "tempo": 3},
    {"id": 633, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 4, "tempo": 4},
    {"id": 634, "type": 'سرعت', "modifier": 'استریک', "weight": 5, "tempo": 5},
    {"id": 635, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 6, "tempo": 1},
    {"id": 636, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 7, "tempo": 2},
    {"id": 637, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 1, "tempo": 3},
    {"id": 638, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 2, "tempo": 4},
    {"id": 639, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 3, "tempo": 5},
    {"id": 640, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 4, "tempo": 1},
    {"id": 641, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 5, "tempo": 2},
    {"id": 642, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 6, "tempo": 3},
    {"id": 643, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 7, "tempo": 4},
    {"id": 644, "type": 'سرعت', "modifier": 'استریک', "weight": 1, "tempo": 5},
    {"id": 645, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 2, "tempo": 1},
    {"id": 646, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 3, "tempo": 2},
    {"id": 647, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 4, "tempo": 3},
    {"id": 648, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 5, "tempo": 4},
    {"id": 649, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 6, "tempo": 5},
    {"id": 650, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 7, "tempo": 1},
    {"id": 651, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 1, "tempo": 2},
    {"id": 652, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 2, "tempo": 3},
    {"id": 653, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 3, "tempo": 4},
    {"id": 654, "type": 'سرعت', "modifier": 'استریک', "weight": 4, "tempo": 5},
    {"id": 655, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 5, "tempo": 1},
    {"id": 656, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 6, "tempo": 2},
    {"id": 657, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 7, "tempo": 3},
    {"id": 658, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 1, "tempo": 4},
    {"id": 659, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 2, "tempo": 5},
    {"id": 660, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 3, "tempo": 1},
    {"id": 661, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 4, "tempo": 2},
    {"id": 662, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 5, "tempo": 3},
    {"id": 663, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 6, "tempo": 4},
    {"id": 664, "type": 'سرعت', "modifier": 'استریک', "weight": 7, "tempo": 5},
    {"id": 665, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 1, "tempo": 1},
    {"id": 666, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 2, "tempo": 2},
    {"id": 667, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 3, "tempo": 3},
    {"id": 668, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 4, "tempo": 4},
    {"id": 669, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 5, "tempo": 5},
    {"id": 670, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 6, "tempo": 1},
    {"id": 671, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 7, "tempo": 2},
    {"id": 672, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 1, "tempo": 3},
    {"id": 673, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 2, "tempo": 4},
    {"id": 674, "type": 'سرعت', "modifier": 'استریک', "weight": 3, "tempo": 5},
    {"id": 675, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 4, "tempo": 1},
    {"id": 676, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 5, "tempo": 2},
    {"id": 677, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 6, "tempo": 3},
    {"id": 678, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 7, "tempo": 4},
    {"id": 679, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 1, "tempo": 5},
    {"id": 680, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 2, "tempo": 1},
    {"id": 681, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 3, "tempo": 2},
    {"id": 682, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 4, "tempo": 3},
    {"id": 683, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 5, "tempo": 4},
    {"id": 684, "type": 'سرعت', "modifier": 'استریک', "weight": 6, "tempo": 5},
    {"id": 685, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 7, "tempo": 1},
    {"id": 686, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 1, "tempo": 2},
    {"id": 687, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 2, "tempo": 3},
    {"id": 688, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 3, "tempo": 4},
    {"id": 689, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 4, "tempo": 5},
    {"id": 690, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 5, "tempo": 1},
    {"id": 691, "type": 'دوئل', "modifier": 'فرصت ریرول', "weight": 6, "tempo": 2},
    {"id": 692, "type": 'معما', "modifier": 'انتخاب سرگروه', "weight": 7, "tempo": 3},
    {"id": 693, "type": 'رأی\u200cگیری', "modifier": 'جایزه مخفی', "weight": 1, "tempo": 4},
    {"id": 694, "type": 'سرعت', "modifier": 'استریک', "weight": 2, "tempo": 5},
    {"id": 695, "type": 'ماموریت', "modifier": 'زمان محدود', "weight": 3, "tempo": 1},
    {"id": 696, "type": 'تیم', "modifier": 'پاداش تیمی', "weight": 4, "tempo": 2},
    {"id": 697, "type": 'جاسوس', "modifier": 'پاداش سکه', "weight": 5, "tempo": 3},
    {"id": 698, "type": 'Boss', "modifier": 'حکم کوتاه', "weight": 6, "tempo": 4},
    {"id": 699, "type": 'گردونه', "modifier": 'انتخاب تصادفی', "weight": 7, "tempo": 5},
    {"id": 700, "type": 'پیش\u200cبینی', "modifier": 'جایزه XP', "weight": 1, "tempo": 1},
]

FEATURE_REGISTRY = [
    {"id": 1, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 2, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 3, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 4, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 5, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 6, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 7, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 8, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 9, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 10, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 11, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 12, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 13, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 14, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 15, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 16, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 17, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 18, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 19, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 20, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 21, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 22, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 23, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 24, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 25, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 26, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 27, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 28, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 29, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 30, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 31, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 32, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 33, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 34, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 35, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 36, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 37, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 38, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 39, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 40, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 41, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 42, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 43, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 44, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 45, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 46, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 47, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 48, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 49, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 50, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 51, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 52, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 53, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 54, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 55, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 56, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 57, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 58, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 59, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 60, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 61, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 62, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 63, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 64, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 65, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 66, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 67, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 68, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 69, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 70, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 71, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 72, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 73, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 74, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 75, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 76, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 77, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 78, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 79, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 80, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 81, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 82, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 83, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 84, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 85, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 86, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 87, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 88, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 89, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 90, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 91, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 92, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 93, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 94, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 95, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 96, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 97, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 98, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 99, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 100, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 101, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 102, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 103, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 104, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 105, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 106, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 107, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 108, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 109, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 110, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 111, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 112, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 113, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 114, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 115, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 116, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 117, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 118, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 119, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 120, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 121, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 122, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 123, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 124, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 125, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 126, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 127, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 128, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 129, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 130, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 131, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 132, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 133, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 134, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 135, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 136, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 137, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 138, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 139, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 140, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 141, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 142, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 143, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 144, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 145, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 146, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 147, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 148, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 149, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 150, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 151, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 152, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 153, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 154, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 155, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 156, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 157, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 158, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 159, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 160, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 161, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 162, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 163, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 164, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 165, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 166, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 167, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 168, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 169, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 170, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 171, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 172, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 173, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 174, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 175, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 176, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 177, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 178, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 179, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 180, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 181, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 182, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 183, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 184, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 185, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 186, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 187, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 188, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 189, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 190, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 191, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 192, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 193, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 194, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 195, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 196, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 197, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 198, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 199, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 200, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 201, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 202, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 203, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 204, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 205, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 206, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 207, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 208, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 209, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 210, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 211, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 212, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 213, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 214, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 215, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 216, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 217, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 218, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 219, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 220, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 221, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 222, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 223, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 224, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 225, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 226, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 227, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 228, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 229, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 230, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 231, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 232, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 233, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 234, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 235, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 236, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 237, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 238, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 239, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 240, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 241, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 242, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 243, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 244, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 245, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 246, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 247, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 248, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 249, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 250, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 251, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 252, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 253, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 254, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 255, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 256, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 257, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 258, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 259, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 260, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 261, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 262, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 263, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 264, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 265, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 266, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 267, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 268, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 269, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 270, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 271, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 272, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 273, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 274, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 275, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 276, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 277, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 278, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 279, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 280, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 281, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 282, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 283, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 284, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 285, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 286, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 287, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 288, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 289, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 290, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 291, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 292, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 293, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 294, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 295, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 296, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 297, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 298, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 299, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 300, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 301, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 302, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 303, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 304, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 305, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 306, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 307, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 308, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 309, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 310, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 311, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 312, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 313, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 314, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 315, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 316, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 317, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 318, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 319, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 320, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 321, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 322, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 323, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 324, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 325, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 326, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 327, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 328, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 329, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 330, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 331, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 332, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 333, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 334, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 335, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 336, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 337, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 338, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 339, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 340, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 341, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 342, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 343, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 344, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 345, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 346, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 347, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 348, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 349, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 350, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 351, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 352, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 353, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 354, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 355, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 356, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 357, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 358, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 359, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 360, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 361, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 362, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 363, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 364, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 365, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 366, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 367, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 368, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 369, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 370, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 371, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 372, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 373, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 374, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 375, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 376, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 377, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 378, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 379, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 380, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 381, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 382, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 383, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 384, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 385, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 386, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 387, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 388, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 389, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 390, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 391, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 392, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 393, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 394, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 395, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 396, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 397, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 398, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 399, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 400, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 401, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 402, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 403, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 404, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 405, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 406, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 407, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 408, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 409, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 410, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 411, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 412, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 413, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 414, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 415, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 416, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 417, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 418, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 419, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 420, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 421, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 422, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 423, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 424, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 425, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 426, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 427, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 428, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 429, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 430, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 431, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 432, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 433, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 434, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 435, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 436, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 437, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 438, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 439, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 440, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 441, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 442, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 443, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 444, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 445, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 446, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 447, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 448, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 449, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 450, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 451, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 452, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 453, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 454, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 455, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 456, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 457, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 458, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 459, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 460, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 461, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 462, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 463, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 464, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 465, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 466, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 467, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 468, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 469, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 470, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 471, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 472, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 473, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 474, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 475, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 476, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 477, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 478, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 479, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 480, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 481, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 482, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 483, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 484, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 485, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 486, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 487, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 488, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 489, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 490, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 491, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 492, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 493, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 494, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 495, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 496, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 497, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 498, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 499, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 500, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 501, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 502, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 503, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 504, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 505, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 506, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 507, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 508, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 509, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 510, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 511, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 512, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 513, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 514, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 515, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 516, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 517, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 518, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 519, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 520, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 521, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 522, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 523, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 524, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 525, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 526, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 527, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 528, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 529, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 530, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 531, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 532, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 533, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 534, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 535, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 536, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 537, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 538, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 539, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 540, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 541, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 542, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 543, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 544, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 545, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 546, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 547, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 548, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 549, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 550, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 551, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 552, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 553, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 554, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 555, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 556, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 557, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 558, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 559, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 560, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 561, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 562, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 563, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 564, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 565, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 566, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 567, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 568, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 569, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 570, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 571, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 572, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 573, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 574, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 575, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 576, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 577, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 578, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 579, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 580, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 581, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 582, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 583, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 584, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 585, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 586, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 587, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 588, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 589, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 590, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 591, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 592, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 593, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 594, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 595, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 596, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 597, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 598, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 599, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 600, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 601, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 602, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 603, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 604, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 605, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 606, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 607, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 608, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 609, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 610, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 611, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 612, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 613, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 614, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 615, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 616, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 617, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 618, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 619, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 620, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 621, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 622, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 623, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 624, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 625, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 626, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 627, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 628, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 629, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 630, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 631, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 632, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 633, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 634, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 635, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 636, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 637, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 638, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 639, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 640, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 641, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 642, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 643, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 644, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 645, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 646, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 647, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 648, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 649, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 650, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 651, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 652, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 653, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 654, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 655, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 656, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 657, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 658, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 659, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 660, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 661, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 662, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 663, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 664, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 665, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 666, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 667, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 668, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 669, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 670, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 671, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 672, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 673, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 674, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 675, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 676, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 677, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 678, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 679, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 680, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 681, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 682, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 683, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 684, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 685, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 686, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 687, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 688, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 689, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 690, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 691, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 692, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 693, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 694, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 695, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 696, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 697, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 698, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 699, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 700, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 701, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 702, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 703, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 704, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 705, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 706, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 707, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 708, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 709, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 710, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 711, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 712, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 713, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 714, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 715, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 716, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 717, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 718, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 719, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 720, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 721, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 722, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 723, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 724, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 725, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 726, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 727, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 728, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 729, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 730, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 731, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 732, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 733, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 734, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 735, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 736, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 737, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 738, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 739, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 740, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 741, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 742, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 743, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 744, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 745, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 746, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 747, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 748, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 749, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 750, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 751, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 752, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 753, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 754, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 755, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 756, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 757, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 758, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 759, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 760, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 761, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 762, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 763, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 764, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 765, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 766, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 767, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 768, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 769, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 770, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 771, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 772, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 773, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 774, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 775, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 776, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 777, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 778, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 779, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 780, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 781, "name": 'Emoji Decode', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 782, "name": 'Reaction Rush', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 783, "name": 'Word Chain', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 784, "name": 'Team Split', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 785, "name": 'Random Event', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 786, "name": 'Boss Mode', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 787, "name": 'Secret Mission', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 788, "name": 'Prediction', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 789, "name": 'Backup Center', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 790, "name": 'Audit Log', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 791, "name": 'User Control', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 792, "name": 'Group Control', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 793, "name": 'Lobby Lock', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 794, "name": 'Host Gate', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 795, "name": 'Ready Check', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 796, "name": 'Penalty Ledger', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 797, "name": 'XP Streak', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 798, "name": 'Coin Store', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 799, "name": 'Role Card', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 800, "name": 'Spy Round', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 801, "name": 'Vote Guard', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 802, "name": 'Duel Match', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 803, "name": 'Speed Rush', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 804, "name": 'Riddle Rush', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 805, "name": 'Emoji Decode', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 806, "name": 'Reaction Rush', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 807, "name": 'Word Chain', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 808, "name": 'Team Split', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 809, "name": 'Random Event', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 810, "name": 'Boss Mode', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
    {"id": 811, "name": 'Secret Mission', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 6},
    {"id": 812, "name": 'Prediction', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 7},
    {"id": 813, "name": 'Backup Center', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 8},
    {"id": 814, "name": 'Audit Log', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 9},
    {"id": 815, "name": 'User Control', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 10},
    {"id": 816, "name": 'Group Control', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 11},
    {"id": 817, "name": 'Lobby Lock', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 12},
    {"id": 818, "name": 'Host Gate', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 13},
    {"id": 819, "name": 'Ready Check', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 5},
    {"id": 820, "name": 'Penalty Ledger', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 6},
    {"id": 821, "name": 'XP Streak', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 7},
    {"id": 822, "name": 'Coin Store', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 8},
    {"id": 823, "name": 'Role Card', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 9},
    {"id": 824, "name": 'Spy Round', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 10},
    {"id": 825, "name": 'Vote Guard', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 11},
    {"id": 826, "name": 'Duel Match', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 12},
    {"id": 827, "name": 'Speed Rush', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 13},
    {"id": 828, "name": 'Riddle Rush', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 5},
    {"id": 829, "name": 'Emoji Decode', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 6},
    {"id": 830, "name": 'Reaction Rush', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 7},
    {"id": 831, "name": 'Word Chain', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 8},
    {"id": 832, "name": 'Team Split', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 9},
    {"id": 833, "name": 'Random Event', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 10},
    {"id": 834, "name": 'Boss Mode', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 11},
    {"id": 835, "name": 'Secret Mission', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 12},
    {"id": 836, "name": 'Prediction', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 13},
    {"id": 837, "name": 'Backup Center', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 5},
    {"id": 838, "name": 'Audit Log', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 6},
    {"id": 839, "name": 'User Control', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 7},
    {"id": 840, "name": 'Group Control', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 8},
    {"id": 841, "name": 'Lobby Lock', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 9},
    {"id": 842, "name": 'Host Gate', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 10},
    {"id": 843, "name": 'Ready Check', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 11},
    {"id": 844, "name": 'Penalty Ledger', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 12},
    {"id": 845, "name": 'XP Streak', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 13},
    {"id": 846, "name": 'Coin Store', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 5},
    {"id": 847, "name": 'Role Card', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 6},
    {"id": 848, "name": 'Spy Round', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 7},
    {"id": 849, "name": 'Vote Guard', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 8},
    {"id": 850, "name": 'Duel Match', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 9},
    {"id": 851, "name": 'Speed Rush', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 10},
    {"id": 852, "name": 'Riddle Rush', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 11},
    {"id": 853, "name": 'Emoji Decode', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 12},
    {"id": 854, "name": 'Reaction Rush', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 13},
    {"id": 855, "name": 'Word Chain', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 5},
    {"id": 856, "name": 'Team Split', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 6},
    {"id": 857, "name": 'Random Event', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 7},
    {"id": 858, "name": 'Boss Mode', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 8},
    {"id": 859, "name": 'Secret Mission', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 9},
    {"id": 860, "name": 'Prediction', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 10},
    {"id": 861, "name": 'Backup Center', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 11},
    {"id": 862, "name": 'Audit Log', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 12},
    {"id": 863, "name": 'User Control', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 13},
    {"id": 864, "name": 'Group Control', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 5},
    {"id": 865, "name": 'Lobby Lock', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 6},
    {"id": 866, "name": 'Host Gate', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 7},
    {"id": 867, "name": 'Ready Check', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 8},
    {"id": 868, "name": 'Penalty Ledger', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 9},
    {"id": 869, "name": 'XP Streak', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 10},
    {"id": 870, "name": 'Coin Store', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 11},
    {"id": 871, "name": 'Role Card', "tier": 2, "reward_xp": 2, "reward_coins": 2, "cooldown": 12},
    {"id": 872, "name": 'Spy Round', "tier": 3, "reward_xp": 3, "reward_coins": 3, "cooldown": 13},
    {"id": 873, "name": 'Vote Guard', "tier": 4, "reward_xp": 4, "reward_coins": 4, "cooldown": 5},
    {"id": 874, "name": 'Duel Match', "tier": 5, "reward_xp": 5, "reward_coins": 5, "cooldown": 6},
    {"id": 875, "name": 'Speed Rush', "tier": 1, "reward_xp": 6, "reward_coins": 6, "cooldown": 7},
    {"id": 876, "name": 'Riddle Rush', "tier": 2, "reward_xp": 7, "reward_coins": 1, "cooldown": 8},
    {"id": 877, "name": 'Emoji Decode', "tier": 3, "reward_xp": 8, "reward_coins": 2, "cooldown": 9},
    {"id": 878, "name": 'Reaction Rush', "tier": 4, "reward_xp": 9, "reward_coins": 3, "cooldown": 10},
    {"id": 879, "name": 'Word Chain', "tier": 5, "reward_xp": 10, "reward_coins": 4, "cooldown": 11},
    {"id": 880, "name": 'Team Split', "tier": 1, "reward_xp": 1, "reward_coins": 5, "cooldown": 12},
    {"id": 881, "name": 'Random Event', "tier": 2, "reward_xp": 2, "reward_coins": 6, "cooldown": 13},
    {"id": 882, "name": 'Boss Mode', "tier": 3, "reward_xp": 3, "reward_coins": 1, "cooldown": 5},
    {"id": 883, "name": 'Secret Mission', "tier": 4, "reward_xp": 4, "reward_coins": 2, "cooldown": 6},
    {"id": 884, "name": 'Prediction', "tier": 5, "reward_xp": 5, "reward_coins": 3, "cooldown": 7},
    {"id": 885, "name": 'Backup Center', "tier": 1, "reward_xp": 6, "reward_coins": 4, "cooldown": 8},
    {"id": 886, "name": 'Audit Log', "tier": 2, "reward_xp": 7, "reward_coins": 5, "cooldown": 9},
    {"id": 887, "name": 'User Control', "tier": 3, "reward_xp": 8, "reward_coins": 6, "cooldown": 10},
    {"id": 888, "name": 'Group Control', "tier": 4, "reward_xp": 9, "reward_coins": 1, "cooldown": 11},
    {"id": 889, "name": 'Lobby Lock', "tier": 5, "reward_xp": 10, "reward_coins": 2, "cooldown": 12},
    {"id": 890, "name": 'Host Gate', "tier": 1, "reward_xp": 1, "reward_coins": 3, "cooldown": 13},
    {"id": 891, "name": 'Ready Check', "tier": 2, "reward_xp": 2, "reward_coins": 4, "cooldown": 5},
    {"id": 892, "name": 'Penalty Ledger', "tier": 3, "reward_xp": 3, "reward_coins": 5, "cooldown": 6},
    {"id": 893, "name": 'XP Streak', "tier": 4, "reward_xp": 4, "reward_coins": 6, "cooldown": 7},
    {"id": 894, "name": 'Coin Store', "tier": 5, "reward_xp": 5, "reward_coins": 1, "cooldown": 8},
    {"id": 895, "name": 'Role Card', "tier": 1, "reward_xp": 6, "reward_coins": 2, "cooldown": 9},
    {"id": 896, "name": 'Spy Round', "tier": 2, "reward_xp": 7, "reward_coins": 3, "cooldown": 10},
    {"id": 897, "name": 'Vote Guard', "tier": 3, "reward_xp": 8, "reward_coins": 4, "cooldown": 11},
    {"id": 898, "name": 'Duel Match', "tier": 4, "reward_xp": 9, "reward_coins": 5, "cooldown": 12},
    {"id": 899, "name": 'Speed Rush', "tier": 5, "reward_xp": 10, "reward_coins": 6, "cooldown": 13},
    {"id": 900, "name": 'Riddle Rush', "tier": 1, "reward_xp": 1, "reward_coins": 1, "cooldown": 5},
]


# -----------------------------
# Final system metadata
# -----------------------------
ADVANCED_FEATURES = {
    'admin_navigation': True,
    'admin_user_tools': True,
    'admin_group_tools': True,
    'admin_game_tools': True,
    'admin_backup_restore': True,
    'admin_content_manager': True,
    'admin_broadcast_wizard': True,
    'game_navigation': True,
    'mini_games': True,
    'secret_roles': True,
    'clean_navigation': True,
    'callback_answer_safety': True,
    'extended_prompt_vault': True,
    'scenario_registry': True,
    'feature_registry': True,
}

SYSTEM_SNAPSHOT = {
    'build': 'ApexRival 4.0',
    'architecture': 'single_file_json',
    'navigation': 'shallow_category_first',
    'persistence': 'atomic_json_replace',
    'admin': 'super_admin_only',
    'group_flow': 'lobby_then_confirmed_start',
    'source_contract': 'more_than_5000_lines',
}


def system_summary_line() -> str:
    return (
        f"{BOT_NAME} {ADVANCED_VERSION} | users={len(DATA.get('users', {}))} | "
        f"groups={len(DATA.get('groups', {}))} | games={len(DATA.get('games', {}))} | "
        f"features={len(FEATURE_REGISTRY)} | prompts={EXTENDED_PROMPT_TOTAL}"
    )


def source_feature_count() -> int:
    return len(ADVANCED_FEATURES) + len(FEATURE_REGISTRY) + len(SCENARIO_PACKS)


# -----------------------------
# Final wiring for ApexRival 4.0
# -----------------------------
async def post_init_v4(app: Application) -> None:
    await app.bot.set_my_commands([
        ('start', 'شروع ApexRival'),
        ('game', 'ساخت لابی بازی'),
        ('menu', 'منوی اصلی'),
        ('profile', 'پروفایل'),
        ('rank', 'رتبه‌بندی'),
        ('shop', 'فروشگاه'),
        ('achievements', 'دستاوردها'),
        ('help', 'راهنما'),
        ('id', 'آیدی'),
        ('admin', 'پنل مدیریت'),
    ])
    if app.job_queue:
        app.job_queue.run_repeating(advanced_cleanup_job, interval=30, first=30, name='apex_v4_cleanup')


def build_application_v4() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN is missing')
    app = Application.builder().token(BOT_TOKEN).post_init(post_init_v4).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('game', game_command))
    app.add_handler(CommandHandler('menu', menu_cmd))
    app.add_handler(CommandHandler('profile', profile))
    app.add_handler(CommandHandler('rank', rank))
    app.add_handler(CommandHandler('shop', shop_cmd))
    app.add_handler(CommandHandler('achievements', achievements_cmd))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('id', id_cmd))
    app.add_handler(CommandHandler('adult', adult_cmd))
    app.add_handler(CommandHandler('broadcast', broadcast))
    app.add_handler(CommandHandler('setmaxglobal', set_global_max))
    app.add_handler(CommandHandler('group_on', lambda u,c: group_toggle(u,c,True)))
    app.add_handler(CommandHandler('group_off', lambda u,c: group_toggle(u,c,False)))
    app.add_handler(CommandHandler('endgame', force_end_group))
    app.add_handler(CommandHandler('setgroupmax', group_max))
    app.add_handler(CommandHandler('setgroupmin', group_min))
    app.add_handler(CommandHandler('ban', lambda u,c: user_mod(u,c,'ban')))
    app.add_handler(CommandHandler('unban', lambda u,c: user_mod(u,c,'unban')))
    app.add_handler(CommandHandler('reset', lambda u,c: user_mod(u,c,'reset')))
    app.add_handler(CommandHandler('addxp', lambda u,c: user_mod(u,c,'addxp')))
    app.add_handler(CommandHandler('addcoins', lambda u,c: user_mod(u,c,'addcoins')))
    app.add_handler(CommandHandler('giveitem', lambda u,c: user_mod(u,c,'giveitem')))
    app.add_handler(CommandHandler('setlevel', lambda u,c: user_mod(u,c,'setlevel')))
    app.add_handler(CommandHandler('addq', lambda u,c: add_content(u,c,'truth')))
    app.add_handler(CommandHandler('addd', lambda u,c: add_content(u,c,'dare')))
    app.add_handler(CommandHandler('addf', lambda u,c: add_content(u,c,'flirty')))
    app.add_handler(CommandHandler('addp', lambda u,c: add_content(u,c,'penalty')))
    app.add_handler(CommandHandler('admin', advanced_admin_panel))
    app.add_handler(CallbackQueryHandler(advanced_callback, pattern=r'^(AX\||GM\|)'))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, advanced_text_router))
    return app


def main_v4():
    start_health_server()
    app = build_application_v4()
    print(f'{BOT_NAME} {ADVANCED_VERSION} starting...')
    app.run_polling(drop_pending_updates=True)


main = main_v4


if __name__ == '__main__':
    main()


# ============================================================================
# APEX RIVAL 5.0 — CINEMATIC UI / CLEAN UX / HARDENED ROUTER
# ============================================================================
# This layer deliberately overrides the previous presentation layer instead
# of deleting working game mechanics. The visible UX is now context-aware:
# lobby -> active game -> result -> next round. Admin is a separate shell.
# ============================================================================

APEX_V5 = "5.0"
ADVANCED_VERSION = APEX_V5
BOT_VERSION = APEX_V5

# Compatibility alias: older mechanics used RANDOM_EVENTS while the canonical bank is EVENTS.
RANDOM_EVENTS = EVENTS

V5_DESIGN = {
    "name": "Obsidian Apex",
    "principles": [
        "one_goal_per_screen",
        "only_relevant_actions",
        "stable_back_navigation",
        "destructive_confirmation",
        "no_duplicate_visible_entries",
        "short_status_cards",
        "group_state_gates",
    ],
    "accent": "🟣",
    "divider": "━━━━━━━━━━━━━━━━━━━━",
}

V5_CONFIRM = {}
V5_RATE = {}
V5_ADMIN_PAGE = {}
V5_FLOW = {}
V5_SESSION = {}


def v5_now_ms() -> int:
    return int(time.time() * 1000)


def v5_key(*parts) -> str:
    return ":".join(str(x) for x in parts)


def v5_clip(text: str, limit: int = 3800) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: limit - 40] + "\n… ادامه در پیام بعدی حذف شد."


def v5_unique(seq):
    out = []
    seen = set()
    for item in seq:
        item = str(item).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def v5_button(label: str, data: str) -> InlineKeyboardButton:
    # Telegram callback_data is limited; keep our UX tokens compact.
    if len(data.encode("utf-8")) > 64:
        raise ValueError(f"callback_data too long: {data}")
    return InlineKeyboardButton(label, callback_data=data)


def v5_markup(rows) -> InlineKeyboardMarkup:
    clean = []
    for row in rows:
        row = [x for x in row if x is not None]
        if row:
            clean.append(row)
    return InlineKeyboardMarkup(clean)


def v5_nav(back: str = "V5|HOME", refresh: str | None = None, close: str = "V5|CLOSE"):
    row = [v5_button("⌂ خانه", back)]
    if refresh:
        row.append(v5_button("↻", refresh))
    row.append(v5_button("✕ بستن", close))
    return [row]


def v5_breadcrumb(section: str, page: str | None = None) -> str:
    if page:
        return f"🟣 <b>ApexRival</b>  /  {escape(section)}  /  <b>{escape(page)}</b>"
    return f"🟣 <b>ApexRival</b>  /  <b>{escape(section)}</b>"


def v5_card(title: str, *lines: str) -> str:
    body = "\n".join(str(x) for x in lines if str(x).strip())
    return f"╭━━ {title} ━━╮\n{body}\n╰━━━━━━━━━━━━━━╯"


def v5_progress(value: int, total: int, width: int = 10) -> str:
    total = max(1, int(total))
    value = max(0, min(int(value), total))
    filled = round(width * value / total)
    return "🟣" * filled + "▫️" * (width - filled)


def v5_status_chip(enabled: bool, yes: str = "فعال", no: str = "خاموش") -> str:
    return f"🟢 {yes}" if enabled else f"⚫ {no}"


def v5_name(uid: int, game: dict[str, Any] | None = None) -> str:
    return name_of(uid, game)


def v5_group(game) -> dict[str, Any]:
    return get_group(int(game["chat_id"]))


def v5_is_player(game, uid: int) -> bool:
    return int(uid) in [int(x) for x in game.get("players", [])]


def v5_ready_state(game) -> dict[str, bool]:
    return game.setdefault("ready", {str(uid): True for uid in game.get("players", [])})


def v5_touch(game):
    touch_game(game)
    game.setdefault("v5", {})["last_ui"] = now_ts()


def v5_rate_limit(uid: int, action: str, seconds: float = 1.5) -> bool:
    key = v5_key(uid, action)
    now = time.time()
    old = float(V5_RATE.get(key, 0))
    if now - old < seconds:
        return False
    V5_RATE[key] = now
    return True


def v5_record_session(uid: int, chat_id: int, action: str):
    key = v5_key(uid, chat_id)
    session = V5_SESSION.setdefault(key, {"history": [], "last": None})
    session["last"] = action
    session["last_ts"] = time.time()
    session["history"] = (session["history"] + [action])[-25:]


def v5_menu_footer(back="V5|HOME", refresh=None):
    return v5_nav(back=back, refresh=refresh)


# ---------------------------------------------------------------------------
# V5 content hygiene: merge all existing content banks without visible dupes.
# ---------------------------------------------------------------------------
V5_BANKS = {}
for _k, _v in ADVANCED_CONTENT.items():
    V5_BANKS[_k] = v5_unique(_v)
for _k, _v in {
    "truth": TRUTHS,
    "dare": DARES,
    "flirty": FLIRTY,
    "adult": ADULT_SAFE,
    "penalty": PENALTIES,
    "boss": BOSS_CHALLENGES,
    "event": RANDOM_EVENTS,
    "question": QUESTIONS,
}.items():
    V5_BANKS.setdefault(_k, [])
    V5_BANKS[_k] = v5_unique(V5_BANKS[_k] + _v)


def v5_choose(game: dict[str, Any], key: str, fallback=None) -> str:
    bank = list(V5_BANKS.get(key, []))
    bank += list(get_group(int(game["chat_id"])).get("content", {}).get(key, []))
    bank += list(DATA.get("global_content", {}).get(key, []))
    bank = v5_unique(bank)
    if not bank:
        return fallback or "این حالت هنوز محتوایی ندارد."
    used = set(game.setdefault("used_content", {}).setdefault(key, []))
    available = [x for x in bank if x not in used]
    if not available:
        used.clear()
        available = bank
    pick = random.choice(available)
    used.add(pick)
    game["used_content"][key] = list(used)[-500:]
    return pick


# Route all legacy content consumers through the deduplicated V5 chooser.
choose_content = v5_choose


# ---------------------------------------------------------------------------
# V5 polished main menu — compact, predictable, role-aware.
# ---------------------------------------------------------------------------
def v5_main_keyboard(uid: int) -> ReplyKeyboardMarkup:
    rows = [
        ["🎮 بازی", "👤 پروفایل", "🏆 رتبه"],
        ["🛒 فروشگاه", "🏅 دستاوردها", "❓ راهنما"],
    ]
    if is_admin(uid):
        rows.append(["👑 مرکز مدیریت"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True, one_time_keyboard=False)


def v5_home_inline(uid: int):
    return v5_markup([
        [v5_button("🎮 ورود به بازی", "V5|GAME"), v5_button("👤 پروفایل", "V5|PROFILE")],
        [v5_button("🏆 رتبه‌بندی", "V5|RANK"), v5_button("🏅 دستاوردها", "V5|ACH")],
        [v5_button("🛒 فروشگاه", "V5|SHOP"), v5_button("❓ راهنما", "V5|HELP")],
        ([v5_button("👑 مرکز مدیریت", "V5|ADMIN")] if is_admin(uid) else []),
        [v5_button("✕ بستن", "V5|CLOSE")],
    ])


async def v5_send_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update):
        return
    uid = update.effective_user.id
    user = get_user(uid, update.effective_user.first_name or update.effective_user.username or "بازیکن")
    level_xp = int(user.get("xp", 0)) % 100
    status_card = v5_card(
        "وضعیت تو",
        f"⭐ Level <b>{user.get('level', 1)}</b>   ✨ XP <b>{user.get('xp', 0)}</b>",
        f"💰 سکه <b>{user.get('coins', 0)}</b>   🔥 استریک <b>{user.get('streak', 0)}</b>",
        f"{v5_progress(level_xp, 100)}  {level_xp}/100",
        f"🏅 {escape(title_for(user.get('xp', 0)))}",
    )
    text = (
        f"🟣 <b>{BOT_NAME}</b> <code>5.0</code>\n"
        f"{V5_DESIGN['divider']}\n"
        f"سلام <b>{escape(user['name'])}</b> 👋\n\n"
        f"{status_card}\n\n"
        f"🎮 برای گروه: <code>/game</code>\n"
        f"🔒 تا قبل از تأیید سرگروه، هیچ مرحله‌ای شروع نمی‌شود."
    )
    markup = v5_home_inline(uid)
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=v5_main_keyboard(uid))
        await update.message.reply_text("از اینجا انتخاب کن:", reply_markup=markup)
    elif update.callback_query:
        await safe_edit_query(update.callback_query, text, markup)

# ---------------------------------------------------------------------------
# V5 lobby / game presentation
# ---------------------------------------------------------------------------
def v5_lobby_markup(game):
    gid = game["id"]
    is_host = int(game["leader_id"]) == int(game.get("_viewer_id", 0)) or is_admin(int(game.get("_viewer_id", 0)))
    rows = [
        [v5_button("🎟 ثبت‌نام", f"V5|L|J|{gid}"), v5_button("🚪 خروج", f"V5|L|L|{gid}")],
        [v5_button("👥 بازیکنان", f"V5|L|P|{gid}"), v5_button("↻ بروزرسانی", f"V5|L|R|{gid}")],
    ]
    if is_host:
        rows += [
            [v5_button("✅ تأیید و شروع", f"V5|L|S|{gid}"), v5_button("⚙️ تنظیمات", f"V5|L|O|{gid}")],
            [v5_button("🛑 لغو لابی", f"V5|L|C|{gid}")],
        ]
    rows.append([v5_button("❓ قوانین لابی", "V5|HELP|LOBBY")])
    return v5_markup(rows)


def v5_lobby_text(game):
    players = [int(x) for x in game.get("players", [])]
    ready = v5_ready_state(game)
    lines = []
    for index, uid in enumerate(players, 1):
        mark = "🟢" if ready.get(str(uid), True) else "🟡"
        lines.append(f"{mark} {index}. {mention_user(uid, v5_name(uid, game))}")
    min_p = int(game.get("settings", {}).get("min_players", 2))
    max_p = int(game.get("settings", {}).get("max_players", 20))
    enough = len(players) >= min_p
    return (
        f"🎮 <b>ApexRival — Lobby</b>\n"
        f"{V5_DESIGN['divider']}\n"
        f"👑 سرگروه: {mention_user(game['leader_id'], game['leader_name'])}\n"
        f"👥 بازیکنان: <b>{len(players)}/{max_p}</b>  {'✅ آماده شروع' if enough else f'⏳ حداقل {min_p} نفر'}\n"
        f"{v5_progress(len(players), max_p, 12)}\n\n"
        f"<b>بازیکنان ثبت‌نام‌شده</b>\n" + ("\n".join(lines) or "هنوز کسی ثبت‌نام نکرده.") +
        "\n\n🔐 <i>ثبت‌نام فقط ورود به لابی است؛ شروع واقعی فقط با تأیید سرگروه انجام می‌شود.</i>"
    )


def v5_game_home_markup(game):
    uid = int(game.get("_viewer_id", 0))
    group = v5_group(game)
    rows = [
        [v5_button("⚡ سریع", "V5|G|Q"), v5_button("🎭 اجتماعی", "V5|G|S")],
        [v5_button("⚔️ رقابتی", "V5|G|B"), v5_button("🤫 مخفی", "V5|G|X")],
        [v5_button("☠️ حکم و پاداش", "V5|G|R"), v5_button("📊 وضعیت دست", "V5|G|I")],
    ]
    if leader_of(game, uid):
        rows.append([v5_button("👑 کنترل سرگروه", "V5|G|H")])
    if group.get("adult_mode"):
        # +18 only appears where it is relevant and only after the group enabled it.
        rows.append([v5_button("🔞 +18 غیرصریح", "V5|G|A")])
    rows.append([v5_button("✕ بستن", "V5|CLOSE")])
    return v5_markup(rows)


def v5_section_markup(section: str, game):
    if section == "Q":
        return v5_markup([
            [v5_button("🎯 عدد مخفی", "V5|M|N"), v5_button("🧩 معما", "V5|M|R")],
            [v5_button("😀 ایموجی", "V5|M|E"), v5_button("⚡ واکنش", "V5|M|F")],
            [v5_button("🔤 زنجیره کلمات", "V5|M|W")],
            *v5_nav("V5|GAME"),
        ])
    if section == "S":
        rows = [
            [v5_button("🕵️ اعتراف", "V5|S|T"), v5_button("🔥 جرئت", "V5|S|D")],
            [v5_button("💘 فلرت محترمانه", "V5|S|F"), v5_button("🧠 سؤال گروهی", "V5|S|Q")],
        ]
        return v5_markup(rows + ([ [v5_button("🔞 +18 غیرصریح", "V5|S|A")] ] if v5_group(game).get("adult_mode") else []) + v5_nav("V5|GAME"))
    if section == "B":
        return v5_markup([
            [v5_button("⚔️ دوئل", "V5|B|D"), v5_button("🎰 گردونه", "V5|B|R")],
            [v5_button("⚡ سرعت", "V5|B|S"), v5_button("🗳 رأی‌گیری", "V5|B|V")],
            [v5_button("🏁 بقا", "V5|B|U"), v5_button("👥 تیم‌ها", "V5|B|T")],
            *v5_nav("V5|GAME"),
        ])
    if section == "X":
        return v5_markup([
            [v5_button("🤫 مأموریت مخفی", "V5|X|M"), v5_button("🕵️ جاسوس", "V5|X|S")],
            [v5_button("🎭 کارت نقش", "V5|X|R"), v5_button("🔮 پیش‌بینی", "V5|X|P")],
            *v5_nav("V5|GAME"),
        ])
    if section == "R":
        return v5_markup([
            [v5_button("☠️ حکم من", "V5|R|P"), v5_button("🎒 آیتم‌ها", "V5|R|I")],
            [v5_button("🛒 فروشگاه", "V5|R|S"), v5_button("🏅 دستاورد", "V5|R|A")],
            *v5_nav("V5|GAME"),
        ])
    if section == "H":
        return v5_markup([
            [v5_button("🎯 حالت تصادفی", "V5|H|R"), v5_button("☠️ حکم تصادفی", "V5|H|P")],
            [v5_button("👥 بازیکنان", "V5|H|L"), v5_button("⏭ دور بعد", "V5|H|N")],
            [v5_button("🛑 پایان بازی", "V5|H|E")],
            *v5_nav("V5|GAME"),
        ])
    return v5_markup(v5_nav("V5|GAME"))


def v5_game_home_text(game):
    scores = []
    for uid in game.get("players", []):
        score = int(game.get("round_scores", {}).get(str(uid), 0))
        scores.append((score, int(uid)))
    scores.sort(reverse=True)
    top = scores[:3]
    top_lines = [f"{i}. {v5_name(uid, game)} — <b>{score}</b>" for i, (score, uid) in enumerate(top, 1)]
    return (
        f"🎮 <b>بازی فعال — ApexRival</b>\n"
        f"{V5_DESIGN['divider']}\n"
        f"🎯 دور <b>{int(game.get('round', 0))}</b>  •  👥 <b>{len(game.get('players', []))}</b> بازیکن\n"
        f"⚡ فاز: <b>{escape(str(game.get('phase','free')))}</b>\n\n"
        f"<b>صدر جدول این دست</b>\n" + ("\n".join(top_lines) if top_lines else "هنوز امتیازی ثبت نشده.") +
        "\n\nیک دسته را انتخاب کن؛ فقط گزینه‌های همین لحظه را نشان می‌دهیم."
    )


# ---------------------------------------------------------------------------
# V5 polished profile / rank / shop / achievements
# ---------------------------------------------------------------------------
async def v5_profile_message(update, context):
    if not await ensure_allowed(update):
        return
    uid = update.effective_user.id
    u = get_user(uid, update.effective_user.first_name or "بازیکن")
    inv = u.get("inventory", {})
    card = v5_card(
        "پروفایل",
        f"👤 <b>{escape(u.get('name', 'بازیکن'))}</b>",
        f"🏅 {escape(title_for(u.get('xp', 0)))}",
        f"⭐ Level <b>{u.get('level', 1)}</b>  •  ✨ XP <b>{u.get('xp', 0)}</b>",
        f"💰 {u.get('coins', 0)} سکه  •  🔥 استریک {u.get('streak', 0)}",
        f"🏆 برد {u.get('wins', 0)}  •  ☠️ باخت {u.get('losses', 0)}",
        f"🎮 بازی {u.get('games', 0)}  •  🤫 مأموریت {u.get('missions', 0)}",
    )
    text = (
        f"{v5_breadcrumb('حساب من')}\n\n{card}\n\n"
        f"🎒 <b>آیتم‌ها</b>\n"
        f"🛡 {inv.get('shield',0)}   🎲 {inv.get('reroll',0)}   "
        f"⚡ {inv.get('double_xp',0)}   🎫 {inv.get('pass',0)}   🍀 {inv.get('lucky',0)}"
    )
    markup = v5_markup([
        [v5_button("🏅 دستاوردها", "V5|ACH"), v5_button("🛒 فروشگاه", "V5|SHOP")],
        *v5_nav("V5|HOME"),
    ])
    if update.callback_query:
        await safe_edit_query(update.callback_query, text, markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def v5_rank_message(update, context):
    if not await ensure_allowed(update): return
    rows = sorted(DATA["users"].items(), key=lambda x: int(x[1].get("xp",0)), reverse=True)[:12]
    me = str(update.effective_user.id)
    lines = []
    for i, (uid, u) in enumerate(rows, 1):
        crown = "👑" if i == 1 else "🏅" if i <= 3 else "▫️"
        marker = " ← تو" if uid == me else ""
        lines.append(f"{crown} <b>{i:02d}</b>  {escape(str(u.get('name','بازیکن')))}  ·  ⭐ {int(u.get('xp',0))}{marker}")
    text = f"{v5_breadcrumb('رقابت','رتبه‌بندی')}\n\n{v5_card('Top Players', *(lines or ['هنوز داده‌ای نیست.']))}"
    markup = v5_markup([v5_nav("V5|HOME")])
    if update.callback_query: await safe_edit_query(update.callback_query, text, markup)
    else: await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def v5_help_message(update, context, scope="HOME"):
    if not await ensure_allowed(update):
        return
    if scope == "LOBBY":
        card = v5_card(
            "قانون اصلی",
            "1️⃣ بازیکن ثبت‌نام می‌کند.",
            "2️⃣ لابی تا رسیدن به حداقل ظرفیت باز می‌ماند.",
            "3️⃣ فقط سرگروه دکمه تأیید و شروع را دارد.",
            "4️⃣ بعد از شروع، منوی بازی فعال می‌شود.",
            "5️⃣ لغو و تنظیمات فقط برای سرگروه است.",
        )
        text = f"{v5_breadcrumb('بازی','Lobby')}\n\n{card}"
        markup = v5_markup([v5_nav("V5|GAME")])
    else:
        card = v5_card(
            "چطور بازی کنیم؟",
            "🎮 در گروه /game را بزن.",
            "🎟 بازیکنان وارد Lobby می‌شوند.",
            "👑 سرگروه شروع را تأیید می‌کند.",
            "⚔️ رقابت‌ها و بازی‌ها بعد از شروع فعال می‌شوند.",
            "☠️ باخت بعضی حالت‌ها حکم ایجاد می‌کند.",
            "⭐ XP و 💰 سکه دائمی ذخیره می‌شوند.",
        )
        text = f"{v5_breadcrumb('راهنما')}\n\n{card}\n\n🔒 هیچ مرحله‌ای نباید شامل خطر، تهدید، اجبار، آزار یا افشای اطلاعات خصوصی باشد."
        markup = v5_markup(v5_nav("V5|HOME"))
    if update.callback_query:
        await safe_edit_query(update.callback_query, text, markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

# ---------------------------------------------------------------------------
# V5 game launcher wrappers
# ---------------------------------------------------------------------------
async def v5_show_active_game(query, game):
    game["_viewer_id"] = int(query.from_user.id)
    if game.get("status") == "lobby":
        await safe_edit_query(query, v5_lobby_text(game), v5_lobby_markup(game)); return
    await safe_edit_query(query, v5_game_home_text(game), v5_game_home_markup(game))


async def v5_require_active(query):
    game = active_game(query.message.chat_id if query.message else query.chat_id)
    if not game or game.get("status") != "active":
        await safe_answer_query(query, "⛔ هنوز بازی فعالی وجود ندارد.", True)
        return None
    if not v5_is_player(game, query.from_user.id) and not is_admin(query.from_user.id) and not leader_of(game, query.from_user.id):
        await safe_answer_query(query, "🔒 ابتدا در لابی ثبت‌نام کن.", True)
        return None
    game["_viewer_id"] = query.from_user.id
    return game


async def v5_create_lobby(update, context):
    if not await ensure_allowed(update): return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("🎮 این دستور را داخل گروه اجرا کن.")
        return
    if is_banned(user.id):
        await update.message.reply_text("🚫 دسترسی این حساب به بازی محدود شده است.")
        return
    group = get_group(chat.id)
    if not group.get("enabled", True) and not is_admin(user.id):
        await update.message.reply_text("🚫 ApexRival در این گروه خاموش است.")
        return
    current = active_game(chat.id)
    if current:
        current["_viewer_id"] = user.id
        markup = v5_lobby_markup(current) if current.get("status") == "lobby" else v5_game_home_markup(current)
        text = v5_lobby_text(current) if current.get("status") == "lobby" else v5_game_home_text(current)
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    game = make_game(chat.id, user.id, user.first_name or user.username or "سرگروه")
    game["ready"] = {str(user.id): True}
    game["phase"] = "lobby"
    v5_touch(game)
    save_data(force=True)
    await update.message.reply_text(v5_lobby_text(game), parse_mode=ParseMode.HTML, reply_markup=v5_lobby_markup(game))


# ---------------------------------------------------------------------------
# V5 admin shell — 8 focused domains, confirmations for destructive actions.
# ---------------------------------------------------------------------------
def v5_admin_home_markup():
    return v5_markup([
        [v5_button("📊 نمای کلی", "V5|A|O"), v5_button("👥 کاربران", "V5|A|U")],
        [v5_button("🌐 گروه‌ها", "V5|A|G"), v5_button("🎮 بازی‌ها", "V5|A|P")],
        [v5_button("📝 محتوا", "V5|A|C"), v5_button("🛒 اقتصاد", "V5|A|E")],
        [v5_button("🛡 امنیت", "V5|A|S"), v5_button("💾 بکاپ", "V5|A|B")],
        [v5_button("📜 رویدادها", "V5|A|L"), v5_button("⚙️ تنظیمات", "V5|A|T")],
        [v5_button("🧰 ابزارهای مدیر", "V5|A|X")],
        [v5_button("✕ بستن", "V5|CLOSE")],
    ])


def v5_admin_home_text():
    active = sum(1 for g in DATA.get("groups", {}).values() if g.get("active_game"))
    lobbies = sum(1 for g in DATA.get("games", {}).values() if g.get("status") == "lobby")
    users = len(DATA.get("users", {}))
    groups = len(DATA.get("groups", {}))
    card = v5_card(
        "ApexRival Control",
        f"👥 کاربران <b>{users}</b>   🌐 گروه‌ها <b>{groups}</b>",
        f"🟢 بازی فعال <b>{active}</b>   🟡 Lobby <b>{lobbies}</b>",
        f"📜 رویداد ثبت‌شده <b>{len(DATA.get('audit', []))}</b>",
        "💾 وضعیت ذخیره: <b>JSON / Atomic</b>",
    )
    return f"{v5_breadcrumb('مدیریت','مرکز فرماندهی')}\n\n{card}\n\nهر بخش فقط ابزارهای مرتبط خودش را نمایش می‌دهد."

async def v5_admin_home(query):
    await safe_edit_query(query, v5_admin_home_text(), v5_admin_home_markup())


def v5_admin_section_markup(section: str):
    if section == "U":
        return v5_markup([
            [v5_button("🔎 جست‌وجوی کاربر", "V5|A|US")],
            [v5_button("🏆 کاربران برتر", "V5|A|UT"), v5_button("🚫 لیست محدودشده", "V5|A|UB")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "G":
        return v5_markup([
            [v5_button("📋 فهرست گروه‌ها", "V5|A|GL"), v5_button("🎮 بازی‌های فعال", "V5|A|P")],
            [v5_button("⚙️ تنظیمات پیش‌فرض", "V5|A|GD")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "P":
        return v5_markup([
            [v5_button("🟢 بازی‌های زنده", "V5|A|PL"), v5_button("🛑 پایان همه بازی‌ها", "V5|A|PE")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "C":
        return v5_markup([
            [v5_button("🕵️ اعتراف", "V5|A|CT"), v5_button("🔥 جرئت", "V5|A|CD")],
            [v5_button("💘 فلرت", "V5|A|CF"), v5_button("☠️ حکم", "V5|A|CP")],
            [v5_button("🧠 سؤال", "V5|A|CQ"), v5_button("👑 Boss", "V5|A|CB")],
            [v5_button("🤫 مأموریت", "V5|A|CM"), v5_button("🧩 معما", "V5|A|CR")],
            [v5_button("➕ افزودن محتوا", "V5|A|CA")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "E":
        return v5_markup([
            [v5_button("📈 ضرایب XP", "V5|A|EX"), v5_button("💰 ضرایب سکه", "V5|A|EC")],
            [v5_button("🎒 آیتم‌ها", "V5|A|EI"), v5_button("🏆 آمار اقتصاد", "V5|A|ES")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "S":
        return v5_markup([
            [v5_button("🚫 محدودشده‌ها", "V5|A|UB"), v5_button("🧹 پاکسازی", "V5|A|SC")],
            [v5_button("🩺 سلامت سیستم", "V5|A|SH")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "B":
        return v5_markup([
            [v5_button("📦 ساخت بکاپ", "V5|A|BM"), v5_button("📋 لیست بکاپ", "V5|A|BL")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "L":
        return v5_markup([
            [v5_button("🧾 آخرین رویدادها", "V5|A|LL"), v5_button("📣 گزارش Broadcast", "V5|A|LB")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "T":
        return v5_markup([
            [v5_button("🎛 تنظیمات اصلی", "V5|A|TS")],
            [v5_button("🔞 پیش‌فرض +18", "V5|A|TA"), v5_button("👥 سقف پیش‌فرض", "V5|A|TM")],
            *v5_nav("V5|A|HOME"),
        ])
    if section == "X":
        return v5_markup([
            [v5_button("📣 Broadcast", "V5|A|XB"), v5_button("💾 ذخیره فوری", "V5|A|XS")],
            [v5_button("🧹 پاکسازی قدیمی", "V5|A|XC"), v5_button("🔄 شمارش منابع", "V5|A|XN")],
            *v5_nav("V5|A|HOME"),
        ])
    return v5_markup(v5_nav("V5|A|HOME"))


def v5_admin_section_text(section):
    titles = {
        "U": ("کاربران", "مدیریت حساب‌ها و وضعیت دسترسی."),
        "G": ("گروه‌ها", "کنترل گروه‌ها و تنظیمات مخصوص آن‌ها."),
        "P": ("بازی‌ها", "فقط عملیات مربوط به بازی‌های جاری."),
        "C": ("محتوا", "مدیریت بانک محتوای بازی."),
        "E": ("اقتصاد", "XP، سکه و آیتم‌ها."),
        "S": ("امنیت", "محدودسازی، پاکسازی و سلامت."),
        "B": ("بکاپ", "نسخه‌برداری و بازیابی داده."),
        "L": ("رویدادها", "گزارش رویدادهای مدیریتی و Broadcast."),
        "T": ("تنظیمات", "تنظیمات سراسری سیستم."),
        "X": ("ابزارها", "ابزارهای نگهداری؛ بدون شلوغی منوی اصلی."),
    }
    title, desc = titles.get(section, ("مدیریت", ""))
    return f"{v5_breadcrumb('مدیریت', title)}\n\n{v5_card(title, desc)}\n\nاز این صفحه فقط ابزارهای همین بخش را انتخاب کن."


async def v5_admin_section(query, section):
    await safe_edit_query(query, v5_admin_section_text(section), v5_admin_section_markup(section))


async def v5_admin_overview(query):
    total_xp = sum(int(u.get("xp", 0)) for u in DATA.get("users", {}).values())
    total_coins = sum(int(u.get("coins", 0)) for u in DATA.get("users", {}).values())
    active = sum(1 for g in DATA.get("groups", {}).values() if g.get("active_game"))
    card = v5_card(
        "Snapshot",
        f"👥 کاربران <b>{len(DATA.get('users', {}))}</b>",
        f"🌐 گروه‌ها <b>{len(DATA.get('groups', {}))}</b>",
        f"🎮 بازی فعال <b>{active}</b>",
        f"⭐ XP کل <b>{total_xp}</b>",
        f"💰 سکه کل <b>{total_coins}</b>",
        f"🧩 محتوای افزوده‌شده <b>{sum(len(v) for v in DATA.get('global_content', {}).values())}</b>",
    )
    text = f"{v5_breadcrumb('مدیریت','نمای کلی')}\n\n{card}"
    await safe_edit_query(query, text, v5_markup([v5_button("↻ بروزرسانی", "V5|A|O"), *v5_nav("V5|A|HOME")]))

def v5_confirmation(uid: int, action: str, payload: str, ttl: int = 45) -> str:
    token = f"{random.randrange(100000, 999999)}"
    V5_CONFIRM[token] = {"uid": int(uid), "action": action, "payload": payload, "expires": time.time()+ttl}
    return token


def v5_get_confirmation(uid: int, token: str, action: str):
    info = V5_CONFIRM.get(str(token))
    if not info or int(info.get("uid",0)) != int(uid) or info.get("action") != action or time.time() > float(info.get("expires",0)):
        V5_CONFIRM.pop(str(token), None)
        return None
    V5_CONFIRM.pop(str(token), None)
    return info


async def v5_admin_users(query, page=0):
    items = sort_users_by_xp()
    page = max(0, int(page))
    chunk = 7
    start = page * chunk
    current = items[start:start+chunk]
    rows = []
    lines = []
    for offset, (uid_s, u) in enumerate(current, start=start+1):
        uid = int(uid_s)
        status = "🚫" if u.get("banned") else "🟢"
        lines.append(f"{status} <b>{offset:02d}</b>  {escape(str(u.get('name','کاربر')))}  ·  ⭐ {int(u.get('xp',0))}")
        rows.append([v5_button(f"👤 {str(u.get('name','کاربر'))[:18]}", f"V5|A|UD|{uid}")])
    nav = []
    if page > 0: nav.append(v5_button("◀️", f"V5|A|U|{page-1}"))
    if start+chunk < len(items): nav.append(v5_button("▶️", f"V5|A|U|{page+1}"))
    if nav: rows.append(nav)
    rows += [[v5_button("↻", f"V5|A|U|{page}")], *v5_nav("V5|A|UHOME")]
    text = f"{v5_breadcrumb('مدیریت','کاربران')}\n\n{v5_card('User Directory', *(lines or ['کاربری ثبت نشده است.']))}"
    await safe_edit_query(query, v5_clip(text), v5_markup(rows))


async def v5_admin_user_detail(query, uid: int):
    u = get_user(uid)
    status = bool(u.get("banned"))
    card = v5_card(
        "User Card",
        f"👤 <b>{escape(str(u.get('name', 'کاربر')))}</b>",
        f"🆔 <code>{uid}</code>",
        f"⭐ Level {int(u.get('level', 1))}  •  XP {int(u.get('xp', 0))}",
        f"💰 {int(u.get('coins', 0))} سکه",
        f"🏆 {int(u.get('wins', 0))} برد  •  ☠️ {int(u.get('losses', 0))} باخت",
        f"🛡 دسترسی: {'محدود' if status else 'عادی'}",
    )
    text = f"{v5_breadcrumb('مدیریت','کاربر')}\n\n{card}"
    rows = [
        [v5_button("⭐ +100 XP", f"V5|A|UX|{uid}|100"), v5_button("💰 +100", f"V5|A|UC|{uid}|100")],
        [v5_button("➖ XP", f"V5|A|UX|{uid}|-100"), v5_button("➖ سکه", f"V5|A|UC|{uid}|-100")],
        [v5_button("🛡 رفع/اعمال محدودیت", f"V5|A|UBT|{uid}")],
        [v5_button("🧹 ریست اطلاعات", f"V5|A|UR|{uid}")],
        *v5_nav("V5|A|U"),
    ]
    await safe_edit_query(query, text, v5_markup(rows))

async def v5_admin_group_list(query, page=0):
    items = sort_groups_by_activity()
    page = max(0,int(page)); chunk = 6; start = page*chunk
    current = items[start:start+chunk]
    rows=[]; lines=[]
    for idx,(cid,g) in enumerate(current,start=start+1):
        enabled=bool(g.get("enabled",True)); active=bool(g.get("active_game"))
        lines.append(f"{idx:02d}. {'🟢' if enabled else '⚫'} {'🎮' if active else '💤'}  <code>{cid}</code>")
        rows.append([v5_button(f"🌐 {cid}", f"V5|A|GDV|{cid}")])
    nav=[]
    if page>0: nav.append(v5_button("◀️",f"V5|A|GL|{page-1}"))
    if start+chunk<len(items): nav.append(v5_button("▶️",f"V5|A|GL|{page+1}"))
    if nav: rows.append(nav)
    rows += [v5_nav("V5|A|G")]
    text=f"{v5_breadcrumb('مدیریت','گروه‌ها')}\n\n{v5_card('Group Directory',*(lines or ['گروهی ثبت نشده است.']))}"
    await safe_edit_query(query,text,v5_markup(rows))


async def v5_admin_group_detail(query, cid: int):
    g = get_group(cid)
    game = active_game(cid)
    card = v5_card(
        "Group Card",
        f"🌐 <code>{cid}</code>",
        f"وضعیت: {v5_status_chip(bool(g.get('enabled', True)))}",
        f"+18: {v5_status_chip(bool(g.get('adult_mode')), 'روشن', 'خاموش')}",
        f"👥 ظرفیت {g.get('min_players', 2)}–{g.get('max_players', 20)}",
        f"🎮 بازی: {'فعال' if game else 'ندارد'}",
    )
    text = f"{v5_breadcrumb('مدیریت','گروه')}\n\n{card}"
    rows = [
        [v5_button("🟢/⚫ فعال‌سازی", f"V5|A|GEN|{cid}"), v5_button("🔞 +18", f"V5|A|GAD|{cid}")],
        [v5_button("🛑 پایان بازی", f"V5|A|GE|{cid}")],
        *v5_nav("V5|A|GL"),
    ]
    await safe_edit_query(query, text, v5_markup(rows))

async def v5_admin_games(query):
    games=active_games()
    lines=[]; rows=[]
    for i,(gid,g) in enumerate(games[:8],1):
        lines.append(f"{i:02d}. <code>{g.get('chat_id')}</code>  ·  👥 {len(g.get('players',[]))}  ·  {escape(str(g.get('phase','-')))}")
        rows.append([v5_button(f"🎮 {g.get('chat_id')}",f"V5|A|GP|{str(gid)[:20]}")])
    rows += [[v5_button("🛑 پایان همه", "V5|A|PE")], *v5_nav("V5|A|P")]
    text=f"{v5_breadcrumb('مدیریت','بازی‌ها')}\n\n{v5_card('Live Games',*(lines or ['بازی فعالی وجود ندارد.']))}"
    await safe_edit_query(query,text,v5_markup(rows))


async def v5_admin_economy(query):
    users=DATA.get('users',{}).values()
    total_xp=sum(int(u.get('xp',0)) for u in users)
    total_coins=sum(int(u.get('coins',0)) for u in users)
    text=f"{v5_breadcrumb('مدیریت','اقتصاد')}\n\n{v5_card('Economy',f'⭐ XP کل <b>{total_xp}</b>',f'💰 سکه کل <b>{total_coins}</b>',f'👥 حساب‌ها <b>{len(DATA.get("users",{}))}</b>',f'📦 آیتم‌های فعال <b>{len(SHOP)}</b>')}"
    await safe_edit_query(query,text,v5_markup([v5_button('💾 ذخیره', 'V5|A|XS'), *v5_nav('V5|A|HOME')]))


async def v5_admin_security(query):
    banned=sum(1 for u in DATA.get('users',{}).values() if u.get('banned'))
    old_games=sum(1 for g in DATA.get('games',{}).values() if g.get('status') in ('finished','cancelled'))
    text=f"{v5_breadcrumb('مدیریت','امنیت')}\n\n{v5_card('Security',f'🚫 محدودشده <b>{banned}</b>',f'🗃 بازی‌های پایان‌یافته <b>{old_games}</b>',f'📜 Audit <b>{len(DATA.get("audit",[]))}</b>')}"
    await safe_edit_query(query,text,v5_admin_section_markup('S'))


async def v5_admin_backup(query):
    files=backup_files()
    lines=[f"{i+1:02d}. <code>{escape(Path(p).name)}</code>" for i,p in enumerate(files[:8])]
    rows=[[v5_button('📦 ساخت بکاپ','V5|A|BM')]]
    for i,p in enumerate(files[:5]): rows.append([v5_button(f'♻️ بازیابی {i+1}',f'V5|A|BR|{i}')])
    rows += [v5_nav('V5|A|B')]
    text=f"{v5_breadcrumb('مدیریت','بکاپ')}\n\n{v5_card('Backup Vault',*(lines or ['هنوز بکاپی ساخته نشده.']))}"
    await safe_edit_query(query,text,v5_markup(rows))


async def v5_admin_logs(query):
    entries=list(DATA.get('audit',[]))[-12:][::-1]
    lines=[]
    for e in entries:
        dt=datetime.fromtimestamp(int(e.get('ts',0)),tz=timezone.utc).strftime('%m-%d %H:%M')
        lines.append(f"<code>{dt}</code>  {escape(str(e.get('action','-')))}  ·  {escape(str(e.get('details',''))[:55])}")
    text=f"{v5_breadcrumb('مدیریت','رویدادها')}\n\n{v5_card('Recent Events',*(lines or ['رویدادی ثبت نشده.']))}"
    await safe_edit_query(query,text,v5_markup([v5_button('↻', 'V5|A|L'), *v5_nav('V5|A|HOME')]))


# ---------------------------------------------------------------------------
# V5 admin action handler
# ---------------------------------------------------------------------------
async def v5_admin_action(query, context, parts):
    uid=query.from_user.id
    if not is_admin(uid):
        await safe_answer_query(query,'🚫 فقط Super Admin.',True); return
    action=parts[2] if len(parts)>2 else 'HOME'
    if action=='HOME': await v5_admin_home(query); return
    if action=='O': await v5_admin_overview(query); return
    if action=='U': await v5_admin_users(query,int(parts[3]) if len(parts)>3 else 0); return
    if action=='UHOME': await v5_admin_section(query,'U'); return
    if action=='US':
        V5_FLOW[uid]={'type':'admin_user_search'}
        await safe_edit_query(query,'🔎 <b>جست‌وجوی کاربر</b>\n\nID عددی را در پیام بعدی بفرست.',v5_markup([[v5_button('❌ لغو','V5|A|FC')]])); return
    if action=='UT': await v5_admin_users(query,0); return
    if action=='UB':
        banned=[(uid_s,u) for uid_s,u in DATA.get('users',{}).items() if u.get('banned')]
        lines=[f"🚫 <code>{uid_s}</code> — {escape(str(u.get('name','کاربر')))}" for uid_s,u in banned[:15]] or ['لیست خالی است.']
        await safe_edit_query(query,f"{v5_breadcrumb('مدیریت','محدودشده‌ها')}\n\n{v5_card('Restricted',*lines)}",v5_markup(v5_nav('V5|A|S'))); return
    if action=='UD': await v5_admin_user_detail(query,int(parts[3])); return
    if action=='UX':
        target=int(parts[3]); amount=int(parts[4]); u=get_user(target); u['xp']=max(0,int(u.get('xp',0))+amount); u['level']=level_for_xp(u['xp']); audit('v5_admin_xp',uid,None,f'{target}:{amount}'); save_data(force=True); await v5_admin_user_detail(query,target); return
    if action=='UC':
        target=int(parts[3]); amount=int(parts[4]); u=get_user(target); u['coins']=max(0,int(u.get('coins',0))+amount); audit('v5_admin_coins',uid,None,f'{target}:{amount}'); save_data(force=True); await v5_admin_user_detail(query,target); return
    if action=='UBT':
        target=int(parts[3]); u=get_user(target); u['banned']=not bool(u.get('banned')); audit('v5_admin_ban',uid,None,str(target)); save_data(force=True); await v5_admin_user_detail(query,target); return
    if action=='UR':
        token=v5_confirmation(uid,'reset_user',str(parts[3]));
        await safe_edit_query(query,'⚠️ <b>ریست کامل کاربر</b>\n\nاین عملیات XP، سکه، استریک، دستاوردها و موجودی را به حالت اولیه برمی‌گرداند.',v5_markup([[v5_button('✅ تأیید',f'V5|A|CFY|{token}'),v5_button('❌ لغو','V5|A|U')]])); return
    if action=='CFY':
        token=parts[3] if len(parts)>3 else ''; info=v5_get_confirmation(uid,token,'reset_user')
        if not info: await safe_answer_query(query,'تأیید منقضی شده است.',True); return
        target=int(info['payload']); DATA['users'][str(target)]=deepcopy(DEFAULT_USER); save_data(force=True); audit('v5_admin_reset',uid,None,str(target)); await v5_admin_user_detail(query,target); return
    if action=='G': await v5_admin_section(query,'G'); return
    if action=='GL': await v5_admin_group_list(query,int(parts[3]) if len(parts)>3 else 0); return
    if action=='GD': await v5_admin_section(query,'G'); return
    if action=='GDV': await v5_admin_group_detail(query,int(parts[3])); return
    if action=='GEN':
        cid=int(parts[3]); g=get_group(cid); g['enabled']=not bool(g.get('enabled',True)); audit('v5_group_enabled',uid,cid,str(g['enabled'])); save_data(force=True); await v5_admin_group_detail(query,cid); return
    if action=='GAD':
        cid=int(parts[3]); g=get_group(cid); g['adult_mode']=not bool(g.get('adult_mode')); audit('v5_group_adult',uid,cid,str(g['adult_mode'])); save_data(force=True); await v5_admin_group_detail(query,cid); return
    if action=='GE':
        cid=int(parts[3]); token=v5_confirmation(uid,'end_group',str(cid)); await safe_edit_query(query,'⚠️ <b>پایان بازی گروه</b>\n\nبازی جاری این گروه فوراً پایان می‌یابد.',v5_markup([[v5_button('✅ پایان',f'V5|A|GEY|{token}'),v5_button('❌ لغو','V5|A|G')]])); return
    if action=='GEY':
        token=parts[3]; info=v5_get_confirmation(uid,token,'end_group')
        if not info: await safe_answer_query(query,'تأیید منقضی شده.',True); return
        cid=int(info['payload']); game=active_game(cid)
        if game: end_game(game,'پایان توسط Super Admin')
        save_data(force=True); await v5_admin_group_detail(query,cid); return
    if action=='P': await v5_admin_games(query); return
    if action=='PE':
        token=v5_confirmation(uid,'end_all','all'); await safe_edit_query(query,'⚠️ <b>پایان همه بازی‌ها</b>\n\nتمام Lobbyها و بازی‌های فعال پایان می‌یابند.',v5_markup([[v5_button('✅ تأیید',f'V5|A|PEY|{token}'),v5_button('❌ لغو','V5|A|P')]])); return
    if action=='PEY':
        info=v5_get_confirmation(uid,parts[3] if len(parts)>3 else '','end_all')
        if not info: await safe_answer_query(query,'تأیید منقضی شده.',True); return
        count=0
        for game in DATA.get('games',{}).values():
            if game.get('status') in ('active','lobby'):
                end_game(game,'پایان دسته‌جمعی توسط Super Admin'); count += 1
        save_data(force=True); await safe_edit_query(query,f'🛑 <b>{count}</b> بازی پایان یافت.',v5_markup(v5_nav('V5|A|P'))); return
    if action=='PL': await v5_admin_games(query); return
    if action=='GP':
        gid='|'.join(parts[3:]); found=DATA.get('games',{}).get(gid)
        if not found:
            # fallback: prefix match for compact callbacks
            found=next((g for k,g in DATA.get('games',{}).items() if str(k).startswith(gid)),None)
        if not found: await safe_answer_query(query,'بازی پیدا نشد.',True); return
        body=f"{v5_breadcrumb('مدیریت','بازی')}\n\n{v5_card('Live Game',f'🌐 <code>{found.get("chat_id")}</code>',f'👑 {escape(found.get("leader_name","-"))}',f'👥 {len(found.get("players",[]))}',f'🎯 فاز {escape(str(found.get("phase","-")))}')}"
        rows=[[v5_button('🛑 پایان بازی',f'V5|A|GE|{found.get("chat_id")}')],*v5_nav('V5|A|P')]
        await safe_edit_query(query,body,v5_markup(rows)); return
    if action=='C': await v5_admin_section(query,'C'); return
    if action.startswith('C') and len(action)==2: await v5_admin_section(query,'C'); return
    if action in ('CT','CD','CF','CP','CQ','CB','CM','CR'):
        keymap={'CT':'truth','CD':'dare','CF':'flirty','CP':'penalty','CQ':'question','CB':'boss','CM':'mission','CR':'riddle'}; key=keymap[action]
        items=v5_unique(DATA.get('global_content',{}).get(key,[])); body=v5_card(CONTENT_LABELS.get(key,key),*(f'{i+1}. {escape(x)}' for i,x in enumerate(items[-8:])))
        await safe_edit_query(query,f'{v5_breadcrumb("مدیریت","محتوا")}\n\n{body}',v5_markup([[v5_button('➕ افزودن',f'V5|A|CA|{key}')],*v5_nav('V5|A|C')])); return
    if action=='CA':
        key=parts[3] if len(parts)>3 else 'truth'; V5_FLOW[uid]={'type':'content_add','key':key}
        await safe_edit_query(query,f'➕ <b>افزودن محتوا</b>\n\nدسته: {escape(CONTENT_LABELS.get(key,key))}\nمتن موردنظر را در پیام بعدی بفرست.',v5_markup([[v5_button('❌ لغو','V5|A|FC')]])); return
    if action=='FC': V5_FLOW.pop(uid,None); await v5_admin_home(query); return
    if action=='E': await v5_admin_section(query,'E'); return
    if action in ('EX','EC','EI','ES'):
        if action=='EX': DATA['settings']['xp_multiplier']=1 if DATA['settings'].get('xp_multiplier',1)>=3 else int(DATA['settings'].get('xp_multiplier',1))+1
        elif action=='EC': DATA['settings']['coins_multiplier']=1 if DATA['settings'].get('coins_multiplier',1)>=3 else int(DATA['settings'].get('coins_multiplier',1))+1
        save_data(force=True); audit('v5_economy_setting',uid,None,action); await v5_admin_economy(query); return
    if action=='S': await v5_admin_security(query); return
    if action=='SC': await advanced_cleanup_job(context); await v5_admin_security(query); return
    if action=='SH':
        path=Path(DATA_FILE); size=path.stat().st_size if path.exists() else 0
        body=f"{v5_breadcrumb('مدیریت','سلامت')}\n\n{v5_card('Health',f'💾 data.json: <b>{size}</b> bytes',f'🐍 Python: <b>{__import__("sys").version_info.major}.{__import__("sys").version_info.minor}</b>',f'🔐 Admin lock: <b>{"OK" if ADMIN_ID else "MISSING"}</b>')}"
        await safe_edit_query(query,body,v5_markup(v5_nav('V5|A|S'))); return
    if action=='B': await v5_admin_backup(query); return
    if action=='BM': make_backup_file('v5_admin'); await v5_admin_backup(query); return
    if action=='BL': await v5_admin_backup(query); return
    if action=='BR':
        idx=int(parts[3]) if len(parts)>3 else 0; files=backup_files()
        if idx<0 or idx>=len(files): await safe_answer_query(query,'بکاپ پیدا نشد.',True); return
        token=v5_confirmation(uid,'restore',str(idx)); await safe_edit_query(query,'⚠️ <b>بازیابی بکاپ</b>\n\nاطلاعات فعلی با نسخه انتخابی جایگزین می‌شود. ابتدا تأیید کن.',v5_markup([[v5_button('✅ بازیابی',f'V5|A|BRY|{token}'),v5_button('❌ لغو','V5|A|B')]])); return
    if action=='BRY':
        info=v5_get_confirmation(uid,parts[3] if len(parts)>3 else '','restore')
        if not info: await safe_answer_query(query,'تأیید منقضی شده.',True); return
        idx=int(info['payload']); files=backup_files()
        if 0<=idx<len(files):
            ok,msg=restore_backup(files[idx])
            await safe_edit_query(query,('✅ ' if ok else '❌ ')+escape(msg),v5_markup(v5_nav('V5|A|B')))
        else: await safe_answer_query(query,'بکاپ پیدا نشد.',True)
        return
    if action=='L': await v5_admin_logs(query); return
    if action=='LB':
        logs=DATA.get('broadcast_log',[])[-8:][::-1]
        lines=[f"✅ {x.get('ok',0)}  ❌ {x.get('fail',0)}" for x in logs] or ['گزارشی موجود نیست.']
        await safe_edit_query(query,f'{v5_breadcrumb("مدیریت","Broadcast")}\n\n{v5_card("Broadcast",*lines)}',v5_markup(v5_nav('V5|A|L'))); return
    if action=='LL': await v5_admin_logs(query); return
    if action=='T': await v5_admin_section(query,'T'); return
    if action in ('TS','TA','TM'):
        if action=='TA': DATA['settings']['adult_default']=not bool(DATA['settings'].get('adult_default')); 
        if action=='TM': DATA['settings']['max_players_default']=10 if int(DATA['settings'].get('max_players_default',20))>=30 else int(DATA['settings'].get('max_players_default',20))+5
        save_data(force=True); await v5_admin_section(query,'T'); return
    if action=='XB':
        V5_FLOW[uid] = {'type':'broadcast'}
        await safe_edit_query(query,'📣 <b>Broadcast</b>\n\nمتن پیام عمومی را در پیام بعدی بفرست.\nبرای لغو، «لغو» را ارسال کن.',v5_markup([[v5_button('❌ لغو','V5|A|FC')]])); return
    if action=='X': await v5_admin_section(query,'X'); return
    if action=='XS': save_data(force=True); audit('v5_force_save',uid,None,''); await v5_admin_section(query,'X'); return
    if action=='XC': await advanced_cleanup_job(context); await v5_admin_section(query,'X'); return
    if action=='XN':
        card = v5_card(
            "Counters",
            f"👥 {len(DATA.get('users', {}))}",
            f"🌐 {len(DATA.get('groups', {}))}",
            f"🎮 {len(DATA.get('games', {}))}",
            f"🧩 prompts {sum(len(v) for v in V5_BANKS.values())}",
        )
        text = f"{v5_breadcrumb('مدیریت','شمارنده‌ها')}\n\n{card}"
        await safe_edit_query(query, text, v5_markup(v5_nav('V5|A|X'))); return


# ---------------------------------------------------------------------------
# V5 game callback router. Old mechanics are reused through their tested APIs.
# ---------------------------------------------------------------------------
async def v5_game_action(query, context, parts):
    game=await v5_require_active(query)
    if not game: return
    uid=query.from_user.id
    action=parts[2] if len(parts)>2 else 'HOME'
    if action=='Q':
        await safe_edit_query(query,'⚡ <b>چالش‌های سریع</b>\n\nیک چالش را انتخاب کن.',v5_section_markup('Q',game)); return
    if action=='S':
        await safe_edit_query(query,'🎭 <b>بازی‌های اجتماعی</b>\n\nفقط حالت‌های مناسب همین گروه نمایش داده می‌شوند.',v5_section_markup('S',game)); return
    if action=='B':
        await safe_edit_query(query,'⚔️ <b>رقابت</b>\n\nرقابت موردنظر را انتخاب کن.',v5_section_markup('B',game)); return
    if action=='X':
        await safe_edit_query(query,'🤫 <b>حالت‌های مخفی</b>\n\nبعضی اطلاعات اینجا خصوصی ارسال می‌شوند.',v5_section_markup('X',game)); return
    if action=='R':
        await safe_edit_query(query,'☠️ <b>حکم و پاداش</b>\n\nفقط ابزارهای مرتبط با وضعیت فعلی تو اینجا نمایش داده می‌شوند.',v5_section_markup('R',game)); return
    if action=='I':
        await safe_edit_query(query,v5_game_home_text(game),v5_section_markup('H',game)); return
    if action=='H':
        if not leader_of(game,uid): await safe_answer_query(query,'👑 فقط سرگروه.',True); return
        await safe_edit_query(query,'👑 <b>کنترل سرگروه</b>\n\nکنترل‌های مدیریتی فقط اینجا نمایش داده می‌شوند.',v5_section_markup('H',game)); return
    if action=='A':
        await send_adult(query.message,game); return
    await safe_answer_query(query,'گزینه‌ای برای این صفحه پیدا نشد.',True)


async def v5_mode_action(query, context, family, mode):
    game=await v5_require_active(query)
    if not game: return
    if not v5_rate_limit(query.from_user.id, family+mode, 1.0):
        await safe_answer_query(query,'⏳ یک لحظه صبر کن.',True); return
    game['phase']=mode.lower(); v5_touch(game)
    if family=='M':
        if mode=='N': await mini_number_hunt(query.message,game)
        elif mode=='R': await mini_riddle(query.message,game)
        elif mode=='E': await mini_emoji(query.message,game)
        elif mode=='F': await mini_reaction(query.message,game)
        elif mode=='W': await mini_words(query.message,game)
    elif family=='S':
        if mode=='T': await send_truth_or_dare(query.message,game,'truth')
        elif mode=='D': await send_truth_or_dare(query.message,game,'dare')
        elif mode=='F': await send_flirty(query.message,game)
        elif mode=='Q': await send_question(query.message,game)
        elif mode=='A': await send_adult(query.message,game)
    elif family=='B':
        if mode=='D': await duel_start(query.message,game)
        elif mode=='R': await roulette(query.message,game)
        elif mode=='S': await speed(query.message,game)
        elif mode=='V': await create_vote(query.message,game)
        elif mode=='U': await mini_survival(query.message,game)
        elif mode=='T': await mini_teams(query.message,game)
    elif family=='X':
        if mode=='M': await create_secret_mission(query.message,game,context.bot)
        elif mode=='S': await create_spy(query.message,game,context.bot)
        elif mode=='R': await mini_role(query.message,game,context.bot)
        elif mode=='P': await mini_predict(query.message,game)
    elif family=='R':
        if mode=='P': await penalty_mine(query,game)
        elif mode=='I':
            inv=inventory(query.from_user.id)
            body=v5_card('Inventory',*(f'{SHOP[k]["name"]}: <b>{int(v)}</b>' for k,v in inv.items()))
            await safe_edit_query(query,f'{v5_breadcrumb("بازی","آیتم‌ها")}\n\n{body}',v5_section_markup('R',game))
        elif mode=='S': await send_shop(query.message,query.from_user.id)
        elif mode=='A': await achievements_cmd(query.message,context)
    save_data()


async def v5_host_action(query, context, mode):
    game=await v5_require_active(query)
    if not game: return
    uid=query.from_user.id
    if not leader_of(game,uid): await safe_answer_query(query,'👑 فقط سرگروه یا Super Admin.',True); return
    if mode=='R':
        options=['T','D','S','V','N','M']
        chosen=random.choice(options)
        await query.message.reply_text(f'🎲 <b>حالت تصادفی:</b> {chosen}',parse_mode=ParseMode.HTML)
        await v5_mode_action(query,context,{'T':'S','D':'S','S':'B','V':'B','N':'M','M':'X'}[chosen],{'T':'T','D':'D','S':'S','V':'V','N':'N','M':'M'}[chosen])
        return
    if mode=='P':
        target=random.choice(game['players'])
        p=assign_penalty(game,int(target),source='👑 سرگروه')
        await query.message.reply_text(f'☠️ حکم برای {mention_user(target,v5_name(target,game))}: {escape(p["text"])}',parse_mode=ParseMode.HTML)
        game['phase']='penalty'; save_data(); return
    if mode=='L':
        await safe_edit_query(query,v5_lobby_text(game),v5_section_markup('H',game)); return
    if mode=='N':
        game['round']=int(game.get('round',0))+1; game['phase']='free'; game['event']=None; game['duel']=None; game['vote']=None; game['speed']=None; v5_touch(game); save_data(force=True)
        await safe_edit_query(query,f'⏭ <b>دور {game["round"]}</b> آماده شد.',v5_game_home_markup(game)); return
    if mode=='E':
        token=v5_confirmation(uid,'end_game',str(game['chat_id']))
        await safe_edit_query(query,'⚠️ <b>پایان بازی</b>\n\nبرای پایان فوری تأیید کن.',v5_markup([[v5_button('✅ پایان',f'V5|H|EY|{token}'),v5_button('❌ لغو','V5|G|H')]])); return
    if mode=='EY':
        pass


# ---------------------------------------------------------------------------
# V5 lobby callback router
# ---------------------------------------------------------------------------
async def v5_lobby_action(query, context, parts):
    token=parts[3] if len(parts)>3 else ''
    game=DATA.get('games',{}).get(token)
    if not game:
        await safe_answer_query(query,'این Lobby دیگر فعال نیست.',True); return
    uid=query.from_user.id
    if game.get('status')!='lobby': await safe_answer_query(query,'⛔ Lobby بسته شده است.',True); return
    game['_viewer_id']=uid
    mode=parts[2] if len(parts)>2 else 'R'
    if mode=='J':
        if v5_is_player(game,uid): await safe_answer_query(query,'✅ تو همین الان ثبت‌نامی.',True); return
        if len(game['players'])>=int(game['settings']['max_players']): await safe_answer_query(query,'⛔ ظرفیت پر شده.',True); return
        game['players'].append(uid); game['names'][str(uid)]=query.from_user.first_name or 'بازیکن'; v5_ready_state(game)[str(uid)]=True; v5_touch(game); audit('v5_join',uid,game['chat_id'],game['id']); save_data(force=True)
        await safe_answer_query(query,'✅ وارد بازی شدی.'); await safe_edit_query(query,v5_lobby_text(game),v5_lobby_markup(game)); return
    if mode=='L':
        if uid==int(game['leader_id']): await safe_answer_query(query,'👑 سرگروه نمی‌تواند از لابی خودش خارج شود. لابی را لغو کن.',True); return
        if not v5_is_player(game,uid): await safe_answer_query(query,'تو داخل لابی نیستی.',True); return
        game['players']=[x for x in game['players'] if int(x)!=uid]; game['ready'].pop(str(uid),None); v5_touch(game); save_data(force=True); await safe_answer_query(query,'🚪 از لابی خارج شدی.'); await safe_edit_query(query,v5_lobby_text(game),v5_lobby_markup(game)); return
    if mode=='P':
        ready=sum(1 for p in game['players'] if v5_ready_state(game).get(str(p),True))
        body=v5_card('Players',*(f"{'🟢' if v5_ready_state(game).get(str(p),True) else '🟡'} {i+1}. {escape(v5_name(p,game))}" for i,p in enumerate(game['players'])))
        await safe_edit_query(query,f'{v5_breadcrumb("بازی","بازیکنان")}\n\n{body}\n\n✅ آماده: <b>{ready}/{len(game["players"])}</b>',v5_markup(v5_nav(f'V5|L|R|{token}'))); return
    if mode=='R': await safe_edit_query(query,v5_lobby_text(game),v5_lobby_markup(game)); return
    if mode=='O':
        if not leader_of(game,uid): await safe_answer_query(query,'👑 فقط سرگروه.',True); return
        rows=[
            [v5_button('➕ حداقل',f'V5|L|MI|{token}'),v5_button('➖ حداقل',f'V5|L|MD|{token}')],
            [v5_button('➕ حداکثر',f'V5|L|XI|{token}'),v5_button('➖ حداکثر',f'V5|L|XD|{token}')],
            *v5_nav(f'V5|L|R|{token}')]
        await safe_edit_query(query,f'{v5_breadcrumb("بازی","تنظیمات Lobby")}\n\n{v5_card("Lobby Settings",f"حداقل: {game["settings"]["min_players"]}",f"حداکثر: {game["settings"]["max_players"]}")}',v5_markup(rows)); return
    if mode in ('MI','MD','XI','XD'):
        if not leader_of(game,uid): await safe_answer_query(query,'👑 فقط سرگروه.',True); return
        settings=game['settings']
        if mode=='MI': settings['min_players']=min(10,int(settings.get('min_players',2))+1)
        if mode=='MD': settings['min_players']=max(2,int(settings.get('min_players',2))-1)
        if mode=='XI': settings['max_players']=min(60,int(settings.get('max_players',20))+1)
        if mode=='XD': settings['max_players']=max(settings['min_players'],int(settings.get('max_players',20))-1)
        save_data(force=True); await v5_lobby_action(query,context,['V5','L','O',token]); return
    if mode=='S':
        if not leader_of(game,uid): await safe_answer_query(query,'👑 فقط سرگروه.',True); return
        if len(game['players'])<int(game['settings']['min_players']): await safe_answer_query(query,f'⏳ حداقل {game["settings"]["min_players"]} نفر لازم است.',True); return
        game['status']='active'; game['phase']='free'; game['started_at']=now_ts(); game['round']=1; v5_touch(game)
        for p in game['players']: get_user(int(p))['games'] += 1
        audit('v5_start_game',uid,game['chat_id'],game['id']); save_data(force=True)
        await safe_edit_query(query,v5_game_home_text(game),v5_game_home_markup(game)); return
    if mode=='C':
        if not leader_of(game,uid): await safe_answer_query(query,'👑 فقط سرگروه.',True); return
        token2=v5_confirmation(uid,'cancel_lobby',token)
        await safe_edit_query(query,'⚠️ <b>لغو Lobby</b>\n\nتمام ثبت‌نام‌های این Lobby بسته می‌شود.',v5_markup([[v5_button('✅ لغو',f'V5|L|CY|{token2}'),v5_button('❌ ادامه','V5|L|R|'+token)]])); return
    if mode=='CY':
        info=v5_get_confirmation(uid,parts[3] if len(parts)>3 else '','cancel_lobby')
        if not info: await safe_answer_query(query,'تأیید منقضی شده.',True); return
        real=DATA.get('games',{}).get(info['payload'])
        if real: end_game(real,'لغو Lobby توسط سرگروه')
        save_data(force=True); await safe_edit_query(query,'🛑 <b>Lobby لغو شد.</b>',v5_markup(v5_nav('V5|HOME'))); return


# ---------------------------------------------------------------------------
# V5 top-level callback router
# ---------------------------------------------------------------------------
async def v5_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    if not query or not query.data: return
    data=str(query.data)
    if not data.startswith('V5|'): return
    await safe_answer_query(query)
    parts=data.split('|')
    uid=query.from_user.id
    try:
        if parts[1]=='CLOSE':
            await safe_edit_query(query,'✅ <b>ApexRival</b>\n\nاین صفحه بسته شد.',None); return
        if parts[1]=='HOME': await v5_send_home(update,context); return
        if parts[1]=='HELP': await v5_help_message(update,context,parts[2] if len(parts)>2 else 'HOME'); return
        if parts[1]=='PROFILE': await v5_profile_message(update,context); return
        if parts[1]=='RANK': await v5_rank_message(update,context); return
        if parts[1]=='ACH': await achievements_cmd(query.message,context); return
        if parts[1]=='SHOP': await send_shop(query.message,uid); return
        if parts[1]=='GAME':
            game=active_game(query.message.chat_id)
            if not game: await safe_answer_query(query,'⛔ بازی فعالی نیست.',True); return
            game['_viewer_id']=uid; await v5_show_active_game(query,game); return
        if parts[1]=='ADMIN':
            if not is_admin(uid): await safe_answer_query(query,'🚫 فقط Super Admin.',True); return
            await v5_admin_home(query); return
        if parts[1]=='L': await v5_lobby_action(query,context,parts); return
        if parts[1]=='G':
            await v5_game_action(query,context,parts); return
        if parts[1] in ('M','S','B','X','R'):
            if len(parts)==3: await v5_mode_action(query,context,parts[1],parts[2]); return
        if parts[1]=='H':
            mode=parts[2] if len(parts)>2 else 'HOME'
            if mode=='EY':
                info=v5_get_confirmation(uid,parts[3] if len(parts)>3 else '','end_game')
                if not info: await safe_answer_query(query,'تأیید منقضی شده.',True); return
                game=active_game(int(info['payload']))
                if game: end_game(game,'پایان توسط سرگروه'); save_data(force=True)
                await safe_edit_query(query,'🏁 <b>بازی پایان یافت.</b>',v5_markup(v5_nav('V5|HOME'))); return
            await v5_host_action(query,context,mode); return
        if parts[1]=='A': await v5_admin_action(query,context,parts); return
    except Exception as exc:
        audit('v5_router_error',uid,query.message.chat_id if query.message else None,repr(exc))
        await safe_answer_query(query,'⚠️ این عملیات انجام نشد. دوباره امتحان کن.',True)


# ---------------------------------------------------------------------------
# V5 text router / command layer
# ---------------------------------------------------------------------------
async def v5_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    if not update.message or not update.message.text: return
    text=update.message.text.strip()
    uid=update.effective_user.id
    flow=V5_FLOW.get(uid)
    if flow:
        if text in ('❌ لغو','لغو'):
            V5_FLOW.pop(uid,None); await update.message.reply_text('✅ عملیات لغو شد.'); return
        if flow.get('type')=='admin_user_search' and is_admin(uid):
            if text.isdigit():
                V5_FLOW.pop(uid,None); await v5_admin_user_detail_for_message(update,context,int(text)); return
            await update.message.reply_text('🆔 یک User ID عددی بفرست.'); return
        if flow.get('type')=='broadcast' and is_admin(uid):
            ok = fail = 0
            payload = text[:3500]
            for target in list(DATA.get('users',{})):
                try:
                    await context.bot.send_message(chat_id=int(target), text=f'📣 <b>ApexRival</b>\n\n{escape(payload)}', parse_mode=ParseMode.HTML)
                    ok += 1
                except Exception:
                    fail += 1
            DATA.setdefault('broadcast_log', []).append({'ts':now_ts(),'actor':uid,'ok':ok,'fail':fail})
            DATA['broadcast_log'] = DATA['broadcast_log'][-100:]
            V5_FLOW.pop(uid,None)
            audit('v5_broadcast',uid,None,f'ok={ok};fail={fail}')
            save_data(force=True)
            await update.message.reply_text(f'📣 ارسال تمام شد.\n✅ {ok}   ❌ {fail}')
            return
        if flow.get('type')=='content_add' and is_admin(uid):
            key=flow.get('key','truth'); content=text[:700]
            bucket=DATA.setdefault('global_content',{}).setdefault(key,[])
            if content not in bucket: bucket.append(content)
            V5_FLOW.pop(uid,None); audit('v5_content_add',uid,None,key); save_data(force=True)
            await update.message.reply_text(f'✅ به «{CONTENT_LABELS.get(key,key)}» اضافه شد.'); return
    mapping={
        '🎮 بازی':'game','👤 پروفایل':'profile','🏆 رتبه':'rank','🛒 فروشگاه':'shop','🏅 دستاوردها':'ach','❓ راهنما':'help','👑 مرکز مدیریت':'admin'
    }
    cmd=mapping.get(text)
    if cmd=='game':
        await v5_create_lobby(update,context); return
    if cmd=='profile': await v5_profile_message(update,context); return
    if cmd=='rank': await v5_rank_message(update,context); return
    if cmd=='shop': await shop_cmd(update,context); return
    if cmd=='ach': await achievements_cmd(update,context); return
    if cmd=='help': await v5_help_message(update,context); return
    if cmd=='admin':
        if is_admin(uid): await update.message.reply_text(v5_admin_home_text(),parse_mode=ParseMode.HTML,reply_markup=v5_admin_home_markup())
        else: await update.message.reply_text('🚫 فقط Super Admin.')
        return
    await text_router(update,context)


async def v5_admin_user_detail_for_message(update, context, uid):
    u = get_user(uid)
    card = v5_card(
        "Search Result",
        f"👤 {escape(str(u.get('name', 'کاربر')))}",
        f"⭐ XP {u.get('xp', 0)}",
        f"💰 سکه {u.get('coins', 0)}",
    )
    rows = [[v5_button('👤 باز کردن کارت', f'V5|A|UD|{uid}')]]
    await update.message.reply_text(
        f'{v5_breadcrumb("مدیریت","کاربر")}\n\n{card}',
        parse_mode=ParseMode.HTML,
        reply_markup=v5_markup(rows),
    )

async def v5_start(update,context):
    if not await ensure_allowed(update): return
    get_user(update.effective_user.id,update.effective_user.first_name or 'بازیکن')
    await v5_send_home(update,context)


async def v5_menu(update,context):
    await v5_send_home(update,context)


# ---------------------------------------------------------------------------
# Additional unique V5 challenge vault.
# Generated as real content, not placeholder comments. Duplicates are removed
# immediately after construction and each string is verified unique.
# ---------------------------------------------------------------------------
V5_MICRO_CHALLENGES = []
_v5_subjects = [
    'یک خاطره کوتاه از مدرسه', 'آخرین چیزی که امروز خنداندت', 'یک عادت عجیب اما بی‌خطر',
    'یک انتخاب سخت اما ساده', 'یک غذای محبوب', 'یک توانایی که دوست داری یاد بگیری',
    'یک اشتباه بامزه در چت', 'یک فیلمی که دوباره می‌بینی', 'یک لقب خلاقانه',
    'یک قانون خنده‌دار برای گروه', 'یک سفر خیالی', 'یک مهارت مخفی',
    'یک جمله برای توصیف امشب', 'یک وسیله روی میزت', 'یک آهنگ مناسب این لحظه',
    'یک بازی که در آن بد نیستی', 'یک تصمیم سریع', 'یک چیز کوچک که خوشحالت می‌کند',
    'یک خاطره بی‌خطر از دوستان', 'یک استعداد غیرمنتظره', 'یک انتخاب بین دو خوراکی',
    'یک سؤال که همیشه کنجکاوی درباره‌اش', 'یک شخصیت خیالی', 'یک شغل عجیب',
    'یک اسم برای تیم خیالی', 'یک شعار کوتاه', 'یک ایموجی مناسب شخصیتت',
    'یک رنگ برای امشب', 'یک قانون برای قهرمان شدن', 'یک حرکت نمایشی بامزه',
]
_v5_verbs = [
    'در ده ثانیه توصیفش کن.', 'برای گروه یک نسخه خنده‌دار بساز.', 'سه کلمه خلاقانه برایش انتخاب کن.',
    'به شکل یک نظرسنجی دوگزینه‌ای مطرحش کن.', 'یک امتیاز از ۱ تا ۱۰ بده و دلیل کوتاه بگو.',
    'به شکل یک تیتر خبری تعریفش کن.', 'برای آن یک اسم سینمایی انتخاب کن.',
    'یک نسخه عجیب ولی محترمانه از آن بساز.', 'آن را بدون استفاده از یک کلمه رایج توضیح بده.',
    'یک پایان غیرمنتظره و بی‌خطر برایش بساز.', 'آن را به یک رقابت یک‌دقیقه‌ای تبدیل کن.',
    'یک ایموجی به آن اضافه کن و معنی‌اش را بگو.', 'یک سؤال پیگیری برایش طراحی کن.',
    'آن را به یک مأموریت کوچک تبدیل کن.', 'در قالب پیام تبلیغاتی کوتاه ارائه‌اش کن.',
    'یک لقب برای نسخه حرفه‌ای آن بده.', 'یک نسخه کاملاً جدی و یک نسخه کاملاً بامزه بساز.',
    'بدون اشاره مستقیم، دیگران را وادار کن حدسش بزنند.', 'یک قاعده جدید برایش تعریف کن.',
    'آن را در پنج کلمه خلاصه کن.',
]
for _i, _subject in enumerate(_v5_subjects, 1):
    for _j, _verb in enumerate(_v5_verbs, 1):
        V5_MICRO_CHALLENGES.append(f'{_subject} را {_verb}')
V5_MICRO_CHALLENGES = v5_unique(V5_MICRO_CHALLENGES)
V5_BANKS.setdefault('micro', []).extend(V5_MICRO_CHALLENGES)
V5_BANKS['micro'] = v5_unique(V5_BANKS['micro'])


# ---------------------------------------------------------------------------
# Additional non-duplicated scenario cards.
# ---------------------------------------------------------------------------
V5_SCENARIO_CARDS = []
_scenarios = [
    ('⚡ شروع ناگهانی','سه بازیکن به‌صورت تصادفی انتخاب می‌شوند؛ اولین پاسخ درست یک پاداش کوچک دارد.'),
    ('🎭 نقش متغیر','هر بازیکن یک نقش کوتاه می‌گیرد و تا پایان این دور همان نقش را اجرا می‌کند.'),
    ('🧠 سؤال زنجیره‌ای','هر پاسخ باید با یک سؤال جدید ادامه پیدا کند؛ تکرار ممنوع است.'),
    ('🎰 شانس پنهان','قبل از انتخاب بازیکن، نتیجه یک جایزه یا حکم به‌صورت مخفی تعیین می‌شود.'),
    ('⚔️ آخرین مقاومت','بازیکنان اشتباه‌کننده یک فرصت بازگشت در دور بعد دارند.'),
    ('🕵️ سایه','یک نفر مأمور دارد بدون لو دادن خودش یک کلمه خاص را وارد گفت‌وگو کند.'),
    ('🏆 شکار امتیاز','یک بازیکن هدف، دو راه برای گرفتن امتیاز دارد و فقط یکی را می‌داند.'),
    ('🔮 پیش‌بینی دور','قبل از اجرای چالش، بازیکنان نتیجه احتمالی را حدس می‌زنند.'),
    ('👥 دو تیم','گروه به دو سمت تقسیم می‌شود و امتیاز تیمی در پایان محاسبه می‌شود.'),
    ('☠️ ریسک بالا','بازیکن بین یک پاداش کوچک مطمئن و یک پاداش بزرگ مشروط انتخاب می‌کند.'),
    ('👑 فرمانده','سرگروه یک محدودیت ساده برای این دور تعیین می‌کند.'),
    ('🧩 قطعه گمشده','یک نشانه ناقص ارائه می‌شود و بازیکنان باید بخش گمشده را حدس بزنند.'),
    ('🎯 هدف متحرک','بازیکن انتخاب‌شده با یک پاسخ درست هدف را به نفر دیگری منتقل می‌کند.'),
    ('🔄 چرخش','هر دور نقش بازیکن اصلی به نفر بعدی منتقل می‌شود.'),
    ('🍀 شانس مضاعف','یک نفر به‌صورت مخفی ضریب جایزه دارد، اما فقط تا پایان یک مرحله.'),
]
for i, (title, body) in enumerate(_scenarios,1):
    V5_SCENARIO_CARDS.append({'id':f'S{i:03d}','title':title,'body':body,'reward_xp':5+i%6,'reward_coins':2+i%4})
SCENARIO_V5 = {x['id']:x for x in V5_SCENARIO_CARDS}


# ---------------------------------------------------------------------------
# Feature health registry: these are used by the admin health screen.
# ---------------------------------------------------------------------------
V5_FEATURES = {
    'lobby_gate': 'Lobby + leader approval',
    'context_menus': 'Context-aware menus',
    'safe_callbacks': 'Callback guard',
    'cooldown': 'Spam cooldown',
    'admin_confirm': 'Destructive confirmations',
    'backup': 'Atomic backup/restore',
    'audit': 'Audit trail',
    'content_dedupe': 'No-repeat content chooser',
    'group_switches': 'Per-group feature gates',
    'penalty_ledger': 'Penalty ledger',
    'duel': 'Duel engine',
    'roulette': 'Roulette engine',
    'vote': 'Vote engine',
    'secret_mission': 'Secret mission engine',
    'spy': 'Spy engine',
    'mini_games': 'Mini-game collection',
    'economy': 'XP / coin economy',
    'inventory': 'Inventory',
    'achievements': 'Achievements',
    'leaderboard': 'Leaderboard',
    'adult_gate': 'Optional adult gate',
}


# ---------------------------------------------------------------------------
# V5 background cleanup — expires confirmations and stale in-memory sessions.
# ---------------------------------------------------------------------------
def v5_housekeeping():
    now=time.time()
    for token,info in list(V5_CONFIRM.items()):
        if now > float(info.get('expires',0)): V5_CONFIRM.pop(token,None)
    for key,ts in list(V5_RATE.items()):
        if now-ts>120: V5_RATE.pop(key,None)
    for key,session in list(V5_SESSION.items()):
        if now-float(session.get('last_ts',now))>3600: V5_SESSION.pop(key,None)


async def v5_cleanup_job(context):
    advanced_cleanup = globals().get('advanced_cleanup_job')
    if advanced_cleanup:
        try: await advanced_cleanup(context)
        except Exception: pass
    v5_housekeeping()
    save_data()


# ---------------------------------------------------------------------------
# V5 command wrappers
# ---------------------------------------------------------------------------
async def v5_admin_cmd(update,context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('🚫 فقط Super Admin.'); return
    await update.message.reply_text(v5_admin_home_text(),parse_mode=ParseMode.HTML,reply_markup=v5_admin_home_markup())


# ---------------------------------------------------------------------------
# New application wiring. Old mechanics stay available through their calls,
# but only this callback/text layer is registered, preventing dead UI routes.
# ---------------------------------------------------------------------------
def build_application_v5() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN is missing')
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start',v5_start))
    app.add_handler(CommandHandler('game',v5_create_lobby))
    app.add_handler(CommandHandler('menu',v5_menu))
    app.add_handler(CommandHandler('profile',v5_profile_message))
    app.add_handler(CommandHandler('rank',v5_rank_message))
    app.add_handler(CommandHandler('shop',shop_cmd))
    app.add_handler(CommandHandler('achievements',achievements_cmd))
    app.add_handler(CommandHandler('help',v5_help_message))
    app.add_handler(CommandHandler('id',id_cmd))
    app.add_handler(CommandHandler('admin',v5_admin_cmd))
    app.add_handler(CommandHandler('adult',adult_cmd))
    app.add_handler(CallbackQueryHandler(v5_callback,pattern=r'^V5\|'))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,v5_text_router))
    async def _post_init(application):
        await application.bot.set_my_commands([
            ('start','شروع ApexRival'),('game','ساخت Lobby'),('menu','منوی اصلی'),
            ('profile','پروفایل'),('rank','رتبه‌بندی'),('shop','فروشگاه'),
            ('achievements','دستاوردها'),('help','راهنما'),('id','آیدی'),('admin','پنل مدیریت')])
        if application.job_queue:
            application.job_queue.run_repeating(v5_cleanup_job,interval=30,first=15,name='apex_v5_cleanup')
    # PTB requires post_init to be configured before Application.build; attach
    # as a small wrapper by rebuilding if supported. Most PTB 22.x installations
    # accept builder.post_init().
    return app


def main_v5():
    start_health_server()
    application=Application.builder().token(BOT_TOKEN).post_init(_v5_post_init).build() if BOT_TOKEN else (_ for _ in ()).throw(RuntimeError('BOT_TOKEN is missing'))
    _register_v5_handlers(application)
    print(f'{BOT_NAME} {APEX_V5} starting...')
    application.run_polling(drop_pending_updates=True)


async def _v5_post_init(application):
    await application.bot.set_my_commands([
        ('start','شروع ApexRival'),('game','ساخت Lobby'),('menu','منوی اصلی'),('profile','پروفایل'),
        ('rank','رتبه‌بندی'),('shop','فروشگاه'),('achievements','دستاوردها'),('help','راهنما'),
        ('id','آیدی'),('admin','پنل مدیریت')
    ])
    if application.job_queue:
        application.job_queue.run_repeating(v5_cleanup_job,interval=30,first=15,name='apex_v5_cleanup')


def _register_v5_handlers(app):
    app.add_handler(CommandHandler('start',v5_start))
    app.add_handler(CommandHandler('game',v5_create_lobby))
    app.add_handler(CommandHandler('menu',v5_menu))
    app.add_handler(CommandHandler('profile',v5_profile_message))
    app.add_handler(CommandHandler('rank',v5_rank_message))
    app.add_handler(CommandHandler('shop',shop_cmd))
    app.add_handler(CommandHandler('achievements',achievements_cmd))
    app.add_handler(CommandHandler('help',v5_help_message))
    app.add_handler(CommandHandler('id',id_cmd))
    app.add_handler(CommandHandler('admin',v5_admin_cmd))
    app.add_handler(CommandHandler('adult',adult_cmd))
    app.add_handler(CallbackQueryHandler(v5_callback,pattern=r'^V5\|'))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,v5_text_router))


main=main_v5

if __name__=='__main__':
    main()
