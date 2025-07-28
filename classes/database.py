# standard library
import sqlite3
import datetime as dt

# local application imports
from classes.game import Game


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
        main = "CREATE TABLE IF NOT EXISTS games"
        args = "(game_name TEXT, save_location TEXT, last_backup TEXT, previous_backup_hash TEXT)"
        self.cursor.execute(main + args)
        self.total_executions = 1

    def sorted_games(self):
        """
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        """
        query = "SELECT game_name, save_location FROM games ORDER BY last_backup DESC"
        self.cursor.execute(query)
        games = self.cursor.fetchall()
        self.total_executions += 1
        games_list = []
        for name, _ in games:
            games_list.append(name)
        return games_list

    def get_game_info(self, game_name: str) -> dict:
        """
        Returns the save location and last backup of `game_name` from the
        SQLite Database.
        """
        self.cursor.execute(
            "SELECT save_location, last_backup, previous_backup_hash FROM games WHERE game_name=:game_name",
            {"game_name": game_name},
        )
        self.total_executions += 1
        game = self.cursor.fetchone()
        if game:
            return {
                "save_location": game[0],
                "last_backup": game[1],
                "previous_backup_hash": game[2],
            }
        return {}

    def update_last_backup(self, game_name):
        """
        Updates the last_backup time for `game_name` to the current datetime.
        """
        last_backup = dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        query = (
            "UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name"
        )
        args = {"game_name": game_name, "last_backup": last_backup}
        self.cursor.execute(query, args)
        self.total_executions += 1
        self.database.commit()

    def update_previous_backup_hash(self, game_name, hash):
        """
        Updates the last_backup time for `game_name` to the current datetime.
        """
        query = (
            "UPDATE games SET previous_backup_hash = :hash WHERE game_name = :game_name"
        )
        args = {"game_name": game_name, "hash": hash}
        self.cursor.execute(query, args)
        self.total_executions += 1
        self.database.commit()

    def get(self, game_name):
        """
        Sets the current game to `game_name`.
        """
        prev_data = self.get_game_info(game_name)
        self.save_location = prev_data.get("save_location", "")
        self.last_backup = prev_data.get("last_backup", "")
        self.prev_backup_hash = prev_data.get("previous_backup_hash", "")
        return Game(
            game_name,
            self.save_location,
            self.last_backup,
            self.prev_backup_hash,
            self.backup_folder,
        )

    def update(self, old_name, new_name, new_save):
        """
        Updates a game data in the database with `old_name` to `new_name` and `new_save`.
        """
        query = "UPDATE games SET game_name = ?, save_location = ? WHERE game_name = ?;"
        args = (new_name, new_save, old_name)
        self.cursor.execute(query, args)
        self.database.commit()
        self.get(new_name)
        self.total_executions += 1

    def add(self, game_name, save_location):
        """
        Adds game to database with `game_name`, `save_location` data.
        """
        query = "INSERT INTO games VALUES (:game_name, :save_location, :last_backup, :previous_backup_hash)"
        args = {
            "game_name": game_name,
            "save_location": save_location,
            "last_backup": "Never",
            "previous_backup_hash": 0,
        }
        self.cursor.execute(query, args)
        self.database.commit()
        self.total_executions += 1

    def delete_from_db(self, game_name):
        """
        Deletes selected game from SQLite Database.
        """
        self.cursor.execute(
            "DELETE FROM games WHERE game_name = :game_name",
            {"game_name": game_name},
        )
        self.database.commit()
        self.total_executions += 1

    def close_database(self):
        """
        Closes the database.
        """
        self.database.close()
        print(f"Database closed after {self.total_executions} excecutions")
