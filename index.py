"""
Telegram-игра «Перекуп» v2.
Запуск:  pip install aiogram  →  export BOT_TOKEN=...  →  python perekup_bot_v2.py
"""
import asyncio
import json
import logging
import os
import random

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

TOKEN = os.getenv("BOT_TOKEN", "")
SAVE_FILE = "perekup_save_v2.json"
VERSION = 2

# ---------- Настройки баланса ----------
START_MONEY = 5000
GOAL = 100_000          # цель: накопить столько наличными
MAX_DAYS = 30           # за столько дней
ENERGY = 6              # действий (⚡) в день
RENT = 150              # аренда в день (растёт вместе со складом)
BASE_CAP = 3            # слотов склада в начале
MAX_CAP = 15
BOX_PRICE = 3500        # цена ящика-загадки
AVITO_FEE = 0.05        # комиссия Авито
FAKE_VALUE = 0.15       # во сколько раз подделка дешевле оригинала
DEFECT_VALUE = 0.6      # во сколько раз вещь с дефектом дешевле
COLLECT_CATS = ("🏺 Коллекции", "🎸 Хобби")

# ---------- Товары по категориям ----------
CATEGORIES = {
    "📱 Электроника": {
        "📱 iPhone 11": 15000, "📱 iPhone 14": 48000, "📱 Samsung Galaxy": 13000,
        "📱 Xiaomi Redmi": 7000, "💻 Ноутбук": 25000, "💻 MacBook": 55000,
        "📟 Планшет": 14500, "🎧 AirPods": 6000, "🎧 Наушники Sony": 11500,
        "🔋 Powerbank": 1800, "🔊 Bluetooth-колонка": 3800, "⌚ Apple Watch": 16000,
        "📺 Телевизор 43\"": 17000, "🖥 Монитор": 9000,
    },
    "🎮 Гейминг": {
        "🎮 PlayStation 4": 12000, "🎮 PlayStation 5": 45000, "🎮 Nintendo Switch": 18000,
        "🎮 Xbox Series S": 27000, "🕹 Steam Deck": 38000, "👾 Приставка Dendy": 2500,
        "🎮 Геймпад DualSense": 5500, "🥽 VR-шлем": 28000, "🪑 Игровое кресло": 8500,
        "🖥 Игровой ПК": 60000, "⌨️ Игровая клавиатура": 3500, "🖱 Игровая мышь": 2800,
        "🎧 Игровая гарнитура": 6500,
    },
    "👟 Одежда": {
        "👟 Кроссовки Nike": 5000, "👟 Кроссовки Jordan": 14000, "🧥 Куртка": 4000,
        "🧥 Пуховик Moncler": 38000, "🧥 Кожаная куртка": 9000, "👕 Худи Supreme": 12000,
        "👖 Джинсы Levi's": 3500, "🧢 Кепка New Era": 1500, "🕶 Очки Ray-Ban": 4500,
        "👜 Сумка Michael Kors": 9500, "🎒 Рюкзак": 2500, "🥾 Ботинки Timberland": 7500,
        "⌚ Часы": 7000, "⌚ Casio G-Shock": 6000,
    },
    "🚲 Транспорт": {
        "🚲 Велосипед": 8000, "🚵 Горный велосипед": 30000, "🛴 Самокат": 6500,
        "🛴 Электросамокат": 22000, "🚲 Электровелосипед": 45000, "🛵 Мопед": 35000,
        "🏍 Мотошлем": 9000, "🛼 Гироскутер": 7500, "⛸ Роликовые коньки": 4500,
        "📻 Автомагнитола": 5000, "👶 Автокресло": 6000, "🛞 Комплект колёс R16": 20000,
    },
    "🎸 Хобби": {
        "🎸 Гитара": 10000, "🎸 Электрогитара Fender": 42000, "🎹 Синтезатор": 15000,
        "🪕 Укулеле": 3500, "🥁 Барабанная установка": 25000, "🎤 Микрофон": 4000,
        "🏂 Сноуборд": 11000, "⛷ Лыжи": 8000, "⛺ Палатка": 6000, "🎣 Спиннинг": 4500,
        "🏋️ Гантели": 3500, "🚁 Дрон": 20000, "📷 Фотоаппарат": 14000,
        "🎥 Экшн-камера GoPro": 13500, "📸 Зеркалка Canon": 38000, "🔭 Телескоп": 16000,
        "🎨 Мольберт": 3000,
    },
    "🏠 Дом": {
        "☕ Кофемашина": 12500, "🤖 Робот-пылесос": 18000, "🍲 Мультиварка": 4000,
        "🍟 Аэрогриль": 5000, "🔥 Микроволновка": 4500, "🫖 Чайник Smeg": 7000,
        "🥤 Блендер": 3000, "🛋 Диван": 15000, "🧶 Ковёр": 5500, "🔨 Дрель Makita": 6500,
        "🪛 Шуруповёрт": 4500, "🧵 Швейная машинка": 7500, "💨 Фен Dyson": 22000,
        "👔 Парогенератор": 6000,
    },
    "🏺 Коллекции": {
        "🧱 Лего-набор": 5500, "🎲 Настольная игра": 3000, "📚 Коллекция книг": 2000,
        "💿 Винил Beatles": 9000, "🪙 Монеты СССР": 6000, "🧸 Фигурка Funko": 2200,
        "🃏 Карточки Pokémon": 8000, "🫙 Самовар": 7000, "🕰 Советские часы": 3500,
        "🏺 Антикварная ваза": 18000, "🖼 Картина маслом": 25000, "📷 Фотоаппарат ФЭД": 3000,
        "📌 Коллекция значков": 1500,
    },
}
ITEMS = {n: pr for items in CATEGORIES.values() for n, pr in items.items()}
CAT_OF = {n: c for c, items in CATEGORIES.items() for n in items}
CATS = list(CATEGORIES)

# ---------- Продавцы: имя, вес, цена от/до (доля рынка), шанс дефекта, шанс подделки, бонус к торгу, фраза
SELLERS = [
    ("👵 Бабушка", 28, 0.70, 1.00, 0.05, 0.00, 0.15, "«Вещь хорошая, берегла как зеницу ока»"),
    ("🎓 Студент", 30, 0.50, 0.80, 0.20, 0.00, 0.05, "«Срочно нужны деньги до стипендии!»"),
    ("🕵️ Барыга", 27, 0.80, 1.00, 0.30, 0.00, -0.15, "«Цена последняя, не торгуюсь»"),
    ("🎭 Подозрительный тип", 15, 0.30, 0.50, 0.10, 0.55, 0.00, "«Бери быстро, пока не передумал...»"),
]
# ---------- Покупатели: имя, цена от/до (доля стоимости), бонус к торгу, фраза
BUYERS = [
    ("🙂 Обычный покупатель", 0.80, 1.10, 0.00, "«Беру, если цена адекватная»"),
    ("🏪 Скупщик", 0.70, 0.88, -0.30, "«Забираю быстро и без разговоров»"),
    ("😤 Торгаш", 0.65, 0.85, 0.20, "«Дорого! Давай скинем...»"),
    ("🧐 Коллекционер", 1.10, 1.40, 0.00, "«Давно такое ищу!»"),
]
RANKS = [(0, "Новичок"), (5, "Барыга"), (15, "Опытный перекуп"), (30, "Профи рынка"), (50, "Король Авито")]

# ---------- Улучшения: название, макс. уровень, цена(ур), описание
PERKS = {
    "talk": ("🗣 Красноречие", 3, lambda l: 2500 * (l + 1), "+7% к шансу торга за уровень"),
    "eye": ("🔎 Намётанный глаз", 3, lambda l: 3000 * (l + 1), "+1 бесплатная проверка лота в день за уровень"),
    "car": ("🚗 Транспорт", 2, lambda l: 8000 if l == 0 else 20000, "+1⚡ в день за уровень"),
}

# ---------- Достижения
ACH = {
    "first": ("🥇 Первая сделка", lambda p: p["deals"] >= 1),
    "ten": ("🔟 10 сделок", lambda p: p["deals"] >= 10),
    "big": ("💎 Куш: +5 000 ₽ за одну сделку", lambda p: p["best"] >= 5000),
    "rich": ("🤑 30 000 ₽ в кармане", lambda p: p["money"] >= 30000),
    "scam": ("🛡 Раскусил мошенника", lambda p: p["scams_found"] >= 1),
    "master": ("🔧 Мастер на все руки (3 ремонта)", lambda p: p["repairs"] >= 3),
    "avito": ("👑 Король Авито (5 продаж)", lambda p: p["avito_sales"] >= 5),
    "orders": ("📋 Исполнительный (3 заказа)", lambda p: p["orders_done"] >= 3),
}

players: dict = {}


# ---------- Хранение ----------
def load():
    global players
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, encoding="utf-8") as f:
            players = json.load(f)


def save():
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False)


# ---------- Утилиты ----------
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", " ") + " ₽"


def sgn(n) -> str:
    return ("+" if n >= 0 else "−") + fmt(abs(n))


def r10(x) -> int:
    return max(10, int(round(x, -1)))


def grid(btns, n=2):
    return [btns[i:i + n] for i in range(0, len(btns), n)]


def kb(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows]
    )


# ---------- Игровая логика ----------
def roll_prices(p):
    up, down = random.sample(CATS, 2)
    p["trend"] = {"up": up, "down": down}
    prices = {}
    for n, base in ITEMS.items():
        k = random.uniform(0.88, 1.15)
        if CAT_OF[n] == up:
            k *= 1.25
        elif CAT_OF[n] == down:
            k *= 0.8
        prices[n] = r10(base * k)
    p["event"] = None
    if random.random() < 0.3:
        n = random.choice(list(ITEMS))
        if random.random() < 0.5:
            prices[n] = r10(prices[n] * 1.35)
            p["event"] = f"Хайп! {n} резко подорожал."
        else:
            prices[n] = r10(prices[n] * 0.7)
            p["event"] = f"Рынок завален: {n} подешевел."
    p["prices"] = prices


def gen_order(p):
    if len(p["orders"]) >= 3:
        return
    n = random.choice(list(ITEMS))
    if any(o["item"] == n for o in p["orders"]):
        return
    p["orders"].append({"item": n, "pay": r10(p["prices"][n] * random.uniform(1.25, 1.45)), "days": 4})


def new_player() -> dict:
    p = {
        "ver": VERSION, "money": START_MONEY, "day": 1, "energy": ENERGY, "rep": 0,
        "cap": BASE_CAP, "inv": [], "orders": [], "offer": None, "prices": {}, "trend": {},
        "event": None, "over": False, "perks": {"talk": 0, "eye": 0, "car": 0}, "free_checks": 0,
        "deals": 0, "best": 0, "profit": 0, "repairs": 0, "avito_sales": 0,
        "orders_done": 0, "scams_found": 0, "ach": [],
    }
    roll_prices(p)
    gen_order(p)
    return p


def get_player(uid) -> dict:
    uid = str(uid)
    if uid not in players or players[uid].get("ver") != VERSION:
        players[uid] = new_player()
    return players[uid]


def make_item(name, cost, defect=False, fake=False, known=False) -> dict:
    return {"item": name, "cost": cost, "defect": defect, "fake": fake, "known": known, "listed": None}


def max_energy(p) -> int:
    return ENERGY + p["perks"]["car"]


def rent_cost(p) -> int:
    return RENT + 40 * ((p["cap"] - BASE_CAP) // 2)


def real_value(p, it) -> int:
    v = p["prices"][it["item"]]
    if it["fake"]:
        return int(v * FAKE_VALUE)
    if it["defect"]:
        return int(v * DEFECT_VALUE)
    return int(v)


def net_worth(p) -> int:
    return p["money"] + sum(real_value(p, it) for it in p["inv"])


def rank(p) -> str:
    r = RANKS[0][1]
    for need, name in RANKS:
        if p["rep"] >= need:
            r = name
    return r


def haggle_chance(p, mod=0.0) -> float:
    c = 0.45 + min(p["rep"], 20) * 0.01 + p["perks"]["talk"] * 0.07 + mod
    return max(0.1, min(0.9, c))


def cap_cost(p) -> int:
    return 2000 * (p["cap"] - 2)


def repair_cost(p, it) -> int:
    return r10(max(100, p["prices"][it["item"]] * 0.12))


def complete_sale(p, it, price, fee=0) -> int:
    net = price - fee
    p["money"] += net
    profit = net - it["cost"]
    p["deals"] += 1
    p["profit"] += profit
    p["best"] = max(p["best"], profit)
    if profit > 0:
        p["rep"] += 1
    return profit


def check_ach(p) -> list:
    notes = []
    for key, (title, cond) in ACH.items():
        if key not in p["ach"] and cond(p):
            p["ach"].append(key)
            p["rep"] += 3
            notes.append(f"🏅 Достижение: {title} (+3⭐)")
    return notes


def box_item() -> str:
    r = random.random()
    if r < 0.75:
        lo, hi = 0, 3500
    elif r < 0.93:
        lo, hi = 3500, 9000
    elif r < 0.98:
        lo, hi = 9000, 20000
    else:
        lo, hi = 20000, 10 ** 9
    return random.choice([n for n, b in ITEMS.items() if lo <= b < hi])


def pick_buyer(item) -> int:
    if CAT_OF[item] in COLLECT_CATS and random.random() < 0.35:
        return 3
    return random.choices([0, 1, 2], weights=[50, 20, 20])[0]


def next_bid(price) -> int:
    return max(price + 10, r10(price * 1.1))


def offer_of(p, kind):
    o = p.get("offer")
    return o if o and o.get("type") == kind else None


def item_flag(it) -> str:
    s = ""
    if it.get("listed"):
        s += " 📢"
    if it["known"] and (it["defect"] or it["fake"]):
        s += " ⚠️"
    return s


# ---------- Тексты ----------
def header(p) -> str:
    return (
        f"📅 День {p['day']}/{MAX_DAYS}   ⚡ {p['energy']}/{max_energy(p)}\n"
        f"💵 {fmt(p['money'])}   ⭐ {rank(p)} ({p['rep']})\n"
        f"📦 Склад: {len(p['inv'])}/{p['cap']}   📋 Заказы: {len(p['orders'])}\n"
        f"🎯 Цель: {fmt(GOAL)}"
    )


def menu_text(p, note="") -> str:
    t = p["trend"]
    body = header(p) + f"\n\n📈 В тренде: {t['up']}\n📉 В упадке: {t['down']}"
    if p["event"]:
        body += f"\n📰 {p['event']}"
    return (f"{note}\n\n" if note else "") + body


def buy_text(p) -> str:
    o = p["offer"]
    s = SELLERS[o["seller"]]
    t = (
        f"🛒 {s[0]} продаёт: {o['item']}\n{s[7]}\n\n"
        f"💰 Цена: {fmt(o['ask'])}\n📊 Рынок: ~{fmt(p['prices'][o['item']])}\n"
    )
    if o["checked"]:
        if o["fake"]:
            t += f"🚨 Проверка: ПОДДЕЛКА! Стоит ~{int(FAKE_VALUE * 100)}% рынка.\n"
        elif o["defect"]:
            t += f"⚠️ Проверка: дефект! Стоит ~{int(DEFECT_VALUE * 100)}% рынка (можно починить).\n"
        else:
            t += "✅ Проверка: всё в порядке.\n"
    else:
        t += "🤔 По фото состояние не понять...\n"
    return t + f"\n💵 У вас: {fmt(p['money'])}   ⚡ {p['energy']}"


def buy_kb(p):
    o = p["offer"]
    rows = [[("✅ Купить", "buy"), ("❌ Пропустить", "skip")]]
    extra = []
    if not o["haggled"]:
        extra.append(("🗣 Торговаться", "haggle_buy"))
    if not o["checked"]:
        extra.append(("🔎 Проверить (бесплатно)" if p["free_checks"] > 0 else "🔎 Проверить (1⚡)", "inspect"))
    if extra:
        rows.append(extra)
    return kb(*rows)


def sell_text(p) -> str:
    o = p["offer"]
    it = p["inv"][o["idx"]]
    b = BUYERS[o["buyer"]]
    t = (
        f"🤝 {b[0]} хочет: {it['item']}\n{b[4]}\n\n"
        f"💰 Предлагает: {fmt(o['bid'])}\n📊 Рынок: ~{fmt(p['prices'][it['item']])}\n"
        f"🧾 Вы купили за: {fmt(it['cost'])}\n"
    )
    if it["known"] and it["fake"]:
        t += "🚨 Это подделка (вы знаете).\n"
    elif it["known"] and it["defect"]:
        t += "⚠️ У вещи дефект (вы знаете).\n"
    return t


def sell_kb(p):
    rows = [[("✅ Продать", "accept_sell"), ("❌ Отказать", "decline_sell")]]
    if not p["offer"]["haggled"]:
        rows.append([("🗣 Набить цену", "haggle_sell")])
    return kb(*rows)


def item_text(p, it) -> str:
    t = f"{it['item']}\n🧾 Куплено за: {fmt(it['cost'])}\n📊 Рынок: ~{fmt(p['prices'][it['item']])}\n"
    if it["known"] and it["fake"]:
        t += f"🚨 Подделка! Реально ~{int(FAKE_VALUE * 100)}% рынка.\n"
    elif it["known"] and it["defect"]:
        t += f"⚠️ Дефект: ~{int(DEFECT_VALUE * 100)}% рынка (можно починить).\n"
    elif it["known"]:
        t += "✅ Проверено: всё в порядке.\n"
    else:
        t += "❔ Состояние не проверено.\n"
    if it.get("listed"):
        t += f"📢 На Авито: {fmt(it['listed'])} (продаётся за ночь, комиссия {int(AVITO_FEE * 100)}%)\n"
    return t


def item_kb(p, i):
    it = p["inv"][i]
    rows = []
    if it.get("listed"):
        rows.append([("↩️ Снять с Авито", f"unlist:{i}")])
    else:
        rows.append([("💬 Найти покупателя (1⚡)", f"sell:{i}")])
        rows.append([("🏪 Скупщику сразу", f"dump:{i}")])
        rows.append([("📢 Авито −5%", f"list:{i}:-5"), ("📢 +15%", f"list:{i}:15"), ("📢 +35%", f"list:{i}:35")])
        if it["known"] and it["defect"] and not it["fake"]:
            rows.append([(f"🔧 Ремонт ({fmt(repair_cost(p, it))}, 1⚡)", f"repair:{i}")])
    rows.append([("⬅️ Склад", "inv")])
    return kb(*rows)


def auction_text(p, note="") -> str:
    o = p["offer"]
    return (f"{note}\n\n" if note else "") + (
        f"🔨 Аукцион: {o['item']}\n✨ Отличное состояние, дефектов нет\n"
        f"📊 Рынок: ~{fmt(p['prices'][o['item']])}\n💰 Текущая ставка: {fmt(o['price'])}\n"
        f"👥 Соперников: {len(o['bots'])}\n\n💵 У вас: {fmt(p['money'])}"
    )


def auction_kb(p):
    nb = next_bid(p["offer"]["price"])
    return kb([(f"⬆️ Поднять до {fmt(nb)}", "auc_raise")], [("🏁 Выйти", "auc_leave")])


def win_text(p) -> str:
    return (
        f"🏆 ПОБЕДА! Ты накопил {fmt(p['money'])} на день {p['day']}!\n"
        f"🏅 Звание: {rank(p)}\n🤝 Сделок: {p['deals']}   💎 Лучшая: {fmt(p['best'])}"
    )


def finish(p, text) -> str:
    p["over"] = True
    return text


# ---------- Отправка ----------
async def show(event, text, markup):
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            pass
        await event.answer()
    else:
        await event.answer(text, reply_markup=markup)


async def show_menu(event, p, note=""):
    p["offer"] = None
    if not p["over"]:
        extra = check_ach(p)
        if p["money"] >= GOAL:
            extra.append(finish(p, win_text(p)))
        if extra:
            note = (note + "\n\n" if note else "") + "\n".join(extra)
    save()
    if p["over"]:
        await show(event, note or "Игра окончена.", kb([("🔄 Новая игра", "restart")]))
    else:
        await show(event, menu_text(p, note), menu_kb(p))


async def show_item(event, p, i, note=""):
    it = p["inv"][i]
    save()
    await show(event, (f"{note}\n\n" if note else "") + item_text(p, it), item_kb(p, i))


def menu_kb(p):
    return kb(
        [("🔍 Искать лот (1⚡)", "search"), ("🔨 Аукцион (1⚡)", "auction")],
        [("📦 Склад", "inv"), (f"📋 Заказы ({len(p['orders'])})", "orders")],
        [("🏷 Рынок", "market"), (f"🎁 Ящик-загадка ({fmt(BOX_PRICE)})", "box")],
        [("🛒 Улучшения", "perks"), ("🏅 Профиль", "profile")],
        [("😴 Закончить день", "next")],
    )


# ---------- Команды ----------
dp = Dispatcher()
ACTIONS = {}


def action(name):
    def deco(fn):
        ACTIONS[name] = fn
        return fn
    return deco


RULES_TEXT = (
    "📖 Правила\n\n"
    f"Старт: {fmt(START_MONEY)}. Цель: {fmt(GOAL)} наличными за {MAX_DAYS} дней.\n"
    f"В день {ENERGY} действий (⚡), аренда от {fmt(RENT)}.\n\n"
    "Что умеешь:\n"
    "• искать лоты по категориям: продавцы бывают честными, жуликами и барыгами;\n"
    "• проверять вещи на дефекты и подделки, чинить их;\n"
    "• торговаться, продавать скупщикам и коллекционерам;\n"
    "• выставлять вещи на Авито — они продаются за ночь;\n"
    "• выполнять заказы клиентов с наценкой;\n"
    "• играть на аукционе и рисковать с ящиком-загадкой;\n"
    "• прокачивать навыки и открывать достижения.\n\n"
    "Команда /new — начать заново."
)


def start_screen(p):
    text = (
        "🔥 ПЕРЕКУП 🔥\n\n"
        f"Покупай вещи дешевле рынка, продавай дороже и накопи {fmt(GOAL)} за {MAX_DAYS} дней."
    )
    if p["over"]:
        rows = [[("🔄 Новая игра", "restart")]]
    elif p["day"] > 1 or p["deals"] > 0 or p["inv"] or p["money"] != START_MONEY:
        text += "\n\nУ тебя есть сохранённая игра."
        rows = [[("▶️ Продолжить", "play")], [("🔄 Новая игра", "restart")], [("📖 Правила", "rules")]]
    else:
        text += "\n\nНажми «Играть», чтобы начать!"
        rows = [[("▶️ Играть", "play")], [("📖 Правила", "rules")]]
    return text, kb(*rows)


@dp.message(CommandStart())
async def cmd_start(m: Message):
    p = get_player(m.from_user.id)
    text, markup = start_screen(p)
    await m.answer(text, reply_markup=markup)


@action("play")
async def a_play(cb, p, arg):
    await show_menu(cb, p)


@action("rules")
async def a_rules(cb, p, arg):
    await show(cb, RULES_TEXT, kb([("▶️ Играть", "play")], [("⬅️ Назад", "home")]))


@action("home")
async def a_home(cb, p, arg):
    text, markup = start_screen(p)
    await show(cb, text, markup)


@dp.message(Command("new"))
async def cmd_new(m: Message):
    players[str(m.from_user.id)] = new_player()
    await show_menu(m, players[str(m.from_user.id)], "Новая игра начата!")


@dp.callback_query()
async def on_cb(cb: CallbackQuery):
    p = get_player(cb.from_user.id)
    data = cb.data or ""
    act, _, arg = data.partition(":")
    if act == "restart":
        players[str(cb.from_user.id)] = p = new_player()
        return await show_menu(cb, p, "Новая игра!")
    if p["over"]:
        return await show_menu(cb, p, "Игра окончена. Нажми «Новая игра».")
    fn = ACTIONS.get(act)
    if fn is None:
        return await cb.answer()
    try:
        await fn(cb, p, arg)
    except Exception:
        logging.exception("Ошибка в действии %s", data)
        await show_menu(cb, p, "⚠️ Что-то пошло не так, возвращаю в меню.")


# ---------- Меню / рынок ----------
@action("menu")
async def a_menu(cb, p, arg):
    await show_menu(cb, p)


@action("market")
async def a_market(cb, p, arg):
    t = p["trend"]
    text = f"🏷 Рынок сегодня\n\n📈 В тренде: {t['up']}\n📉 В упадке: {t['down']}\n\nВыбери категорию:"
    btns = [(c, f"mk:{i}") for i, c in enumerate(CATS)]
    await show(cb, text, kb(*grid(btns), [("⬅️ Назад", "menu")]))


@action("mk")
async def a_mk(cb, p, arg):
    c = CATS[int(arg)]
    lines = []
    for n, base in sorted(CATEGORIES[c].items(), key=lambda x: x[1]):
        cur = p["prices"][n]
        arrow = "📈" if cur > base * 1.1 else "📉" if cur < base * 0.9 else "➖"
        lines.append(f"{arrow} {n}: {fmt(cur)}")
    await show(cb, f"{c}\n\n" + "\n".join(lines), kb([("⬅️ К категориям", "market")], [("🏠 Меню", "menu")]))


# ---------- Поиск и покупка ----------
@action("search")
async def a_search(cb, p, arg):
    if p["energy"] < 1:
        return await show_menu(cb, p, "😵 Нет сил. Закончи день.")
    if len(p["inv"]) >= p["cap"]:
        return await show_menu(cb, p, "📦 Склад полон! Продай что-нибудь или расширь склад.")
    btns = [(c, f"cat:{i}") for i, c in enumerate(CATS)]
    await show(cb, "🔍 Где ищем лот? (1⚡)", kb(*grid(btns), [("⬅️ Назад", "menu")]))


@action("cat")
async def a_cat(cb, p, arg):
    if p["energy"] < 1:
        return await show_menu(cb, p, "😵 Нет сил. Закончи день.")
    if len(p["inv"]) >= p["cap"]:
        return await show_menu(cb, p, "📦 Склад полон!")
    c = CATS[int(arg)]
    p["energy"] -= 1
    item = random.choice(list(CATEGORIES[c]))
    si = random.choices(range(len(SELLERS)), weights=[s[1] for s in SELLERS])[0]
    s = SELLERS[si]
    fake = random.random() < s[5]
    defect = (not fake) and random.random() < s[4]
    ask = r10(p["prices"][item] * random.uniform(s[2], s[3]))
    p["offer"] = {"type": "buy", "item": item, "ask": ask, "defect": defect, "fake": fake,
                  "checked": False, "haggled": False, "seller": si}
    save()
    await show(cb, buy_text(p), buy_kb(p))


@action("buy")
async def a_buy(cb, p, arg):
    o = offer_of(p, "buy")
    if not o:
        return await show_menu(cb, p, "Это предложение уже неактуально.")
    if p["money"] < o["ask"]:
        return await show(cb, buy_text(p) + "\n❌ Не хватает денег!", buy_kb(p))
    p["money"] -= o["ask"]
    p["inv"].append(make_item(o["item"], o["ask"], o["defect"], o["fake"], o["checked"]))
    await show_menu(cb, p, f"✅ Куплено: {o['item']} за {fmt(o['ask'])}")


@action("haggle_buy")
async def a_haggle_buy(cb, p, arg):
    o = offer_of(p, "buy")
    if not o or o["haggled"]:
        return await show_menu(cb, p, "Это предложение уже неактуально.")
    o["haggled"] = True
    if random.random() < haggle_chance(p, SELLERS[o["seller"]][6]):
        o["ask"] = r10(o["ask"] * random.uniform(0.80, 0.92))
        save()
        return await show(cb, "😎 Продавец уступил!\n\n" + buy_text(p), buy_kb(p))
    if random.random() < 0.4:
        return await show_menu(cb, p, "😤 Продавец обиделся и ушёл.")
    save()
    await show(cb, "🙅 Продавец не уступает.\n\n" + buy_text(p), buy_kb(p))


@action("inspect")
async def a_inspect(cb, p, arg):
    o = offer_of(p, "buy")
    if not o or o["checked"]:
        return await show_menu(cb, p, "Это предложение уже неактуально.")
    if p["free_checks"] > 0:
        p["free_checks"] -= 1
    elif p["energy"] >= 1:
        p["energy"] -= 1
    else:
        return await show(cb, buy_text(p) + "\n😵 Нет сил на проверку.", buy_kb(p))
    o["checked"] = True
    if o["fake"]:
        p["scams_found"] += 1
    save()
    await show(cb, buy_text(p), buy_kb(p))


@action("skip")
async def a_skip(cb, p, arg):
    await show_menu(cb, p, "Пропустили лот.")


# ---------- Склад ----------
@action("inv")
async def a_inv(cb, p, arg):
    if not p["inv"]:
        return await show(cb, "📦 Склад пуст. Найди что-нибудь!", kb([("⬅️ Назад", "menu")]))
    rows = [[(f"{it['item']} · {fmt(it['cost'])}{item_flag(it)}", f"item:{i}")] for i, it in enumerate(p["inv"])]
    rows.append([("⬅️ Назад", "menu")])
    text = (
        f"📦 Склад {len(p['inv'])}/{p['cap']}\n"
        f"Оценка по рынку: ~{fmt(sum(real_value(p, it) for it in p['inv']))}\n"
        "Выбери вещь:"
    )
    await show(cb, text, kb(*rows))


def get_idx(p, arg):
    try:
        i = int(arg.split(":")[0])
    except ValueError:
        return None
    return i if 0 <= i < len(p["inv"]) else None


@action("item")
async def a_item(cb, p, arg):
    i = get_idx(p, arg)
    if i is None:
        return await show_menu(cb, p, "Вещь не найдена.")
    await show_item(cb, p, i)


@action("sell")
async def a_sell(cb, p, arg):
    i = get_idx(p, arg)
    if i is None:
        return await show_menu(cb, p, "Вещь не найдена.")
    it = p["inv"][i]
    if it.get("listed"):
        return await show_item(cb, p, i, "Сначала сними вещь с Авито.")
    if p["energy"] < 1:
        return await show_item(cb, p, i, "😵 Нет сил искать покупателя.")
    p["energy"] -= 1
    bi = pick_buyer(it["item"])
    b = BUYERS[bi]
    bid = r10(real_value(p, it) * random.uniform(b[1], b[2]) * (1 + min(p["rep"], 20) * 0.005))
    p["offer"] = {"type": "sell", "idx": i, "bid": bid, "haggled": False, "buyer": bi}
    save()
    await show(cb, sell_text(p), sell_kb(p))


@action("accept_sell")
async def a_accept_sell(cb, p, arg):
    o = offer_of(p, "sell")
    if not o or o["idx"] >= len(p["inv"]):
        return await show_menu(cb, p, "Покупатель уже ушёл.")
    it = p["inv"].pop(o["idx"])
    profit = complete_sale(p, it, o["bid"])
    note = f"💸 Продано: {it['item']} за {fmt(o['bid'])} ({sgn(profit)})"
    if it["fake"] and not it["known"]:
        note += "\n(это была подделка — покупатель сбил цену)"
    elif it["defect"] and not it["known"]:
        note += "\n(был скрытый дефект — покупатель сбил цену)"
    await show_menu(cb, p, note)


@action("haggle_sell")
async def a_haggle_sell(cb, p, arg):
    o = offer_of(p, "sell")
    if not o or o["haggled"] or o["idx"] >= len(p["inv"]):
        return await show_menu(cb, p, "Покупатель уже ушёл.")
    o["haggled"] = True
    if random.random() < haggle_chance(p, BUYERS[o["buyer"]][3]):
        o["bid"] = r10(o["bid"] * random.uniform(1.08, 1.20))
        save()
        return await show(cb, "😏 Покупатель согласился на большее!\n\n" + sell_text(p), sell_kb(p))
    if random.random() < 0.35:
        return await show_menu(cb, p, "🚶 Покупатель ушёл.")
    save()
    await show(cb, "🙅 Покупатель стоит на своём.\n\n" + sell_text(p), sell_kb(p))


@action("decline_sell")
async def a_decline_sell(cb, p, arg):
    await show_menu(cb, p, "Отказали покупателю.")


@action("dump")
async def a_dump(cb, p, arg):
    i = get_idx(p, arg)
    if i is None:
        return await show_menu(cb, p, "Вещь не найдена.")
    it = p["inv"].pop(i)
    price = r10(real_value(p, it) * 0.65)
    profit = complete_sale(p, it, price)
    await show_menu(cb, p, f"🏪 Скупщик забрал {it['item']} за {fmt(price)} ({sgn(profit)})")


@action("list")
async def a_list(cb, p, arg):
    i = get_idx(p, arg)
    if i is None:
        return await show_menu(cb, p, "Вещь не найдена.")
    try:
        pct = int(arg.split(":")[1])
    except (IndexError, ValueError):
        return await show_item(cb, p, i)
    it = p["inv"][i]
    it["listed"] = r10(p["prices"][it["item"]] * (1 + pct / 100))
    await show_item(cb, p, i, f"📢 Объявление выложено: {fmt(it['listed'])}")


@action("unlist")
async def a_unlist(cb, p, arg):
    i = get_idx(p, arg)
    if i is None:
        return await show_menu(cb, p, "Вещь не найдена.")
    p["inv"][i]["listed"] = None
    await show_item(cb, p, i, "Объявление снято.")


@action("repair")
async def a_repair(cb, p, arg):
    i = get_idx(p, arg)
    if i is None:
        return await show_menu(cb, p, "Вещь не найдена.")
    it = p["inv"][i]
    if not (it["known"] and it["defect"]) or it["fake"]:
        return await show_item(cb, p, i, "Тут нечего чинить.")
    cost = repair_cost(p, it)
    if p["energy"] < 1:
        return await show_item(cb, p, i, "😵 Нет сил на ремонт.")
    if p["money"] < cost:
        return await show_item(cb, p, i, f"Нужно {fmt(cost)} на запчасти.")
    p["energy"] -= 1
    p["money"] -= cost
    if random.random() < 0.8:
        it["defect"] = False
        p["repairs"] += 1
        note = f"🔧 Отремонтировано! Теперь {it['item']} стоит полную цену."
    else:
        note = f"💥 Не получилось починить, запчасти ({fmt(cost)}) потрачены зря."
    await show_item(cb, p, i, note)


# ---------- Заказы ----------
@action("orders")
async def a_orders(cb, p, arg):
    if not p["orders"]:
        return await show(cb, "📋 Заказов нет. Завтра могут появиться новые.", kb([("⬅️ Назад", "menu")]))
    lines, rows = [], []
    for k, o in enumerate(p["orders"]):
        lines.append(f"• {o['item']} — заплатят {fmt(o['pay'])} (дней: {o['days']}, рынок ~{fmt(p['prices'][o['item']])})")
        has = any(it["item"] == o["item"] and not (it["known"] and (it["defect"] or it["fake"])) for it in p["inv"])
        if has:
            rows.append([(f"✅ Выполнить: {o['item']} (+{fmt(o['pay'])})", f"order:{k}")])
    rows.append([("⬅️ Назад", "menu")])
    text = "📋 Заказы клиентов (нужен исправный оригинал):\n\n" + "\n".join(lines)
    await show(cb, text, kb(*rows))


@action("order")
async def a_order(cb, p, arg):
    k = int(arg)
    if k >= len(p["orders"]):
        return await show_menu(cb, p, "Заказ уже недоступен.")
    o = p["orders"][k]
    idxs = [i for i, it in enumerate(p["inv"])
            if it["item"] == o["item"] and not (it["known"] and (it["defect"] or it["fake"]))]
    if not idxs:
        return await show_menu(cb, p, "У тебя нет подходящей вещи.")
    i = idxs[0]
    it = p["inv"][i]
    if it["fake"] or it["defect"]:
        it["known"] = True
        p["rep"] = max(0, p["rep"] - 1)
        kind = "подделка" if it["fake"] else "дефект"
        return await show_menu(cb, p, f"😠 Клиент проверил вещь: {kind}! Сделка сорвана (−1⭐).")
    p["inv"].pop(i)
    p["orders"].pop(k)
    profit = complete_sale(p, it, o["pay"])
    p["rep"] += 2
    p["orders_done"] += 1
    await show_menu(cb, p, f"📋 Заказ выполнен: {it['item']} за {fmt(o['pay'])} ({sgn(profit)}, +2⭐)")


# ---------- Ящик-загадка ----------
@action("box")
async def a_box(cb, p, arg):
    if p["energy"] < 1:
        return await show_menu(cb, p, "😵 Нет сил. Закончи день.")
    if len(p["inv"]) >= p["cap"]:
        return await show_menu(cb, p, "📦 Склад полон!")
    if p["money"] < BOX_PRICE:
        return await show_menu(cb, p, f"Ящик стоит {fmt(BOX_PRICE)}.")
    p["energy"] -= 1
    p["money"] -= BOX_PRICE
    name = box_item()
    p["inv"].append(make_item(name, BOX_PRICE, defect=random.random() < 0.2))
    await show_menu(cb, p, f"🎁 В ящике: {name}! Рынок ~{fmt(p['prices'][name])}")


# ---------- Аукцион ----------
@action("auction")
async def a_auction(cb, p, arg):
    if p["energy"] < 1:
        return await show_menu(cb, p, "😵 Нет сил. Закончи день.")
    if len(p["inv"]) >= p["cap"]:
        return await show_menu(cb, p, "📦 Склад полон!")
    p["energy"] -= 1
    item = random.choice(list(ITEMS))
    m = p["prices"][item]
    bots = [m * random.uniform(0.45, 1.0) for _ in range(random.choice([1, 2, 2, 3]))]
    p["offer"] = {"type": "auction", "item": item, "price": r10(m * 0.45), "bots": bots}
    save()
    await show(cb, auction_text(p), auction_kb(p))


@action("auc_raise")
async def a_auc_raise(cb, p, arg):
    o = offer_of(p, "auction")
    if not o:
        return await show_menu(cb, p, "Аукцион уже закончился.")
    new = next_bid(o["price"])
    if p["money"] < new:
        return await show(cb, auction_text(p, "❌ Не хватает денег на ставку!"), auction_kb(p))
    before = len(o["bots"])
    o["price"] = new
    o["bots"] = [b for b in o["bots"] if b >= new]
    if not o["bots"]:
        p["money"] -= new
        p["inv"].append(make_item(o["item"], new, known=True))
        return await show_menu(cb, p, f"🔨 Победа на аукционе! {o['item']} за {fmt(new)} (рынок ~{fmt(p['prices'][o['item']])})")
    note = "👋 Один соперник сдался." if len(o["bots"]) < before else "Соперники не сдаются!"
    save()
    await show(cb, auction_text(p, note), auction_kb(p))


@action("auc_leave")
async def a_auc_leave(cb, p, arg):
    await show_menu(cb, p, "Вышли с аукциона.")


# ---------- Улучшения ----------
def perks_screen(p, note=""):
    lines = []
    rows = []
    for key, (name, mx, cost, desc) in PERKS.items():
        lvl = p["perks"][key]
        lines.append(f"{name} {lvl}/{mx}: {desc}")
        if lvl < mx:
            rows.append([(f"{name} → {lvl + 1} ({fmt(cost(lvl))})", f"perk:{key}")])
    lines.append(f"📦 Склад {p['cap']}/{MAX_CAP}: +2 слота (аренда дороже)")
    if p["cap"] < MAX_CAP:
        rows.append([(f"📦 Склад +2 ({fmt(cap_cost(p))})", "capup")])
    rows.append([("⬅️ Назад", "menu")])
    text = (f"{note}\n\n" if note else "") + f"🛒 Улучшения\n💵 {fmt(p['money'])}\n\n" + "\n".join(lines)
    return text, kb(*rows)


@action("perks")
async def a_perks(cb, p, arg):
    text, markup = perks_screen(p)
    await show(cb, text, markup)


@action("perk")
async def a_perk(cb, p, arg):
    if arg not in PERKS:
        return await show_menu(cb, p)
    name, mx, cost, _ = PERKS[arg]
    lvl = p["perks"][arg]
    if lvl >= mx:
        text, markup = perks_screen(p, "Уже максимум.")
    elif p["money"] < cost(lvl):
        text, markup = perks_screen(p, f"Не хватает денег ({fmt(cost(lvl))}).")
    else:
        p["money"] -= cost(lvl)
        p["perks"][arg] += 1
        if arg == "car":
            p["energy"] += 1
        if arg == "eye":
            p["free_checks"] += 1
        text, markup = perks_screen(p, f"✅ Улучшено: {name}!")
    save()
    await show(cb, text, markup)


@action("capup")
async def a_capup(cb, p, arg):
    cost = cap_cost(p)
    if p["cap"] >= MAX_CAP:
        text, markup = perks_screen(p, "Склад уже максимальный.")
    elif p["money"] < cost:
        text, markup = perks_screen(p, f"Не хватает денег ({fmt(cost)}).")
    else:
        p["money"] -= cost
        p["cap"] += 2
        text, markup = perks_screen(p, "🏗 Склад расширен на 2 слота!")
    save()
    await show(cb, text, markup)


# ---------- Профиль ----------
@action("profile")
async def a_profile(cb, p, arg):
    ach = [f"{'✅' if k in p['ach'] else '🔒'} {t}" for k, (t, _) in ACH.items()]
    text = (
        f"🏅 Профиль\n\nЗвание: {rank(p)} ({p['rep']}⭐)\n"
        f"📊 Капитал: {fmt(net_worth(p))}\n🤝 Сделок: {p['deals']}\n"
        f"💹 Чистая прибыль: {sgn(p['profit'])}\n💎 Лучшая сделка: {fmt(p['best'])}\n"
        f"🔧 Ремонтов: {p['repairs']}\n📢 Продаж на Авито: {p['avito_sales']}\n"
        f"📋 Заказов: {p['orders_done']}\n🛡 Мошенников раскрыто: {p['scams_found']}\n"
        f"🏢 Аренда: {fmt(rent_cost(p))}/день\n\n"
        f"Достижения ({len(p['ach'])}/{len(ACH)}):\n" + "\n".join(ach)
    )
    await show(cb, text, kb([("⬅️ Назад", "menu")]))


# ---------- Конец дня ----------
@action("next")
async def a_next(cb, p, arg):
    notes = []

    # Авито продаёт за ночь
    for it in list(p["inv"]):
        lp = it.get("listed")
        if not lp:
            continue
        m = lp / max(1, real_value(p, it))
        chance = 0.85 if m <= 1 else max(0.05, 0.85 - (m - 1) * 1.5)
        if random.random() < chance:
            fee = int(lp * AVITO_FEE)
            profit = complete_sale(p, it, lp, fee)
            p["inv"] = [x for x in p["inv"] if x is not it]
            p["avito_sales"] += 1
            notes.append(f"📢 Авито: {it['item']} продан за {fmt(lp)} (комиссия {fmt(fee)}, {sgn(profit)})")

    p["day"] += 1

    # аренда
    rent = rent_cost(p)
    p["money"] -= rent
    notes.append(f"🏢 Аренда: −{fmt(rent)}")
    if p["money"] < 0 and p["inv"]:
        total = sum(r10(real_value(p, it) * 0.6) for it in p["inv"])
        p["money"] += total
        p["inv"] = []
        notes.append(f"🚨 Не хватило на аренду — склад срочно продан скупщику за {fmt(total)}")
    if p["money"] < 0:
        return await show_menu(cb, p, finish(p, f"💀 Банкрот! Не хватило на аренду.\nДней продержался: {p['day'] - 1}"))

    # случайные события
    if random.random() < 0.12 and p["money"] >= 3000:
        fine = max(200, int(p["money"] * 0.03))
        p["money"] -= fine
        notes.append(f"🚔 Проверка! Штраф за торговлю без ИП: −{fmt(fine)}")
    if random.random() < 0.12 and len(p["inv"]) < p["cap"]:
        name = random.choice([n for n, b in ITEMS.items() if b <= 5000])
        p["inv"].append(make_item(name, 0, defect=random.random() < 0.3))
        notes.append(f"🎁 Нашёл на помойке: {name}!")

    # заказы
    for o in p["orders"]:
        o["days"] -= 1
    expired = [o for o in p["orders"] if o["days"] <= 0]
    p["orders"] = [o for o in p["orders"] if o["days"] > 0]
    for o in expired:
        notes.append(f"⌛ Заказ на {o['item']} истёк.")

    # конец игры по сроку
    if p["day"] > MAX_DAYS:
        nw = net_worth(p)
        if nw >= GOAL:
            txt = f"🏆 Срок вышел, но капитал {fmt(nw)} — ты победил! Звание: {rank(p)}"
        else:
            txt = f"⌛ Срок вышел. Капитал: {fmt(nw)} из {fmt(GOAL)}. Попробуй ещё раз!"
        return await show_menu(cb, p, finish(p, "\n".join(notes) + "\n\n" + txt))

    roll_prices(p)
    if random.random() < 0.7:
        gen_order(p)
    p["energy"] = max_energy(p)
    p["free_checks"] = p["perks"]["eye"]
    await show_menu(cb, p, f"🌅 День {p['day']}\n" + "\n".join(notes))


async def main():
    if not TOKEN:
        raise SystemExit("Задай токен: export BOT_TOKEN=123:ABC...")
    logging.basicConfig(level=logging.INFO)
    load()
    bot = Bot(TOKEN)
    await bot.set_my_commands([
        BotCommand(command="start", description="▶️ Играть"),
        BotCommand(command="new", description="🔄 Новая игра"),
    ])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

