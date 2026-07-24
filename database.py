import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file="faceit_bot.db"):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица лобби
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lobbies (
                lobby_id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER,
                host_nickname TEXT,
                mode TEXT,
                map TEXT,
                rounds INTEGER,
                status TEXT DEFAULT 'waiting',
                message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (host_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица игроков в лобби
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lobby_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lobby_id INTEGER,
                user_id INTEGER,
                nickname TEXT,
                team TEXT DEFAULT 'waiting',
                elo_mode TEXT,
                elo INTEGER,
                is_duo_partner INTEGER DEFAULT 0,
                duo_partner_nickname TEXT,
                FOREIGN KEY (lobby_id) REFERENCES lobbies (lobby_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица матчей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                lobby_id INTEGER,
                mode TEXT,
                map TEXT,
                score_ct INTEGER,
                score_t INTEGER,
                winner TEXT,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lobby_id) REFERENCES lobbies (lobby_id)
            )
        ''')

        # Таблица тикетов поддержки
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                issue TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        self.connection.commit()

    # Методы для пользователей
    def register_user(self, user_id, username):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        self.connection.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def get_user_by_username(self, username):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def update_nickname(self, user_id, nickname):
        self.cursor.execute(
            "UPDATE users SET nickname = ? WHERE user_id = ?",
            (nickname, user_id)
        )
        self.connection.commit()

    def update_game_id(self, user_id, game_id):
        self.cursor.execute(
            "UPDATE users SET game_id = ? WHERE user_id = ?",
            (game_id, user_id)
        )
        self.connection.commit()

    def update_elo(self, user_id, mode, new_elo):
        elo_column = f"elo_{mode}"
        self.cursor.execute(
            f"UPDATE users SET {elo_column} = ? WHERE user_id = ?",
            (new_elo, user_id)
        )
        self.connection.commit()

    def add_win(self, user_id):
        self.cursor.execute(
            "UPDATE users SET wins = wins + 1 WHERE user_id = ?",
            (user_id,)
        )
        self.connection.commit()

    def set_premium(self, user_id, status):
        self.cursor.execute(
            "UPDATE users SET premium = ? WHERE user_id = ?",
            (status, user_id)
        )
        self.connection.commit()

    def set_verified(self, user_id, status):
        self.cursor.execute(
            "UPDATE users SET verified = ? WHERE user_id = ?",
            (status, user_id)
        )
        self.connection.commit()

    def set_admin(self, user_id, status):
        self.cursor.execute(
            "UPDATE users SET is_admin = ? WHERE user_id = ?",
            (status, user_id)
        )
        self.connection.commit()

    def set_can_create_lobby(self, user_id, status):
        self.cursor.execute(
            "UPDATE users SET can_create_lobby = ? WHERE user_id = ?",
            (status, user_id)
        )
        self.connection.commit()

    def ban_user(self, user_id):
        self.cursor.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?",
            (user_id,)
        )
        self.connection.commit()

    def unban_user(self, user_id):
        self.cursor.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?",
            (user_id,)
        )
        self.connection.commit()

    # Методы для лобби
    def create_lobby(self, host_id, host_nickname, mode, map_name, rounds):
        self.cursor.execute(
            "INSERT INTO lobbies (host_id, host_nickname, mode, map, rounds) VALUES (?, ?, ?, ?, ?)",
            (host_id, host_nickname, mode, map_name, rounds)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def get_lobby(self, lobby_id):
        self.cursor.execute("SELECT * FROM lobbies WHERE lobby_id = ?", (lobby_id,))
        return self.cursor.fetchone()

    def get_user_lobbies(self, user_id):
        self.cursor.execute(
            "SELECT * FROM lobbies WHERE host_id = ? AND status != 'completed' ORDER BY created_at DESC",
            (user_id,)
        )
        return self.cursor.fetchall()

    def update_lobby_message_id(self, lobby_id, message_id):
        self.cursor.execute(
            "UPDATE lobbies SET message_id = ? WHERE lobby_id = ?",
            (message_id, lobby_id)
        )
        self.connection.commit()

    def update_lobby_status(self, lobby_id, status):
        self.cursor.execute(
            "UPDATE lobbies SET status = ? WHERE lobby_id = ?",
            (status, lobby_id)
        )
        self.connection.commit()

    # Методы для игроков в лобби
    def add_player_to_lobby(self, lobby_id, user_id, nickname, elo_mode, elo, is_duo_partner=False, duo_partner_nickname=None):
        self.cursor.execute(
            "INSERT INTO lobby_players (lobby_id, user_id, nickname, elo_mode, elo, is_duo_partner, duo_partner_nickname) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (lobby_id, user_id, nickname, elo_mode, elo, is_duo_partner, duo_partner_nickname)
        )
        self.connection.commit()

    def remove_player_from_lobby(self, lobby_id, user_id):
        self.cursor.execute(
            "DELETE FROM lobby_players WHERE lobby_id = ? AND user_id = ?",
            (lobby_id, user_id)
        )
        self.connection.commit()

    def get_lobby_players(self, lobby_id):
        self.cursor.execute(
            "SELECT * FROM lobby_players WHERE lobby_id = ?",
            (lobby_id,)
        )
        return self.cursor.fetchall()

    def update_player_team(self, player_id, team):
        self.cursor.execute(
            "UPDATE lobby_players SET team = ? WHERE id = ?",
            (team, player_id)
        )
        self.connection.commit()

    def get_player_in_lobby(self, lobby_id, user_id):
        self.cursor.execute(
            "SELECT * FROM lobby_players WHERE lobby_id = ? AND user_id = ?",
            (lobby_id, user_id)
        )
        return self.cursor.fetchone()

    # Методы для матчей
    def create_match(self, lobby_id, mode, map_name, score_ct, score_t, winner):
        self.cursor.execute(
            "INSERT INTO matches (lobby_id, mode, map, score_ct, score_t, winner) VALUES (?, ?, ?, ?, ?, ?)",
            (lobby_id, mode, map_name, score_ct, score_t, winner)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    # Методы для топ игроков
    def get_top_players(self, mode='all', limit=10):
        if mode == 'all':
            self.cursor.execute(
                "SELECT user_id, username, nickname, (elo_competitive + elo_duo + elo_duel) / 3 as avg_elo FROM users WHERE is_banned = 0 ORDER BY avg_elo DESC LIMIT ?",
                (limit,)
            )
        else:
            elo_column = f"elo_{mode}"
            self.cursor.execute(
                f"SELECT user_id, username, nickname, {elo_column} as elo FROM users WHERE is_banned = 0 ORDER BY {elo_column} DESC LIMIT ?",
                (limit,)
            )
        return self.cursor.fetchall()

    def get_user_rank(self, user_id, mode='all'):
        if mode == 'all':
            self.cursor.execute(
                "SELECT COUNT(*) + 1 FROM users WHERE is_banned = 0 AND (elo_competitive + elo_duo + elo_duel) / 3 > (SELECT (elo_competitive + elo_duo + elo_duel) / 3 FROM users WHERE user_id = ?)",
                (user_id,)
            )
        else:
            elo_column = f"elo_{mode}"
            self.cursor.execute(
                f"SELECT COUNT(*) + 1 FROM users WHERE is_banned = 0 AND {elo_column} > (SELECT {elo_column} FROM users WHERE user_id = ?)",
                (user_id,)
            )
        return self.cursor.fetchone()[0]

    # Методы для тикетов поддержки
    def create_ticket(self, user_id, username, issue):
        self.cursor.execute(
            "INSERT INTO support_tickets (user_id, username, issue) VALUES (?, ?, ?)",
            (user_id, username, issue)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def get_open_tickets(self):
        self.cursor.execute(
            "SELECT * FROM support_tickets WHERE status = 'open' ORDER BY created_at"
        )
        return self.cursor.fetchall()

    def close_ticket(self, ticket_id):
        self.cursor.execute(
            "UPDATE support_tickets SET status = 'closed' WHERE ticket_id = ?",
            (ticket_id,)
        )
        self.connection.commit()

    def close(self):
        self.connection.close()
