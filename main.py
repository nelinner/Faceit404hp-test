import telebot
from telebot import types
from database import Database
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8254209430:AAHrYF_5KJCA77-4nYpCaleisJckxUtCMLY"
CHANNEL_ID = "@testhp404bot"
CHANNEL_LINK = "https://t.me/testhp404bot"
SUPER_ADMIN_USERNAME = "nelinner"  # руководитель проекта

bot = telebot.TeleBot(TOKEN)
db = Database()

# Временное хранилище состояний пользователей
user_states = {}

class UserState:
    def __init__(self, state, data=None):
        self.state = state
        self.data = data or {}

# Карты и режимы
MAPS = {
    'competitive': ['Sandstone', 'Zone 9', 'Rust', 'Dune', 'Training Outside'],
    'duo': ['Sandstone', 'Zone 9', 'Province', 'Breeze'],
    'duel': ['Sandstone', 'Zone 9', 'Arena']
}

MODE_NAMES = {
    'competitive': 'Соревновательный',
    'duo': 'Напарники',
    'duel': 'Дуэль'
}

ROUNDS = {
    'competitive': 13,
    'duo': 9,
    'duel': 9
}

# Проверка подписки на канал
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Проверка, является ли пользователь руководителем @nelinner
def is_super_admin(user_id):
    user = db.get_user(user_id)
    if user and user[1] == SUPER_ADMIN_USERNAME:
        return True
    return False

# Главное меню
def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🔍 Найти матч"),
        types.KeyboardButton("👤 Мой профиль"),
        types.KeyboardButton("📝 Тикет поддержки"),
        types.KeyboardButton("📢 Канал фейсита"),
        types.KeyboardButton("🏆 Топ игроков")
    )
    user = db.get_user(user_id)
    if not user or not user[2] or not user[3]:
        markup.add(types.KeyboardButton("📋 Регистрация"))
    if user and (user[10] == 1 or is_super_admin(user_id)):  # is_admin = индекс 10
        markup.add(types.KeyboardButton("⚙️ Админ-панель"))
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    db.register_user(user_id, username)

    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
        bot.send_message(
            message.chat.id,
            "❌ Для использования бота необходимо подписаться на канал @testhp404bot",
            reply_markup=markup
        )
        return

    user = db.get_user(user_id)
    if not user or not user[2] or not user[3]:
        bot.send_message(message.chat.id, "👋 Добро пожаловать! Пройдите регистрацию, нажав кнопку «📋 Регистрация»",
                         reply_markup=get_main_keyboard(user_id))
    else:
        bot.send_message(message.chat.id, f"👋 С возвращением, {user[2]}!",
                         reply_markup=get_main_keyboard(user_id))

# Проверка подписки (callback)
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.edit_message_text("✅ Подписка подтверждена!", call.message.chat.id, call.message.message_id)
        user = db.get_user(user_id)
        if not user or not user[2] or not user[3]:
            bot.send_message(call.message.chat.id, "Пройдите регистрацию, нажав «📋 Регистрация»",
                             reply_markup=get_main_keyboard(user_id))
        else:
            bot.send_message(call.message.chat.id, f"Добро пожаловать, {user[2]}!",
                             reply_markup=get_main_keyboard(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ Вы ещё не подписаны!")

# Обработка текстовых сообщений
@bot.message_handler(content_types=['text', 'photo'])
def handle_text(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Проверить", callback_data="check_sub"))
        bot.send_message(message.chat.id, "❌ Необходимо подписаться на канал!", reply_markup=markup)
        return

    # Обработка состояний
    if user_id in user_states:
        state = user_states[user_id]
        if state.state == "waiting_nickname" and message.content_type == 'text':
            state.data['nickname'] = message.text
            user_states[user_id] = UserState("waiting_game_id", state.data)
            bot.send_message(message.chat.id, "🪪 Введите ваш игровой ID Standoff 2:")
            return
        elif state.state == "waiting_game_id" and message.content_type == 'text':
            state.data['game_id'] = message.text
            user_states[user_id] = UserState("confirm_registration", state.data)
            info = f"ℹ️ Проверьте данные:\nНик: {state.data['nickname']}\nID: {state.data['game_id']}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Подтвердить", callback_data="reg_confirm"))
            markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="reg_cancel"))
            bot.send_message(message.chat.id, info, reply_markup=markup)
            return
        elif state.state == "waiting_duo_partner" and message.content_type == 'text':
            state.data['duo_partner'] = message.text
            user_states[user_id] = UserState("confirm_lobby", state.data)
            show_lobby_confirmation(message.chat.id, state.data)
            return
        elif state.state == "waiting_screenshot":
            if message.photo:
                state.data['has_screenshot'] = True
                bot.send_message(message.chat.id, "📊 Введите счёт матча (CT T):")
                user_states[user_id] = UserState("waiting_match_score", state.data)
            else:
                bot.send_message(message.chat.id, "Отправьте скриншот изображением.")
            return
        elif state.state == "waiting_match_score" and message.content_type == 'text':
            try:
                scores = message.text.split()
                score_ct = int(scores[0])
                score_t = int(scores[1])
                state.data['score_ct'] = score_ct
                state.data['score_t'] = score_t
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔄 Да, поменялись", callback_data="swap_yes"))
                markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="swap_no"))
                bot.send_message(message.chat.id, "Поменялись игроки местами?", reply_markup=markup)
                user_states[user_id] = UserState("waiting_swap", state.data)
            except:
                bot.send_message(message.chat.id, "Неверный формат. Пример: 13 5")
            return
        elif state.state == "waiting_lobby_link" and message.content_type == 'text':
            lobby_id = state.data['lobby_id']
            show_lobby_link(message.chat.id, lobby_id, message.text)
            del user_states[user_id]
            return
        elif state.state == "waiting_ticket" and message.content_type == 'text':
            db.create_ticket(user_id, message.from_user.username, message.text)
            bot.send_message(message.chat.id, "✅ Тикет создан!")
            del user_states[user_id]
            return
        # Админские состояния
        elif state.state.startswith("waiting_"):
            admin_states = ["waiting_ban_username", "waiting_unban_username", "waiting_premium_username",
                            "waiting_verify_username", "waiting_admin_username", "waiting_game_access_username"]
            if state.state in admin_states and message.content_type == 'text':
                target = db.get_user_by_username(message.text)
                if not target:
                    bot.send_message(message.chat.id, "Пользователь не найден.")
                    del user_states[user_id]
                    return
                target_id = target[0]
                if state.state == "waiting_ban_username":
                    db.ban_user(target_id)
                    bot.send_message(message.chat.id, f"Пользователь @{message.text} забанен.")
                elif state.state == "waiting_unban_username":
                    db.unban_user(target_id)
                    bot.send_message(message.chat.id, f"Пользователь @{message.text} разбанен.")
                elif state.state == "waiting_premium_username":
                    action = state.data['action']
                    db.set_premium(target_id, 1 if action == 'give' else 0)
                    bot.send_message(message.chat.id, f"Премиум {'выдан' if action == 'give' else 'забран'} для @{message.text}.")
                elif state.state == "waiting_verify_username":
                    action = state.data['action']
                    db.set_verified(target_id, 1 if action == 'give' else 0)
                    bot.send_message(message.chat.id, f"Верификация {'выдана' if action == 'give' else 'забрана'} для @{message.text}.")
                elif state.state == "waiting_admin_username":
                    action = state.data['action']
                    db.set_admin(target_id, 1 if action == 'give' else 0)
                    bot.send_message(message.chat.id, f"Админка {'выдана' if action == 'give' else 'забрана'} для @{message.text}.")
                elif state.state == "waiting_game_access_username":
                    action = state.data['action']
                    db.set_can_create_lobby(target_id, 1 if action == 'give' else 0)
                    bot.send_message(message.chat.id, f"Доступ к играм {'выдан' if action == 'give' else 'забран'} для @{message.text}.")
                del user_states[user_id]
            return
        return

    # Основные кнопки меню
    if message.content_type != 'text':
        return
    text = message.text

    if text == "📋 Регистрация":
        user_states[user_id] = UserState("waiting_nickname", {})
        bot.send_message(message.chat.id, "ℹ️ Введите свой ник в Standoff 2:")
    elif text == "🔍 Найти матч":
        show_match_menu(message.chat.id, user_id)
    elif text == "👤 Мой профиль":
        show_profile(message.chat.id, user_id)
    elif text == "📝 Тикет поддержки":
        user_states[user_id] = UserState("waiting_ticket", {})
        bot.send_message(message.chat.id, "Опишите проблему:")
    elif text == "📢 Канал фейсита":
        bot.send_message(message.chat.id, f"Канал: {CHANNEL_LINK}")
    elif text == "🏆 Топ игроков":
        show_top_menu(message.chat.id)
    elif text == "⚙️ Админ-панель":
        user = db.get_user(user_id)
        if user and (user[10] == 1 or is_super_admin(user_id)):
            show_admin_panel(message.chat.id, user_id)
        else:
            bot.send_message(message.chat.id, "Нет доступа.")

# --- Вспомогательные функции ---
def show_match_menu(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎮 Создать матч", callback_data="create_match"),
        types.InlineKeyboardButton("📋 Мои лобби", callback_data="my_lobbies"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

def show_lobby_confirmation(chat_id, data):
    mode = data['mode']
    map_name = data['map']
    rounds = ROUNDS[mode]
    text = (
        f"Вы выбрали: {MODE_NAMES[mode]}\n"
        f"Вот настройки данного режима\n"
        f"——————\n"
        f"🏞️ Maps: {map_name}\n"
        f"⚔️ Количество раундов: до {rounds}\n"
        f"ℹ️ Создавать лобби в турнир формате\n"
        f"💲 Баланс денег: 16К\n"
        f"——————\n"
        f"Если всё правильно, смело начинайте создавать лобби"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_lobby"),
        types.InlineKeyboardButton("❌ Вернуться", callback_data="cancel_lobby")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

def show_profile(chat_id, user_id):
    u = db.get_user(user_id)
    if not u:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь.")
        return
    rank = db.get_user_rank(user_id)
    premium_status = "Есть" if u[8] == 1 else "Нет"  # premium = индекс 8
    text = (
        f"👤 {u[2]}\n"
        f"——————\n"
        f"⭐ Премиум: {premium_status}\n"
        f"ℹ️ Эло:\n"
        f"Соревновательный: {u[4]}\n"
        f"Напарники: {u[5]}\n"
        f"Дуэль: {u[6]}\n"
        f"🏆 Побед: {u[7]}\n"
        f"🏆 Место в топе: #{rank}"
    )
    bot.send_message(chat_id, text)

def show_top_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Соревновательный", callback_data="top_competitive"),
        types.InlineKeyboardButton("Напарники", callback_data="top_duo"),
        types.InlineKeyboardButton("Дуэль", callback_data="top_duel"),
        types.InlineKeyboardButton("Все общее", callback_data="top_all"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    bot.send_message(chat_id, "Выберите режим топа:", reply_markup=markup)

def show_top_players(chat_id, mode):
    players = db.get_top_players(mode)
    medals = ["🥇", "🥈", "🥉"] + [f"TOP {i}" for i in range(4, 11)]
    txt = "ℹ️ Топ игроков | 404hp FACEIT\n——————\n"
    for i, p in enumerate(players):
        nick = p[2] or "Player"
        elo = round(p[3]) if mode == 'all' else p[3]
        txt += f"{medals[i]}: {nick} | {elo} ELO\n"
    txt += "——————\n"
    bot.send_message(chat_id, txt)
    user_rank = db.get_user_rank(chat_id, mode)
    bot.send_message(chat_id, f"🏆 Ваше место: #{user_rank}")

# --- Лобби и матчи ---
def create_lobby_post(chat_id, lobby_id):
    lobby = db.get_lobby(lobby_id)
    players = db.get_lobby_players(lobby_id)
    txt = (
        f"ℹ️ Регистрация на матч | 404hp FACEIT\n"
        f"By host: {lobby[2]} | лобби #{lobby_id}\n"
        f"——————\n"
        f"[🏞️] Maps: {lobby[4]}\n"
        f"[⚔️] Режим: {MODE_NAMES[lobby[3]]}\n"
        f"——————\n"
        f"[👥] Игроки:\n"
    )
    for p in players:
        prefix = ""
        if p[2]:
            u = db.get_user(p[2])
            if u:
                if u[10] == 1:        # is_admin
                    prefix = "🔴 "
                elif u[8] == 1:       # premium
                    prefix = "⭐️ "
        txt += f"{prefix}{p[3]} | {p[5]} ELO\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎮 Присоединиться", callback_data=f"join_{lobby_id}"),
        types.InlineKeyboardButton("🔙 Выйти", callback_data=f"leave_{lobby_id}")
    )
    msg = bot.send_message(CHANNEL_ID, txt, reply_markup=markup)
    db.update_lobby_message_id(lobby_id, msg.message_id)
    bot.send_message(chat_id, "✅ Лобби создано и отправлено в канал!")

def update_lobby_post(lobby_id):
    lobby = db.get_lobby(lobby_id)
    if not lobby or not lobby[6]:
        return
    players = db.get_lobby_players(lobby_id)
    txt = (
        f"ℹ️ Регистрация на матч | 404hp FACEIT\n"
        f"By host: {lobby[2]} | лобби #{lobby_id}\n"
        f"——————\n"
        f"[🏞️] {lobby[4]}\n"
        f"[⚔️] {MODE_NAMES[lobby[3]]}\n"
        f"——————\n"
        f"[👥] Игроки:\n"
    )
    for p in players:
        prefix = ""
        if p[2]:
            u = db.get_user(p[2])
            if u:
                if u[10] == 1:
                    prefix = "🔴 "
                elif u[8] == 1:
                    prefix = "⭐️ "
        txt += f"{prefix}{p[3]} | {p[5]} ELO\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎮 Присоединиться", callback_data=f"join_{lobby_id}"),
        types.InlineKeyboardButton("🔙 Выйти", callback_data=f"leave_{lobby_id}")
    )
    try:
        bot.edit_message_text(txt, CHANNEL_ID, lobby[6], reply_markup=markup)
    except Exception as e:
        logger.error(f"Update lobby post error: {e}")

def show_team_split(chat_id, lobby_id):
    players = db.get_lobby_players(lobby_id)
    ct, t = [], []
    for i, p in enumerate(players):
        prefix = ""
        if p[2]:
            u = db.get_user(p[2])
            if u:
                if u[10] == 1:
                    prefix = "🔴 "
                elif u[8] == 1:
                    prefix = "⭐️ "
        line = f"{prefix}{p[3]} | {p[5]} ELO"
        if i % 2 == 0:
            ct.append(line)
            db.update_player_team(p[0], 'CT')
        else:
            t.append(line)
            db.update_player_team(p[0], 'T')
    lobby = db.get_lobby(lobby_id)
    txt = (
        f"ℹ️ Жеребьёвка | 404hp FACEIT\n"
        f"By host: {lobby[2]} | лобби #{lobby_id}\n"
        f"——————\n"
        f"⚔️ CT:\n" + "\n".join(ct) + "\n"
        f"🔫 T:\n" + "\n".join(t) + "\n"
        f"——————\n"
        f"Ожидайте ссылку от хоста"
    )
    bot.send_message(CHANNEL_ID, txt)
    bot.send_message(chat_id, "Жеребьёвка проведена. Отправьте ссылку на лобби:")
    user_states[chat_id] = UserState("waiting_lobby_link", {"lobby_id": lobby_id})

def show_lobby_link(chat_id, lobby_id, link):
    lobby = db.get_lobby(lobby_id)
    txt = (
        f"ℹ️ Ссылка на лобби | 404hp FACEIT\n"
        f"By host: {lobby[2]} | лобби #{lobby_id}\n"
        f"——————\n"
        f"[🏞️] {lobby[4]}\n"
        f"[⚔️] {MODE_NAMES[lobby[3]]}\n"
        f"——————\n"
        f"🔗 {link}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 Присоединиться", url=link))
    bot.send_message(CHANNEL_ID, txt, reply_markup=markup)
    bot.send_message(chat_id, "Ссылка отправлена в канал!")

def show_match_results(chat_id, lobby_id, score_ct, score_t, swapped):
    players = db.get_lobby_players(lobby_id)
    ct_players = [p for p in players if p[4] == 'CT']
    t_players = [p for p in players if p[4] == 'T']
    if swapped:
        ct_players, t_players = t_players, ct_players
    winner = "CT" if score_ct > score_t else "T"
    lobby = db.get_lobby(lobby_id)
    txt = (
        f"ℹ️ Результаты | 404hp FACEIT\n"
        f"By host: {lobby[2]} | лобби #{lobby_id}\n"
        f"——————\n"
        f"⚔️ CT: {score_ct}\n"
    )
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
            u = db.get_user(p[2])
            change = 50 if u[8] == 1 else 25  # premium
            new_elo = p[5] + change if winner == 'CT' else p[5] - change
            db.update_elo(p[2], mode, new_elo)
            if winner == 'CT':
                db.add_win(p[2])
    for p in t_players:
        if p[2]:
            u = db.get_user(p[2])
            change = 15 if u[8] == 1 else 25
            new_elo = p[5] + change if winner == 'T' else p[5] - change
            db.update_elo(p[2], mode, new_elo)
            if winner == 'T':
                db.add_win(p[2])

    db.create_match(lobby_id, mode, lobby[4], score_ct, score_t, winner)
    db.update_lobby_status(lobby_id, 'completed')
    bot.send_message(chat_id, txt)

# --- Callback обработчики ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    try:
        if data == "back_to_main":
            bot.send_message(call.message.chat.id, "Главное меню", reply_markup=get_main_keyboard(user_id))
            bot.answer_callback_query(call.id)
        elif data == "create_match":
            user = db.get_user(user_id)
            if not user or user[11] != 1:  # can_create_lobby
                bot.answer_callback_query(call.id, "Нет доступа. Обратитесь к @nelinner")
                return
            markup = types.InlineKeyboardMarkup()
            for mode in ['competitive', 'duo', 'duel']:
                markup.add(types.InlineKeyboardButton(MODE_NAMES[mode], callback_data=f"mode_{mode}"))
            markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
            bot.edit_message_text("Выберите режим:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        elif data.startswith("mode_"):
            mode = data[5:]
            markup = types.InlineKeyboardMarkup()
            for m in MAPS[mode]:
                markup.add(types.InlineKeyboardButton(m, callback_data=f"map_{mode}_{m}"))
            markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="create_match"))
            bot.edit_message_text("Выберите карту:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        elif data.startswith("map_"):
            _, mode, map_name = data.split("_", 2)
            user_data = db.get_user(user_id)
            state_data = {
                'mode': mode,
                'map': map_name,
                'host_id': user_id,
                'host_nickname': user_data[2]
            }
            if mode == 'duo':
                bot.edit_message_text("Введите ник напарника:", call.message.chat.id, call.message.message_id)
                user_states[user_id] = UserState("waiting_duo_partner", state_data)
            else:
                user_states[user_id] = UserState("confirm_lobby", state_data)
                show_lobby_confirmation(call.message.chat.id, state_data)
                bot.answer_callback_query(call.id, "Подтвердите создание лобби")
        elif data == "confirm_lobby":
            st = user_states.get(user_id)
            if st:
                d = st.data
                lobby_id = db.create_lobby(d['host_id'], d['host_nickname'], d['mode'], d['map'], ROUNDS[d['mode']])
                user = db.get_user(user_id)
                elo_index = 4 + ['competitive', 'duo', 'duel'].index(d['mode'])
                db.add_player_to_lobby(lobby_id, user_id, d['host_nickname'], d['mode'], user[elo_index])
                if 'duo_partner' in d:
                    db.add_player_to_lobby(lobby_id, 0, d['duo_partner'], d['mode'], 1000, is_duo_partner=True)
                create_lobby_post(call.message.chat.id, lobby_id)
                del user_states[user_id]
                bot.answer_callback_query(call.id, "Лобби создано")
        elif data == "cancel_lobby":
            if user_id in user_states:
                del user_states[user_id]
            bot.edit_message_text("Создание лобби отменено.", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        elif data.startswith("join_"):
            lobby_id = int(data[5:])
            u = db.get_user(user_id)
            if not db.get_player_in_lobby(lobby_id, user_id):
                mode = db.get_lobby(lobby_id)[3]
                elo_index = 4 + ['competitive', 'duo', 'duel'].index(mode)
                db.add_player_to_lobby(lobby_id, user_id, u[2], mode, u[elo_index])
                update_lobby_post(lobby_id)
                players = db.get_lobby_players(lobby_id)
                max_players = 10 if mode == 'competitive' else 4
                if len(players) >= max_players:
                    show_team_split(call.message.chat.id, lobby_id)
            bot.answer_callback_query(call.id, "Присоединились")
        elif data.startswith("leave_"):
            lobby_id = int(data[6:])
            db.remove_player_from_lobby(lobby_id, user_id)
            update_lobby_post(lobby_id)
            bot.answer_callback_query(call.id, "Вы вышли из лобби")
        elif data == "my_lobbies":
            lobbies = db.get_user_lobbies(user_id)
            markup = types.InlineKeyboardMarkup()
            for l in lobbies:
                markup.add(types.InlineKeyboardButton(
                    f"#{l[0]} {MODE_NAMES[l[3]]} {l[4]}",
                    callback_data=f"manage_{l[0]}"
                ))
            markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
            bot.edit_message_text("Ваши лобби:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        elif data.startswith("manage_"):
            lobby_id = int(data[7:])
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📊 Результаты", callback_data=f"result_{lobby_id}"),
                types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{lobby_id}"),
                types.InlineKeyboardButton("🔙 Назад", callback_data="my_lobbies")
            )
            bot.edit_message_text("Управление лобби:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        elif data.startswith("result_"):
            lobby_id = int(data[7:])
            user_states[user_id] = UserState("waiting_screenshot", {"lobby_id": lobby_id})
            bot.send_message(call.message.chat.id, "Пришлите скриншот результата.")
            bot.answer_callback_query(call.id)
        elif data.startswith("cancel_"):
            lobby_id = int(data[7:])
            db.update_lobby_status(lobby_id, 'cancelled')
            bot.send_message(call.message.chat.id, "Игра отменена.")
            bot.answer_callback_query(call.id)
        elif data in ["swap_yes", "swap_no"]:
            st = user_states.get(user_id)
            if st:
                show_match_results(
                    call.message.chat.id,
                    st.data['lobby_id'],
                    st.data['score_ct'],
                    st.data['score_t'],
                    data == "swap_yes"
                )
                del user_states[user_id]
            bot.answer_callback_query(call.id)
        elif data.startswith("top_"):
            mode = data[4:]
            show_top_players(call.message.chat.id, mode)
            bot.answer_callback_query(call.id)
        elif data == "reg_confirm":
            st = user_states.get(user_id)
            if st:
                db.update_nickname(user_id, st.data['nickname'])
                db.update_game_id(user_id, st.data['game_id'])
                del user_states[user_id]
                bot.send_message(call.message.chat.id, "Регистрация завершена!", reply_markup=get_main_keyboard(user_id))
                bot.answer_callback_query(call.id, "Готово")
        elif data == "reg_cancel":
            if user_id in user_states:
                del user_states[user_id]
            bot.send_message(call.message.chat.id, "Регистрация отменена.")
            bot.answer_callback_query(call.id)
        # Админ-панель
        elif data == "admin_tickets":
            tickets = db.get_open_tickets()
            if not tickets:
                bot.send_message(call.message.chat.id, "Нет открытых тикетов.")
            else:
                for t in tickets:
                    bot.send_message(call.message.chat.id, f"Тикет #{t[0]} от @{t[2]}: {t[3]}")
            bot.answer_callback_query(call.id)
        elif data == "admin_ban":
            user_states[user_id] = UserState("waiting_ban_username")
            bot.send_message(call.message.chat.id, "Введите username для бана:")
        elif data == "admin_unban":
            user_states[user_id] = UserState("waiting_unban_username")
            bot.send_message(call.message.chat.id, "Введите username для разбана:")
        elif data == "admin_premium_give":
            user_states[user_id] = UserState("waiting_premium_username", {"action": "give"})
            bot.send_message(call.message.chat.id, "Введите username для выдачи премиума:")
        elif data == "admin_premium_remove":
            user_states[user_id] = UserState("waiting_premium_username", {"action": "remove"})
            bot.send_message(call.message.chat.id, "Введите username для снятия премиума:")
        elif data == "admin_verify_give":
            user_states[user_id] = UserState("waiting_verify_username", {"action": "give"})
            bot.send_message(call.message.chat.id, "Введите username для верификации:")
        elif data == "admin_verify_remove":
            user_states[user_id] = UserState("waiting_verify_username", {"action": "remove"})
            bot.send_message(call.message.chat.id, "Введите username для снятия верификации:")
        elif data == "admin_admin_give":
            if not is_super_admin(user_id):
                bot.answer_callback_query(call.id, "Только для @nelinner")
                return
            user_states[user_id] = UserState("waiting_admin_username", {"action": "give"})
            bot.send_message(call.message.chat.id, "Введите username для выдачи админки:")
        elif data == "admin_admin_remove":
            if not is_super_admin(user_id):
                bot.answer_callback_query(call.id, "Только для @nelinner")
                return
            user_states[user_id] = UserState("waiting_admin_username", {"action": "remove"})
            bot.send_message(call.message.chat.id, "Введите username для снятия админки:")
        elif data == "admin_game_give":
            if not is_super_admin(user_id):
                bot.answer_callback_query(call.id, "Только для @nelinner")
                return
            user_states[user_id] = UserState("waiting_game_access_username", {"action": "give"})
            bot.send_message(call.message.chat.id, "Введите username для выдачи доступа к играм:")
        elif data == "admin_game_remove":
            if not is_super_admin(user_id):
                bot.answer_callback_query(call.id, "Только для @nelinner")
                return
            user_states[user_id] = UserState("waiting_game_access_username", {"action": "remove"})
            bot.send_message(call.message.chat.id, "Введите username для снятия доступа к играм:")
        else:
            bot.answer_callback_query(call.id, "Неизвестная команда")
    except Exception as e:
        logger.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")

def show_admin_panel(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Тикеты", callback_data="admin_tickets"),
        types.InlineKeyboardButton("🚫 Бан", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Разбан", callback_data="admin_unban"),
        types.InlineKeyboardButton("⭐ Выдать премиум", callback_data="admin_premium_give"),
        types.InlineKeyboardButton("⭐ Забрать премиум", callback_data="admin_premium_remove"),
        types.InlineKeyboardButton("🟢 Выдать верификацию", callback_data="admin_verify_give"),
        types.InlineKeyboardButton("🔴 Забрать верификацию", callback_data="admin_verify_remove")
    )
    if is_super_admin(user_id):
        markup.add(
            types.InlineKeyboardButton("👑 Выдать админку", callback_data="admin_admin_give"),
            types.InlineKeyboardButton("👑 Забрать админку", callback_data="admin_admin_remove"),
            types.InlineKeyboardButton("🎮 Выдать доступ к играм", callback_data="admin_game_give"),
            types.InlineKeyboardButton("🎮 Забрать доступ к играм", callback_data="admin_game_remove")
        )
    bot.send_message(chat_id, "Админ-панель:", reply_markup=markup)

if __name__ == "__main__":
    print("Бот запущен")
    bot.polling(none_stop=True)
