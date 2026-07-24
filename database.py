import aiosqlite

class Database:
    def __init__(self, db_file="faceit_bot.db"):
        self.db_file = db_file

    async def create_tables(self):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                nickname TEXT,
                game_id TEXT,
                elo_competitive INTEGER DEFAULT 1000,
                elo_duo INTEGER DEFAULT 1000,
                elo_duel INTEGER DEFAULT 1000,
                wins INTEGER DEFAULT 0,
                premium INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                can_create_lobby INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS lobbies (
                lobby_id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER, host_nickname TEXT, mode TEXT,
                map TEXT, rounds INTEGER, status TEXT DEFAULT 'waiting',
                message_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (host_id) REFERENCES users (user_id))''')
            await db.execute('''CREATE TABLE IF NOT EXISTS lobby_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lobby_id INTEGER, user_id INTEGER, nickname TEXT,
                team TEXT DEFAULT 'waiting', elo_mode TEXT, elo INTEGER,
                is_duo_partner INTEGER DEFAULT 0, duo_partner_nickname TEXT,
                FOREIGN KEY (lobby_id) REFERENCES lobbies (lobby_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id))''')
            await db.execute('''CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                lobby_id INTEGER, mode TEXT, map TEXT,
                score_ct INTEGER, score_t INTEGER, winner TEXT,
                status TEXT DEFAULT 'completed', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lobby_id) REFERENCES lobbies (lobby_id))''')
            await db.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, username TEXT, issue TEXT,
                status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id))''')
            await db.commit()

    # ----- Пользователи -----
    async def register_user(self, user_id, username):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone()

    async def get_user_by_username(self, username):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
            return await cursor.fetchone()

    async def update_nickname(self, user_id, nickname):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (nickname, user_id))
            await db.commit()

    async def update_game_id(self, user_id, game_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET game_id = ? WHERE user_id = ?", (game_id, user_id))
            await db.commit()

    async def update_elo(self, user_id, mode, new_elo):
        col = f"elo_{mode}"
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(f"UPDATE users SET {col} = ? WHERE user_id = ?", (new_elo, user_id))
            await db.commit()

    async def add_win(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET wins = wins + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def set_premium(self, user_id, status):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET premium = ? WHERE user_id = ?", (status, user_id))
            await db.commit()

    async def set_verified(self, user_id, status):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET verified = ? WHERE user_id = ?", (status, user_id))
            await db.commit()

    async def set_admin(self, user_id, status):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (status, user_id))
            await db.commit()

    async def set_can_create_lobby(self, user_id, status):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET can_create_lobby = ? WHERE user_id = ?", (status, user_id))
            await db.commit()

    async def ban_user(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def unban_user(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
            await db.commit()

    # ----- Лобби -----
    async def create_lobby(self, host_id, host_nickname, mode, map_name, rounds):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                "INSERT INTO lobbies (host_id, host_nickname, mode, map, rounds) VALUES (?,?,?,?,?)",
                (host_id, host_nickname, mode, map_name, rounds))
            await db.commit()
            return cursor.lastrowid

    async def get_lobby(self, lobby_id):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("SELECT * FROM lobbies WHERE lobby_id = ?", (lobby_id,))
            return await cursor.fetchone()

    async def get_user_lobbies(self, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                "SELECT * FROM lobbies WHERE host_id = ? AND status != 'completed' ORDER BY created_at DESC",
                (user_id,))
            return await cursor.fetchall()

    async def update_lobby_message_id(self, lobby_id, message_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE lobbies SET message_id = ? WHERE lobby_id = ?", (message_id, lobby_id))
            await db.commit()

    async def update_lobby_status(self, lobby_id, status):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE lobbies SET status = ? WHERE lobby_id = ?", (status, lobby_id))
            await db.commit()

    # ----- Игроки в лобби -----
    async def add_player_to_lobby(self, lobby_id, user_id, nickname, elo_mode, elo, is_duo_partner=False, duo_partner_nickname=None):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                "INSERT INTO lobby_players (lobby_id, user_id, nickname, elo_mode, elo, is_duo_partner, duo_partner_nickname) VALUES (?,?,?,?,?,?,?)",
                (lobby_id, user_id, nickname, elo_mode, elo, is_duo_partner, duo_partner_nickname))
            await db.commit()

    async def remove_player_from_lobby(self, lobby_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("DELETE FROM lobby_players WHERE lobby_id = ? AND user_id = ?", (lobby_id, user_id))
            await db.commit()

    async def get_lobby_players(self, lobby_id):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("SELECT * FROM lobby_players WHERE lobby_id = ?", (lobby_id,))
            return await cursor.fetchall()

    async def update_player_team(self, player_id, team):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE lobby_players SET team = ? WHERE id = ?", (team, player_id))
            await db.commit()

    async def get_player_in_lobby(self, lobby_id, user_id):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("SELECT * FROM lobby_players WHERE lobby_id = ? AND user_id = ?", (lobby_id, user_id))
            return await cursor.fetchone()

    # ----- Матчи -----
    async def create_match(self, lobby_id, mode, map_name, score_ct, score_t, winner):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                "INSERT INTO matches (lobby_id, mode, map, score_ct, score_t, winner) VALUES (?,?,?,?,?,?)",
                (lobby_id, mode, map_name, score_ct, score_t, winner))
            await db.commit()

    # ----- Топ -----
    async def get_top_players(self, mode='all', limit=10):
        async with aiosqlite.connect(self.db_file) as db:
            if mode == 'all':
                cursor = await db.execute(
                    "SELECT user_id, username, nickname, (elo_competitive+elo_duo+elo_duel)/3 as avg_elo FROM users WHERE is_banned=0 ORDER BY avg_elo DESC LIMIT ?",
                    (limit,))
            else:
                col = f"elo_{mode}"
                cursor = await db.execute(
                    f"SELECT user_id, username, nickname, {col} as elo FROM users WHERE is_banned=0 ORDER BY {col} DESC LIMIT ?",
                    (limit,))
            return await cursor.fetchall()

    async def get_user_rank(self, user_id, mode='all'):
        async with aiosqlite.connect(self.db_file) as db:
            if mode == 'all':
                cursor = await db.execute(
                    "SELECT COUNT(*)+1 FROM users WHERE is_banned=0 AND (elo_competitive+elo_duo+elo_duel)/3 > (SELECT (elo_competitive+elo_duo+elo_duel)/3 FROM users WHERE user_id=?)",
                    (user_id,))
            else:
                col = f"elo_{mode}"
                cursor = await db.execute(
                    f"SELECT COUNT(*)+1 FROM users WHERE is_banned=0 AND {col} > (SELECT {col} FROM users WHERE user_id=?)",
                    (user_id,))
            row = await cursor.fetchone()
            return row[0]

    # ----- Тикеты -----
    async def create_ticket(self, user_id, username, issue):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                "INSERT INTO support_tickets (user_id, username, issue) VALUES (?,?,?)",
                (user_id, username, issue))
            await db.commit()
            return cursor.lastrowid

    async def get_open_tickets(self):
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute("SELECT * FROM support_tickets WHERE status='open' ORDER BY created_at")
            return await cursor.fetchall()

    async def close_ticket(self, ticket_id):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("UPDATE support_tickets SET status='closed' WHERE ticket_id=?", (ticket_id,))
            await db.commit()
