import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8254209430:AAHrYF_5KJCA77-4nYpCaleisJckxUtCMLY"
CHANNEL_ID = "@testhp404bot"
CHANNEL_LINK = "https://t.me/testhp404bot"
SUPER_ADMIN_USERNAME = "nelinner"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()

# Состояния FSM
class Registration(StatesGroup):
    waiting_nickname = State()
    waiting_game_id = State()
    confirm = State()

class LobbyCreation(StatesGroup):
    waiting_duo_partner = State()
    confirm = State()

class ResultSubmission(StatesGroup):
    waiting_screenshot = State()
    waiting_score = State()
    waiting_swap = State()

class LobbyLink(StatesGroup):
    waiting_link = State()

class Ticket(StatesGroup):
    waiting_text = State()

class AdminAction(StatesGroup):
    waiting_username = State()

# Карты и режимы
MAPS = {
    'competitive': ['Sandstone', 'Zone 9', 'Rust', 'Dune', 'Training Outside'],
    'duo': ['Sandstone', 'Zone 9', 'Province', 'Breeze'],
    'duel': ['Sandstone', 'Zone 9', 'Arena']
}
MODE_NAMES = {'competitive': 'Соревновательный', 'duo': 'Напарники', 'duel': 'Дуэль'}
ROUNDS = {'competitive': 13, 'duo': 9, 'duel': 9}

# Вспомогательные функции
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def is_super_admin(user_id):
    user = await db.get_user(user_id)
    return user and user[1] == SUPER_ADMIN_USERNAME

async def get_main_keyboard(user_id):
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔍 Найти матч"))
    builder.add(KeyboardButton(text="👤 Мой профиль"))
    builder.add(KeyboardButton(text="📝 Тикет поддержки"))
    builder.add(KeyboardButton(text="📢 Канал фейсита"))
    builder.add(KeyboardButton(text="🏆 Топ игроков"))
    user = await db.get_user(user_id)
    if not user or not user[2] or not user[3]:
        builder.add(KeyboardButton(text="📋 Регистрация"))
    if user and (user[10] == 1 or await is_super_admin(user_id)):
        builder.add(KeyboardButton(text="⚙️ Админ-панель"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    await db.register_user(user_id, username)

    if not await check_subscription(user_id):
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_LINK))
        kb.add(InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub"))
        await message.answer("❌ Подпишитесь на канал @testhp404bot", reply_markup=kb.as_markup())
        return

    user = await db.get_user(user_id)
    if not user or not user[2] or not user[3]:
        await message.answer("👋 Добро пожаловать! Пройдите регистрацию, нажав «📋 Регистрация»",
                             reply_markup=await get_main_keyboard(user_id))
    else:
        await message.answer(f"👋 С возвращением, {user[2]}!", reply_markup=await get_main_keyboard(user_id))

# Проверка подписки (callback)
@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("✅ Подписка подтверждена!")
        user = await db.get_user(callback.from_user.id)
        if not user or not user[2] or not user[3]:
            await callback.message.answer("Пройдите регистрацию, нажав «📋 Регистрация»",
                                          reply_markup=await get_main_keyboard(callback.from_user.id))
        else:
            await callback.message.answer(f"Добро пожаловать, {user[2]}!", reply_markup=await get_main_keyboard(callback.from_user.id))
    else:
        await callback.answer("❌ Вы ещё не подписаны!")

# ====== РЕГИСТРАЦИЯ ======
@dp.message(F.text == "📋 Регистрация")
async def reg_start(message: types.Message, state: FSMContext):
    await state.set_state(Registration.waiting_nickname)
    await message.answer("ℹ️ Введите свой ник в Standoff 2:")

@dp.message(Registration.waiting_nickname, F.text)
async def reg_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await state.set_state(Registration.waiting_game_id)
    await message.answer("🪪 Введите ваш игровой ID Standoff 2:")

@dp.message(Registration.waiting_game_id, F.text)
async def reg_game_id(message: types.Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    data = await state.get_data()
    await state.set_state(Registration.confirm)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="reg_confirm"))
    kb.add(InlineKeyboardButton(text="❌ Отмена", callback_data="reg_cancel"))
    await message.answer(f"Проверьте данные:\nНик: {data['nickname']}\nID: {data['game_id']}", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "reg_confirm")
async def reg_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.update_nickname(callback.from_user.id, data['nickname'])
    await db.update_game_id(callback.from_user.id, data['game_id'])
    await state.clear()
    await callback.message.edit_text("Регистрация завершена!")
    await callback.message.answer("Вы успешно зарегистрированы!", reply_markup=await get_main_keyboard(callback.from_user.id))

@dp.callback_query(F.data == "reg_cancel")
async def reg_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Регистрация отменена.")

# ====== ГЛАВНОЕ МЕНЮ ======
@dp.message(F.text == "🔍 Найти матч")
async def find_match(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🎮 Создать матч", callback_data="create_match"))
    kb.add(InlineKeyboardButton(text="📋 Мои лобби", callback_data="my_lobbies"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    await message.answer("Выберите действие:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Главное меню", reply_markup=await get_main_keyboard(callback.from_user.id))

@dp.message(F.text == "👤 Мой профиль")
async def profile(message: types.Message):
    u = await db.get_user(message.from_user.id)
    if not u:
        await message.answer("Сначала зарегистрируйтесь.")
        return
    rank = await db.get_user_rank(message.from_user.id)
    premium_status = "Есть" if u[8] == 1 else "Нет"
    text = (f"👤 {u[2]}\n"
            f"——————\n"
            f"⭐ Премиум: {premium_status}\n"
            f"ℹ️ Эло:\n"
            f"Соревновательный: {u[4]}\n"
            f"Напарники: {u[5]}\n"
            f"Дуэль: {u[6]}\n"
            f"🏆 Побед: {u[7]}\n"
            f"🏆 Место в топе: #{rank}")
    await message.answer(text)

@dp.message(F.text == "📝 Тикет поддержки")
async def ticket_start(message: types.Message, state: FSMContext):
    await state.set_state(Ticket.waiting_text)
    await message.answer("Опишите проблему:")

@dp.message(Ticket.waiting_text, F.text)
async def ticket_received(message: types.Message, state: FSMContext):
    await db.create_ticket(message.from_user.id, message.from_user.username, message.text)
    await state.clear()
    await message.answer("✅ Тикет создан! Администраторы рассмотрят его.")

@dp.message(F.text == "📢 Канал фейсита")
async def channel_link(message: types.Message):
    await message.answer(f"Канал: {CHANNEL_LINK}")

@dp.message(F.text == "🏆 Топ игроков")
async def top_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Соревновательный", callback_data="top_competitive"))
    kb.add(InlineKeyboardButton(text="Напарники", callback_data="top_duo"))
    kb.add(InlineKeyboardButton(text="Дуэль", callback_data="top_duel"))
    kb.add(InlineKeyboardButton(text="Все общее", callback_data="top_all"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    kb.adjust(2)
    await message.answer("Выберите режим топа:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("top_"))
async def show_top(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    players = await db.get_top_players(mode)
    medals = ["🥇", "🥈", "🥉"] + [f"TOP {i}" for i in range(4, 11)]
    txt = "ℹ️ Топ игроков | 404hp FACEIT\n——————\n"
    for i, p in enumerate(players):
        nick = p[2] or "Player"
        elo = round(p[3]) if mode == 'all' else p[3]
        txt += f"{medals[i]}: {nick} | {elo} ELO\n"
    txt += "——————\n"
    await callback.message.answer(txt)
    rank = await db.get_user_rank(callback.from_user.id, mode)
    await callback.message.answer(f"🏆 Ваше место: #{rank}")
    await callback.answer()

# ====== СОЗДАНИЕ МАТЧА ======
@dp.callback_query(F.data == "create_match")
async def create_match_start(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user or user[11] != 1:
        await callback.answer("Нет доступа. Обратитесь к @nelinner", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for mode in ['competitive', 'duo', 'duel']:
        kb.add(InlineKeyboardButton(text=MODE_NAMES[mode], callback_data=f"mode_{mode}"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    await callback.message.edit_text("Выберите режим:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("mode_"))
async def choose_map(callback: types.CallbackQuery):
    mode = callback.data[5:]
    kb = InlineKeyboardBuilder()
    for m in MAPS[mode]:
        kb.add(InlineKeyboardButton(text=m, callback_data=f"map_{mode}_{m}"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="create_match"))
    await callback.message.edit_text("Выберите карту:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("map_"))
async def map_selected(callback: types.CallbackQuery, state: FSMContext):
    _, mode, map_name = callback.data.split("_", 2)
    user_data = await db.get_user(callback.from_user.id)
    data = {'mode': mode, 'map': map_name, 'host_id': callback.from_user.id, 'host_nickname': user_data[2]}
    if mode == 'duo':
        await state.set_state(LobbyCreation.waiting_duo_partner)
        await state.update_data(data)
        await callback.message.edit_text("Введите ник напарника:")
    else:
        await state.set_state(LobbyCreation.confirm)
        await state.update_data(data)
        await show_lobby_confirmation(callback.message, data)

@dp.message(LobbyCreation.waiting_duo_partner, F.text)
async def duo_partner_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['duo_partner'] = message.text
    await state.set_state(LobbyCreation.confirm)
    await state.update_data(data)
    await show_lobby_confirmation(message, data)

async def show_lobby_confirmation(message, data):
    mode, map_name = data['mode'], data['map']
    rounds = ROUNDS[mode]
    text = (f"Вы выбрали: {MODE_NAMES[mode]}\n"
            f"Вот настройки данного режима\n"
            f"——————\n"
            f"🏞️ Maps: {map_name}\n"
            f"⚔️ Количество раундов: до {rounds}\n"
            f"ℹ️ Создавать лобби в турнир формате\n"
            f"💲 Баланс денег: 16К\n"
            f"——————\n"
            f"Если всё правильно, смело начинайте создавать лобби")
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_lobby"))
    kb.add(InlineKeyboardButton(text="❌ Вернуться", callback_data="cancel_lobby"))
    await message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "confirm_lobby")
async def confirm_lobby(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lobby_id = await db.create_lobby(data['host_id'], data['host_nickname'], data['mode'], data['map'], ROUNDS[data['mode']])
    user = await db.get_user(data['host_id'])
    elo_index = 4 + ['competitive', 'duo', 'duel'].index(data['mode'])
    await db.add_player_to_lobby(lobby_id, data['host_id'], data['host_nickname'], data['mode'], user[elo_index])
    if 'duo_partner' in data:
        await db.add_player_to_lobby(lobby_id, 0, data['duo_partner'], data['mode'], 1000, is_duo_partner=True)
    await create_lobby_post(callback.message.chat.id, lobby_id)
    await state.clear()
    await callback.message.edit_text("Лобби создано!")
    await callback.answer("Готово")

@dp.callback_query(F.data == "cancel_lobby")
async def cancel_lobby(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Создание лобби отменено.")

async def create_lobby_post(chat_id, lobby_id):
    lobby = await db.get_lobby(lobby_id)
    players = await db.get_lobby_players(lobby_id)
    txt = (f"ℹ️ Регистрация на матч | 404hp FACEIT\n"
           f"By host: {lobby[2]} | лобби #{lobby_id}\n"
           f"——————\n"
           f"[🏞️] Maps: {lobby[4]}\n"
           f"[⚔️] Режим: {MODE_NAMES[lobby[3]]}\n"
           f"——————\n"
           f"[👥] Игроки:\n")
    for p in players:
        prefix = ""
        if p[2]:
            u = await db.get_user(p[2])
            if u:
                if u[10] == 1: prefix = "🔴 "
                elif u[8] == 1: prefix = "⭐️ "
        txt += f"{prefix}{p[3]} | {p[5]} ELO\n"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🎮 Присоединиться", callback_data=f"join_{lobby_id}"))
    kb.add(InlineKeyboardButton(text="🔙 Выйти", callback_data=f"leave_{lobby_id}"))
    msg = await bot.send_message(CHANNEL_ID, txt, reply_markup=kb.as_markup())
    await db.update_lobby_message_id(lobby_id, msg.message_id)
    await bot.send_message(chat_id, "✅ Лобби создано и отправлено в канал!")

# ====== ПРИСОЕДИНЕНИЕ / ВЫХОД ======
@dp.callback_query(F.data.startswith("join_"))
async def join_lobby(callback: types.CallbackQuery):
    lobby_id = int(callback.data[5:])
    user_id = callback.from_user.id
    if await db.get_player_in_lobby(lobby_id, user_id):
        await callback.answer("Вы уже в этом лобби!")
        return
    u = await db.get_user(user_id)
    lobby = await db.get_lobby(lobby_id)
    mode = lobby[3]
    elo_index = 4 + ['competitive', 'duo', 'duel'].index(mode)
    await db.add_player_to_lobby(lobby_id, user_id, u[2], mode, u[elo_index])
    await update_lobby_post(lobby_id)
    players = await db.get_lobby_players(lobby_id)
    max_players = 10 if mode == 'competitive' else 4
    if len(players) >= max_players:
        await show_team_split(callback.message.chat.id, lobby_id)
    await callback.answer("Присоединились!")

@dp.callback_query(F.data.startswith("leave_"))
async def leave_lobby(callback: types.CallbackQuery):
    lobby_id = int(callback.data[6:])
    await db.remove_player_from_lobby(lobby_id, callback.from_user.id)
    await update_lobby_post(lobby_id)
    await callback.answer("Вы вышли из лобби")

async def update_lobby_post(lobby_id):
    lobby = await db.get_lobby(lobby_id)
    if not lobby or not lobby[6]: return
    players = await db.get_lobby_players(lobby_id)
    txt = (f"ℹ️ Регистрация на матч | 404hp FACEIT\n"
           f"By host: {lobby[2]} | лобби #{lobby_id}\n"
           f"——————\n"
           f"[🏞️] {lobby[4]}\n"
           f"[⚔️] {MODE_NAMES[lobby[3]]}\n"
           f"——————\n"
           f"[👥] Игроки:\n")
    for p in players:
        prefix = ""
        if p[2]:
            u = await db.get_user(p[2])
            if u:
                if u[10] == 1: prefix = "🔴 "
                elif u[8] == 1: prefix = "⭐️ "
        txt += f"{prefix}{p[3]} | {p[5]} ELO\n"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🎮 Присоединиться", callback_data=f"join_{lobby_id}"))
    kb.add(InlineKeyboardButton(text="🔙 Выйти", callback_data=f"leave_{lobby_id}"))
    try:
        await bot.edit_message_text(txt, CHANNEL_ID, lobby[6], reply_markup=kb.as_markup())
    except:
        pass

async def show_team_split(chat_id, lobby_id):
    players = await db.get_lobby_players(lobby_id)
    ct, t = [], []
    for i, p in enumerate(players):
        prefix = ""
        if p[2]:
            u = await db.get_user(p[2])
            if u:
                if u[10] == 1: prefix = "🔴 "
                elif u[8] == 1: prefix = "⭐️ "
        line = f"{prefix}{p[3]} | {p[5]} ELO"
        if i % 2 == 0:
            ct.append(line)
            await db.update_player_team(p[0], 'CT')
        else:
            t.append(line)
            await db.update_player_team(p[0], 'T')
    lobby = await db.get_lobby(lobby_id)
    txt = (f"ℹ️ Жеребьёвка | 404hp FACEIT\n"
           f"By host: {lobby[2]} | лобби #{lobby_id}\n"
           f"——————\n"
           f"⚔️ CT:\n" + "\n".join(ct) + "\n"
           f"🔫 T:\n" + "\n".join(t) + "\n"
           f"——————\n"
           f"Ожидайте ссылку от хоста")
    await bot.send_message(CHANNEL_ID, txt)
    await bot.send_message(chat_id, "Жеребьёвка проведена. Отправьте ссылку на лобби:")
    state = dp.fsm.get_context(chat_id=chat_id, user_id=chat_id)
    await state.set_state(LobbyLink.waiting_link)
    await state.update_data(lobby_id=lobby_id)

@dp.message(LobbyLink.waiting_link, F.text)
async def lobby_link_sent(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lobby_id = data['lobby_id']
    lobby = await db.get_lobby(lobby_id)
    txt = (f"ℹ️ Ссылка на лобби | 404hp FACEIT\n"
           f"By host: {lobby[2]} | лобби #{lobby_id}\n"
           f"——————\n"
           f"[🏞️] {lobby[4]}\n"
           f"[⚔️] {MODE_NAMES[lobby[3]]}\n"
           f"——————\n"
           f"🔗 {message.text}")
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔗 Присоединиться", url=message.text))
    await bot.send_message(CHANNEL_ID, txt, reply_markup=kb.as_markup())
    await message.answer("Ссылка отправлена в канал!")
    await state.clear()

# ====== МОИ ЛОББИ ======
@dp.callback_query(F.data == "my_lobbies")
async def my_lobbies(callback: types.CallbackQuery):
    lobbies = await db.get_user_lobbies(callback.from_user.id)
    if not lobbies:
        await callback.answer("У вас нет активных лобби", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for l in lobbies:
        kb.add(InlineKeyboardButton(text=f"#{l[0]} {MODE_NAMES[l[3]]} {l[4]}", callback_data=f"manage_{l[0]}"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    await callback.message.edit_text("Ваши лобби:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("manage_"))
async def manage_lobby(callback: types.CallbackQuery):
    lobby_id = int(callback.data[7:])
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="📊 Результаты", callback_data=f"result_{lobby_id}"))
    kb.add(InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{lobby_id}"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="my_lobbies"))
    await callback.message.edit_text("Управление лобби:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("result_"))
async def result_start(callback: types.CallbackQuery, state: FSMContext):
    lobby_id = int(callback.data[7:])
    await state.set_state(ResultSubmission.waiting_screenshot)
    await state.update_data(lobby_id=lobby_id)
    await callback.message.answer("Пришлите скриншот результата.")
    await callback.answer()

@dp.message(ResultSubmission.waiting_screenshot, F.photo)
async def screenshot_received(message: types.Message, state: FSMContext):
    await state.update_data(has_screenshot=True)
    await state.set_state(ResultSubmission.waiting_score)
    await message.answer("📊 Введите счёт матча (CT T):")

@dp.message(ResultSubmission.waiting_score, F.text)
async def score_entered(message: types.Message, state: FSMContext):
    try:
        scores = message.text.split()
        ct, t = int(scores[0]), int(scores[1])
        await state.update_data(score_ct=ct, score_t=t)
        await state.set_state(ResultSubmission.waiting_swap)
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔄 Да, поменялись", callback_data="swap_yes"))
        kb.add(InlineKeyboardButton(text="❌ Нет", callback_data="swap_no"))
        await message.answer("Поменялись игроки местами?", reply_markup=kb.as_markup())
    except:
        await message.answer("Неверный формат. Пример: 13 5")

@dp.callback_query(F.data.startswith("swap_"))
async def swap_decision(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    swapped = callback.data == "swap_yes"
    lobby_id = data['lobby_id']
    # Показываем результаты
    await show_match_results(callback.message.chat.id, lobby_id, data['score_ct'], data['score_t'], swapped)
    await state.clear()
    await callback.answer("Результаты зарегистрированы!")

async def show_match_results(chat_id, lobby_id, score_ct, score_t, swapped):
    players = await db.get_lobby_players(lobby_id)
    ct_players = [p for p in players if p[4] == 'CT']
    t_players = [p for p in players if p[4] == 'T']
    if swapped:
        ct_players, t_players = t_players, ct_players
    winner = "CT" if score_ct > score_t else "T"
    lobby = await db.get_lobby(lobby_id)
    txt = (f"ℹ️ Результаты | 404hp FACEIT\n"
           f"By host: {lobby[2]} | лобби #{lobby_id}\n"
           f"——————\n"
           f"⚔️ CT: {score_ct}\n")
    for p in ct_players:
        txt += f"{p[3]} | {p[5]} ELO\n"
    txt += f"\n🔫 T: {score_t}\n"
    for p in t_players:
        txt += f"{p[3]} | {p[5]} ELO\n"
    txt += f"——————\nПобедила команда: {winner}\n"
    mode = lobby[3]
    # Обновление ELO
    for p in ct_players:
        if p[2]:
            u = await db.get_user(p[2])
            change = 50 if u[8] == 1 else 25
            new_elo = p[5] + change if winner == 'CT' else p[5] - change
            await db.update_elo(p[2], mode, new_elo)
            if winner == 'CT':
                await db.add_win(p[2])
    for p in t_players:
        if p[2]:
            u = await db.get_user(p[2])
            change = 15 if u[8] == 1 else 25
            new_elo = p[5] + change if winner == 'T' else p[5] - change
            await db.update_elo(p[2], mode, new_elo)
            if winner == 'T':
                await db.add_win(p[2])
    await db.create_match(lobby_id, mode, lobby[4], score_ct, score_t, winner)
    await db.update_lobby_status(lobby_id, 'completed')
    await bot.send_message(chat_id, txt)

# ====== АДМИН-ПАНЕЛЬ ======
@dp.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user or (user[10] != 1 and not await is_super_admin(message.from_user.id)):
        await message.answer("Нет доступа.")
        return
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="📋 Тикеты", callback_data="admin_tickets"))
    kb.add(InlineKeyboardButton(text="🚫 Бан", callback_data="admin_ban"))
    kb.add(InlineKeyboardButton(text="✅ Разбан", callback_data="admin_unban"))
    kb.add(InlineKeyboardButton(text="⭐ Выдать премиум", callback_data="admin_premium_give"))
    kb.add(InlineKeyboardButton(text="⭐ Забрать премиум", callback_data="admin_premium_remove"))
    kb.add(InlineKeyboardButton(text="🟢 Выдать верификацию", callback_data="admin_verify_give"))
    kb.add(InlineKeyboardButton(text="🔴 Забрать верификацию", callback_data="admin_verify_remove"))
    if await is_super_admin(message.from_user.id):
        kb.add(InlineKeyboardButton(text="👑 Выдать админку", callback_data="admin_admin_give"))
        kb.add(InlineKeyboardButton(text="👑 Забрать админку", callback_data="admin_admin_remove"))
        kb.add(InlineKeyboardButton(text="🎮 Выдать доступ к играм", callback_data="admin_game_give"))
        kb.add(InlineKeyboardButton(text="🎮 Забрать доступ к играм", callback_data="admin_game_remove"))
    kb.adjust(2)
    await message.answer("Админ-панель:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: types.CallbackQuery):
    tickets = await db.get_open_tickets()
    if not tickets:
        await callback.message.answer("Нет открытых тикетов.")
    else:
        for t in tickets:
            await callback.message.answer(f"Тикет #{t[0]} от @{t[2]}: {t[3]}")
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_"))
async def admin_actions(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data[6:]  # ban, unban, premium_give, ...
    if action in ("admin_give", "admin_remove") and not await is_super_admin(callback.from_user.id):
        await callback.answer("Только для @nelinner", show_alert=True)
        return
    await state.set_state(AdminAction.waiting_username)
    await state.update_data(action=action)
    await callback.message.answer("Введите username:")
    await callback.answer()

@dp.message(AdminAction.waiting_username, F.text)
async def admin_username_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']
    username = message.text.strip().lstrip('@')
    target = await db.get_user_by_username(username)
    if not target:
        await message.answer("Пользователь не найден.")
        await state.clear()
        return
    tid = target[0]
    if action == "ban":
        await db.ban_user(tid)
        await message.answer(f"@{username} забанен.")
    elif action == "unban":
        await db.unban_user(tid)
        await message.answer(f"@{username} разбанен.")
    elif action == "premium_give":
        await db.set_premium(tid, 1)
        await message.answer(f"Премиум выдан @{username}.")
    elif action == "premium_remove":
        await db.set_premium(tid, 0)
        await message.answer(f"Премиум забран у @{username}.")
    elif action == "verify_give":
        await db.set_verified(tid, 1)
        await message.answer(f"Верификация выдана @{username}.")
    elif action == "verify_remove":
        await db.set_verified(tid, 0)
        await message.answer(f"Верификация забрана у @{username}.")
    elif action == "admin_give":
        await db.set_admin(tid, 1)
        await message.answer(f"Админка выдана @{username}.")
    elif action == "admin_remove":
        await db.set_admin(tid, 0)
        await message.answer(f"Админка забрана у @{username}.")
    elif action == "game_give":
        await db.set_can_create_lobby(tid, 1)
        await message.answer(f"Доступ к играм выдан @{username}.")
    elif action == "game_remove":
        await db.set_can_create_lobby(tid, 0)
        await message.answer(f"Доступ к играм забран у @{username}.")
    await state.clear()

# Запуск бота
async def main():
    await db.create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
