# standard library
import sqlite3
import datetime as dt

# local application imports
from utils.game import Game


class Database:
    def __init__(self, backup_folder, db_loc) -> None:
        """
        Game class that allows setting the current game info up.
        """
        self.backup_folder = backup_folder
        # database creation
        self.db_loc = db_loc
        self.database = sqlite3.connect(db_loc)
        self.cursor = self.database.cursor()
        query = """
            CREATE TABLE IF NOT EXISTS games
            (game_name TEXT, save_path TEXT, last_backup TEXT, previous_backup_hash TEXT)
        """
        self.cursor.execute(query)

    def sorted_games(self) -> list[str]:
        """
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        """
        query = "SELECT game_name, save_path FROM games ORDER BY last_backup DESC"
        self.cursor.execute(query)
        games = self.cursor.fetchall()
        return [game for game, _ in games]

    def update_last_backup(self, game_name: str) -> None:
        """
        Updates the last_backup time for `game_name` to the current datetime.
        """
        last_backup = dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        query = """
            UPDATE games
            SET last_backup = :last_backup
            WHERE game_name = :game_name
        """
        args = {"game_name": game_name, "last_backup": last_backup}
        self.cursor.execute(query, args)
        self.database.commit()

    def update_previous_backup_hash(self, game_name: str, hash: str) -> None:
        """
        Updates the last_backup time for `game_name` to the current datetime.
        """
        query = """
            UPDATE games
            SET previous_backup_hash = :hash
            WHERE game_name = :game_name
        """
        args = {"game_name": game_name, "hash": hash}
        self.cursor.execute(query, args)
        self.database.commit()

    def get_game(self, game_name: str) -> Game:
        """
        Gets a Game object by `game_name` from the SQLite Database.
        """
        query = """
            SELECT save_path, last_backup, previous_backup_hash
            FROM games
            WHERE game_name = :game_name
        """
        self.cursor.execute(query, {"game_name": game_name})
        row = self.cursor.fetchone()
        if row is None:
            return Game()

        return Game(
            game_name,
            save_path=row[0],
            last_backup=row[1],
            prev_backup_hash=row[2],
            backup_folder=self.backup_folder,
        )

    def update(self, old_name: str, new_name: str, new_save: str) -> tuple[str, str]:
        """
        Updates a game data in the database with `old_name` to `new_name` and `new_save` and returns new_name and new_save.
        """
        query = """
            UPDATE games
            SET game_name = ?, save_path = ?
            WHERE game_name = ?;
        """
        args = (new_name, new_save, old_name)
        self.cursor.execute(query, args)
        self.database.commit()
        return new_name, new_save

    def add(self, game_name: str, save_path: str) -> None:
        """
        Adds game to database with `game_name`, `save_path` data.
        """
        query = """
            INSERT INTO games
            VALUES (:game_name, :save_path, :last_backup, :previous_backup_hash)
        """
        args = {
            "game_name": game_name,
            "save_path": save_path,
            "last_backup": "Never",
            "previous_backup_hash": 0,
        }
        self.cursor.execute(query, args)
        self.database.commit()

    def delete_from_db(self, game_name: str) -> None:
        """
        Deletes selected game from SQLite Database.
        """
        query = """
            DELETE FROM games 
            WHERE game_name = :game_name
        """
        self.cursor.execute(query, {"game_name": game_name})
        self.database.commit()

    def close(self) -> None:
        """
        Closes the database.
        """
        self.database.close()
