import asyncio
import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

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
    "کدام تصمیم کوچک زندگی‌ات بیشتر از چیزی که فکر می‌کردی رویت اثر گذاشت؟",
    "اگر فقط یک نفر از گروه را برای یک سفر انتخاب کنی، چه کسی؟",
    "کدام ویژگی بقیه را سریع جذب می‌کند؟",
]

DARES = [
    "با لحن گوینده اخبار، آخرین چیزی که خوردی را گزارش کن.",
    "۳۰ ثانیه فقط با ایموجی جواب بده.",
    "یک جمله خیلی جدی درباره یک موضوع کاملاً مسخره بگو.",
    "برای خودت یک تبلیغ ۱۵ ثانیه‌ای بساز.",
    "اسم یک عضو گروه را انتخاب کن و سه تعریف واقعی از او بگو.",
    "یک جمله بگو که اگر خارج از این گروه شنیده شود عجیب به نظر برسد.",
    "تا دو پیام بعدی بدون استفاده از حرف «ا» جواب بده.",
]

FLIRTY = [
    "یک تعریف محترمانه و واقعی از یک نفر در گروه بنویس؛ طرف مقابل حق دارد نپذیرد.",
    "به انتخاب خودت یک نفر را انتخاب کن و یک لقب بامزه و محترمانه برایش بساز.",
    "یک جمله شروع گفت‌وگوی رمانتیکِ کاملاً محترمانه بنویس، بدون خطاب اجباری به شخص خاص.",
    "یک تعریف کوتاه درباره استایل یا انرژی یکی از اعضای گروه بگو.",
]

ADULT_SAFE = [
    "۱۸+: درباره یک قرار ایده‌آل، فقط در حد غیرصریح و محترمانه، یک سناریوی کوتاه بگو.",
    "۱۸+: بگو در یک رابطه سالم، مهم‌ترین مرز شخصی از نظر تو چیست؟",
    "۱۸+: یک سؤال صمیمی اما غیرجنسی از گروه بپرس؛ هرکس می‌تواند رد کند.",
    "۱۸+: یک ویژگی جذاب شخصیتی را نام ببر و توضیح کوتاه بده چرا.",
]

PENALTIES = [
    "یک پیام خنده‌دار با ۳ ایموجی تصادفی بفرست.",
    "برای ۲ دقیقه با یک لقب انتخابی بقیه صدایت کنند.",
    "یک تعریف واقعی از سه نفر گروه بنویس.",
    "یک جمله سخت‌گیرانه و رسمی درباره یک موضوع خنده‌دار بنویس.",
    "یک ویس ۱۰ ثانیه‌ای با صدای گوینده اخبار بفرست.",
]

BOSS = [
    "👑 Boss: اولین نفر که به این پیام با «APEX» جواب دهد، ۳ XP می‌گیرد.",
    "👑 Boss: یک سؤال سریع از گروه بپرس؛ اولین پاسخ درست ۵ XP می‌گیرد.",
    "👑 Boss: همه یک ایموجی بفرستند؛ مدیر بازی یکی را به‌صورت تصادفی انتخاب کند.",
]

EVENTS = [
    "⚡ رویداد: بازیکن با بیشترین XP فعلاً سپر دارد و در این مرحله مجازات نمی‌شود.",
    "🎲 رویداد: امتیاز این مرحله برای برنده دو برابر شد.",
    "🌀 رویداد: همه بازیکنان یک پیام کوتاه بفرستند؛ سازنده بازی یکی را انتخاب کند.",
    "🔥 رویداد: یک بازیکن تصادفی مأموریت کوتاه دریافت می‌کند.",
]

MAIN_BUTTONS = [
    ["🎮 بازی‌ها", "🕵️ اعتراف", "🔥 جرئت"],
    ["⚔️ دوئل", "🎰 گردونه", "🧠 سؤال گروهی"],
    ["⚡ مسابقه سرعت", "⚖️ حکم", "👤 پروفایل من"],
    ["🏆 رتبه‌بندی", "📜 قوانین", "❓ راهنما"],
]


def load_data() -> dict[str, Any]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError
        return data
    except Exception:
        return {"users": {}, "groups": {}, "games": {}}


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
    k = user_key(uid)
    with LOCK:
        u = DATA["users"].setdefault(k, {"name": name, "xp": 0, "coins": 0, "wins": 0, "losses": 0, "streak": 0, "best_streak": 0, "games": 0, "trials": 0, "banned": False})
        u["name"] = name or u.get("name", "کاربر")
        return u


def add_xp(uid: int, amount: int, name: str = "کاربر") -> None:
    u = get_user(uid, name)
    u["xp"] = max(0, int(u.get("xp", 0)) + amount)


def title_for(xp: int) -> str:
    if xp >= 500: return "👑 افسانه Apex"
    if xp >= 250: return "🔥 کابوس گروه"
    if xp >= 100: return "⚔️ رقیب جدی"
    if xp >= 50: return "🎯 بازیکن حرفه‌ای"
    return "🌱 تازه‌وارد"


def mention(user) -> str:
    name = (user.first_name or "بازیکن").replace("<", "").replace(">", "")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def group_key(chat_id: int) -> str:
    return str(chat_id)


def get_group(chat_id: int) -> dict[str, Any]:
    return DATA["groups"].setdefault(group_key(chat_id), {"adult_mode": False, "enabled": True, "active_game": None})


def is_admin(uid: int) -> bool:
    return bool(ADMIN_ID and uid == ADMIN_ID)


def is_banned(uid: int) -> bool:
    return bool(get_user(uid).get("banned", False))


def reply_keyboard(uid: int) -> ReplyKeyboardMarkup:
    rows = [r[:] for r in MAIN_BUTTONS]
    if is_admin(uid):
        rows.append(["👑 پنل مدیر"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def lobby_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟 ثبت‌نام", callback_data=f"join:{game_id}"), InlineKeyboardButton("❌ انصراف", callback_data=f"leave:{game_id}")],
        [InlineKeyboardButton("👥 بازیکنان", callback_data=f"players:{game_id}")],
        [InlineKeyboardButton("▶️ شروع بازی", callback_data=f"startgame:{game_id}"), InlineKeyboardButton("🛑 لغو", callback_data=f"cancelgame:{game_id}")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data=f"settings:{game_id}")],
    ])


def game_menu(chat_id: int) -> InlineKeyboardMarkup:
    adult = get_group(chat_id).get("adult_mode", False)
    rows = [
        [InlineKeyboardButton("🕵️ اعتراف", callback_data="play:truth"), InlineKeyboardButton("🔥 جرئت", callback_data="play:dare")],
        [InlineKeyboardButton("💘 فلرت", callback_data="play:flirty"), InlineKeyboardButton("🎰 گردونه", callback_data="play:roulette")],
        [InlineKeyboardButton("⚡ سرعت", callback_data="play:speed"), InlineKeyboardButton("🧠 سؤال", callback_data="play:question")],
        [InlineKeyboardButton("🤫 مأموریت مخفی", callback_data="play:secret"), InlineKeyboardButton("🗳 رأی‌گیری", callback_data="play:vote")],
        [InlineKeyboardButton("👑 Boss", callback_data="play:boss"), InlineKeyboardButton("🎲 رویداد", callback_data="play:event")],
    ]
    if adult:
        rows.append([InlineKeyboardButton("🔞 +18 غیرصریح", callback_data="play:adult")])
    return InlineKeyboardMarkup(rows)


def active_game(chat_id: int) -> dict[str, Any] | None:
    gid = get_group(chat_id).get("active_game")
    return DATA["games"].get(gid) if gid else None


def new_game(chat_id: int, leader_id: int, leader_name: str) -> str:
    gid = f"{chat_id}:{int(time.time()*1000)}:{random.randint(100,999)}"
    DATA["games"][gid] = {"id": gid, "chat_id": chat_id, "leader_id": leader_id, "leader_name": leader_name, "status": "lobby", "players": [leader_id], "names": {str(leader_id): leader_name}, "created": time.time(), "round": 0, "active": None, "pending_penalties": {}}
    get_group(chat_id)["active_game"] = gid
    return gid


def game_players_text(g: dict[str, Any]) -> str:
    if not g["players"]:
        return "هنوز کسی ثبت‌نام نکرده."
    return "\n".join(f"{i+1}. {g['names'].get(str(uid), 'بازیکن')}" for i, uid in enumerate(g["players"]))


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار", callback_data="admin:stats"), InlineKeyboardButton("👥 کاربران", callback_data="admin:users")],
        [InlineKeyboardButton("📝 سؤال‌ها", callback_data="admin:content_questions"), InlineKeyboardButton("🔥 جرئت‌ها", callback_data="admin:content_dares")],
        [InlineKeyboardButton("☠️ مجازات‌ها", callback_data="admin:content_penalties"), InlineKeyboardButton("🔞 +18", callback_data="admin:adult")],
        [InlineKeyboardButton("💾 ذخیره", callback_data="admin:save"), InlineKeyboardButton("🎲 رویداد", callback_data="admin:event")],
        [InlineKeyboardButton("👑 Boss", callback_data="admin:boss")],
    ])


async def ensure_allowed(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else 0
    if is_banned(uid):
        if update.callback_query:
            await update.callback_query.answer("حساب شما توسط مدیر مسدود شده است.", show_alert=True)
        elif update.effective_message:
            await update.effective_message.reply_text("🚫 دسترسی شما مسدود است.")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(
        f"🎮 <b>ApexRival</b>\n\nخوش اومدی {mention(update.effective_user)}!\n⭐ XP: {u['xp']}\n💰 سکه: {u['coins']}\n🏅 عنوان: {title_for(u['xp'])}\n\nبرای ساخت یک بازی گروهی، /game را بزن.",
        parse_mode=ParseMode.HTML, reply_markup=reply_keyboard(update.effective_user.id))


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("این دستور را داخل گروه اجرا کن.")
        return
    chat_id = update.effective_chat.id
    existing = active_game(chat_id)
    if existing:
        await update.message.reply_text("یک بازی در حال حاضر فعال است. اول همان بازی را لغو یا تمام کنید.")
        return
    gid = new_game(chat_id, update.effective_user.id, update.effective_user.first_name or "سرگروه")
    await update.message.reply_text(
        f"🎮 <b>لابی ApexRival ساخته شد!</b>\n\n👑 سرگروه: {mention(update.effective_user)}\n\nهرکس می‌خواهد بازی کند روی «🎟 ثبت‌نام» بزند.\n⛔ تا وقتی سرگروه «▶️ شروع بازی» را نزند، هیچ مرحله‌ای اجرا نمی‌شود.",
        parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(gid))
    save_data()


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"👤 <b>{u['name']}</b>\n⭐ XP: {u['xp']}\n💰 سکه: {u['coins']}\n🏆 برد: {u['wins']}\n☠️ باخت: {u['losses']}\n🔥 رکورد پشت‌سرهم: {u['best_streak']}\n🎖 {title_for(u['xp'])}", parse_mode=ParseMode.HTML)


async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = sorted(DATA["users"].values(), key=lambda x: x.get("xp", 0), reverse=True)[:10]
    text = "🏆 <b>رتبه‌بندی ApexRival</b>\n\n" + "\n".join(f"{i+1}. {u.get('name','کاربر')} — ⭐ {u.get('xp',0)} XP" for i,u in enumerate(users))
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("❓ /game = ساخت لابی\n/game باید داخل گروه اجرا شود.\n\nبعد از ثبت‌نام، فقط سرگروه می‌تواند بازی را شروع کند. مدیر اصلی ApexRival دسترسی مدیریتی کامل دارد.")


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🆔 User ID: {update.effective_user.id}\n💬 Chat ID: {update.effective_chat.id}")


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🎮 منوی ApexRival", reply_markup=game_menu(update.effective_chat.id))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not await ensure_allowed(update): return
    uid = q.from_user.id
    data = q.data

    if data.startswith("join:"):
        gid = data.split(":",1)[1]; g = DATA["games"].get(gid)
        if not g or g["status"] != "lobby": return await q.edit_message_text("این لابی دیگر فعال نیست.")
        if uid not in g["players"]:
            g["players"].append(uid); g["names"][str(uid)] = q.from_user.first_name or "بازیکن"
            await q.edit_message_text(f"🎮 <b>لابی ApexRival</b>\n\n👑 سرگروه: {g['leader_name']}\n\n👥 بازیکنان:\n{game_players_text(g)}\n\nبرای شروع، سرگروه باید تأیید کند.", parse_mode=ParseMode.HTML, reply_markup=lobby_keyboard(gid))
        else:
            await q.answer("قبلاً ثبت‌نام کردی.", show_alert=True)
        save_data(); return

    if data.startswith("leave:"):
        gid=data.split(":",1)[1]; g=DATA["games"].get(gid)
        if g and g["status"]=="lobby" and uid != g["leader_id"] and uid in g["players"]:
            g["players"].remove(uid); g["names"].pop(str(uid),None); save_data(); await q.answer("از بازی خارج شدی.")
        else: await q.answer("سرگروه نمی‌تواند از لابی خارج شود.", show_alert=True)
        return

    if data.startswith("players:"):
        gid=data.split(":",1)[1]; g=DATA["games"].get(gid)
        if not g: return await q.answer("بازی پیدا نشد.", show_alert=True)
        await q.answer(game_players_text(g)[:190], show_alert=True); return

    if data.startswith("startgame:"):
        gid=data.split(":",1)[1]; g=DATA["games"].get(gid)
        if not g: return
        if uid != g["leader_id"]: return await q.answer("فقط سرگروه می‌تواند بازی را شروع کند.", show_alert=True)
        if len(g["players"]) < 2: return await q.answer("حداقل ۲ بازیکن لازم است.", show_alert=True)
        g["status"]="active"; g["round"]=1; save_data()
        await q.edit_message_text(f"🟢 <b>ApexRival شروع شد!</b>\n\n👑 سرگروه: {g['leader_name']}\n👥 بازیکنان: {len(g['players'])}\n\nحالا مراحل بازی فعال هستند.", parse_mode=ParseMode.HTML, reply_markup=game_menu(g["chat_id"]))
        return

    if data.startswith("cancelgame:"):
        gid=data.split(":",1)[1]; g=DATA["games"].get(gid)
        if g and uid == g["leader_id"]:
            g["status"]="cancelled"; get_group(g["chat_id"])["active_game"]=None; save_data(); await q.edit_message_text("🛑 بازی توسط سرگروه لغو شد.")
        else: await q.answer("فقط سرگروه می‌تواند لغو کند.", show_alert=True)
        return

    if data.startswith("settings:"):
        gid=data.split(":",1)[1]; g=DATA["games"].get(gid)
        if not g or uid != g["leader_id"]: return await q.answer("فقط سرگروه.", show_alert=True)
        await q.answer("تنظیمات پیشرفته در حال آماده‌سازی است.", show_alert=True); return

    if data.startswith("play:"):
        g=active_game(q.message.chat_id)
        if not g or g["status"] != "active": return await q.answer("اول سرگروه باید بازی را شروع کند.", show_alert=True)
        kind=data.split(":",1)[1]
        await play_kind(q.message, q.from_user, g, kind)
        return

    if data.startswith("admin:"):
        if not is_admin(uid): return await q.answer("دسترسی ندارید.", show_alert=True)
        action=data.split(":",1)[1]
        if action == "stats":
            await q.message.reply_text(f"📊 کاربران: {len(DATA['users'])}\n👥 گروه‌ها: {len(DATA['groups'])}\n🎮 بازی‌ها: {len(DATA['games'])}")
        elif action == "save": save_data(); await q.message.reply_text("💾 ذخیره شد.")
        elif action == "adult": await q.message.reply_text("🔞 برای تغییر +18 از تنظیمات گروه استفاده کن؛ این حالت فقط برای گروه‌های واقعاً ۱۸+ و محتوای غیرصریح است.")
        elif action == "event": await q.message.reply_text(random.choice(EVENTS))
        elif action == "boss": await q.message.reply_text(random.choice(BOSS))
        elif action == "users": await q.message.reply_text(f"👥 تعداد کاربران ثبت‌شده: {len(DATA['users'])}")
        elif action == "content_questions": await q.message.reply_text(f"📝 تعداد سؤال‌ها: {len(QUESTIONS)}")
        elif action == "content_dares": await q.message.reply_text(f"🔥 تعداد جرئت‌ها: {len(DARES)}")
        elif action == "content_penalties": await q.message.reply_text(f"☠️ تعداد مجازات‌ها: {len(PENALTIES)}")
        return


async def play_kind(message, actor, g, kind: str) -> None:
    if kind == "truth": text=f"🕵️ <b>اعتراف</b>\n\n{random.choice(QUESTIONS)}"
    elif kind == "dare": text=f"🔥 <b>جرئت</b>\n\n{random.choice(DARES)}"
    elif kind == "flirty": text=f"💘 <b>فلرت محترمانه</b>\n\n{random.choice(FLIRTY)}"
    elif kind == "adult":
        if not get_group(g["chat_id"]).get("adult_mode"): return await message.reply_text("🔒 حالت +18 برای این گروه فعال نیست.")
        text=f"🔞 <b>۱۸+ غیرصریح</b>\n\n{random.choice(ADULT_SAFE)}"
    elif kind == "roulette":
        target=random.choice(g["players"]); name=g["names"].get(str(target),"بازیکن"); text=f"🎰 <b>گردونه</b>\n\nقرعه افتاد به: <b>{name}</b>\nاین بازیکن یک جرئت می‌گیرد.\n\n🔥 {random.choice(DARES)}"
    elif kind == "speed":
        answer=str(random.randint(10,99)); g["active"]={"type":"speed","answer":answer,"expires":time.time()+30}; text=f"⚡ <b>مسابقه سرعت!</b>\n\nاولین نفری که عدد <b>{answer}</b> را دقیق بفرستد، برنده است."
    elif kind == "question": text=f"🧠 <b>سؤال گروهی</b>\n\n{random.choice(QUESTIONS)}\n\nهمه می‌توانند جواب دهند؛ سرگروه می‌تواند برنده را انتخاب کند."
    elif kind == "secret":
        target=random.choice(g["players"]); name=g["names"].get(str(target),"بازیکن"); text=f"🤫 <b>مأموریت مخفی</b>\n\nیک مأموریت کوتاه برای <b>{name}</b>: در سه پیام بعدی کاری کن یکی از بازیکنان کلمه «بازی» را بگوید، بدون اینکه دلیلش را فاش کنی."
    elif kind == "vote":
        text="🗳 <b>چه کسی...؟</b>\n\nچه کسی احتمالاً بیشتر از همه در یک بازی رقابتی برنده می‌شود؟\n\nهمه یک نام بفرستند؛ رأی‌ها را سرگروه حساب کند."
    elif kind == "boss": text=random.choice(BOSS)
    elif kind == "event": text=random.choice(EVENTS)
    else: return
    g["round"] += 1
    save_data()
    await message.reply_text(text, parse_mode=ParseMode.HTML)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_allowed(update): return
    text=(update.message.text or "").strip()
    uid=update.effective_user.id
    if text == "👑 پنل مدیر":
        if is_admin(uid): await update.message.reply_text("👑 <b>پنل کامل مدیر ApexRival</b>", parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())
        else: await update.message.reply_text("دسترسی ندارید.")
        return
    if text == "🎮 بازی‌ها": await update.message.reply_text("🎮 منوی بازی", reply_markup=game_menu(update.effective_chat.id)); return
    mapping={"🕵️ اعتراف":"truth","🔥 جرئت":"dare","⚔️ دوئل":"roulette","🎰 گردونه":"roulette","🧠 سؤال گروهی":"question","⚡ مسابقه سرعت":"speed"}
    if text in mapping:
        g=active_game(update.effective_chat.id)
        if not g or g["status"]!="active": await update.message.reply_text("⛔ هنوز بازی شروع نشده. سرگروه باید لابی را تأیید و شروع کند.")
        else: await play_kind(update.message, update.effective_user, g, mapping[text])
        return
    if text == "⚖️ حکم":
        g=active_game(update.effective_chat.id)
        if not g or g["status"]!="active": return await update.message.reply_text("اول بازی را شروع کنید.")
        await update.message.reply_text(f"☠️ حکم فعلی: {random.choice(PENALTIES)}\n\nاگر این حکم به‌طور رسمی به تو اختصاص داده نشده، اجرا اجباری نیست.")
    elif text == "👤 پروفایل من": await profile(update, context)
    elif text == "🏆 رتبه‌بندی": await rank(update, context)
    elif text == "📜 قوانین": await update.message.reply_text("📜 قوانین: رضایت مهم است؛ هرکس می‌تواند یک چالش را رد کند. محتوای خطرناک، تهدید، آزار، افشای اطلاعات خصوصی و اجبار ممنوع است. +18 فقط اختیاری و غیرصریح است.")
    elif text == "❓ راهنما": await help_cmd(update, context)
    elif text == "انجام شد": add_xp(uid, 2, update.effective_user.first_name); save_data(); await update.message.reply_text("✅ ثبت شد! +۲ XP")
    else:
        g=active_game(update.effective_chat.id)
        if g and g.get("active",{}).get("type")=="speed" and time.time() <= g["active"].get("expires",0) and text == g["active"].get("answer"):
            add_xp(uid,5,update.effective_user.first_name); g["active"]=None; save_data(); await update.message.reply_text(f"🏁 {mention(update.effective_user)} برنده مسابقه سرعت شد! +۵ XP", parse_mode=ParseMode.HTML)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id): return await update.message.reply_text("دسترسی ندارید.")
    await update.message.reply_text("👑 پنل مدیر ApexRival", reply_markup=admin_keyboard())


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(b"ApexRival OK")
    def log_message(self, format, *args): return


def start_health_server():
    server=ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        ("start", "شروع"), ("game", "ساخت لابی بازی"), ("menu", "منوی بازی"), ("profile", "پروفایل"), ("rank", "رتبه‌بندی"), ("help", "راهنما"), ("id", "آیدی"),
    ])


def main():
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is missing")
    start_health_server()
    app=Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("game", game_command)); app.add_handler(CommandHandler("menu", menu_cmd)); app.add_handler(CommandHandler("profile", profile)); app.add_handler(CommandHandler("rank", rank)); app.add_handler(CommandHandler("help", help_cmd)); app.add_handler(CommandHandler("id", id_cmd)); app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    print("ApexRival starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
