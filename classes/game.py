from classes.logger import Logger
import sqlite3, os, re, math
import datetime as dt


class Game(Logger):
    def __init__(self, backup_dest, db_loc) -> None:
        """
        Game class that allows setting the current game info up.
        """
        self.backup_dest = backup_dest
        # database creation
        self.db_loc = db_loc
        self.database = sqlite3.connect(db_loc)
        self.cursor = self.database.cursor()
        main = "CREATE TABLE IF NOT EXISTS games"
        args = "(game_name TEXT, save_location TEXT, last_backup TEXT, previous_backup_hash TEXT)"
        self.cursor.execute(main + args)
        self.total_executions = 1

    def database_check(self):
        """
        Checks for no longer existing save directories from the database and
        allows showing the missing entries for fixing.
        """
        self.cursor.execute("SELECT game_name, save_location FROM games")
        self.total_executions += 1
        return [
            name
            for name, save_location in self.cursor.fetchall()
            if not os.path.exists(save_location)
        ]

    def sorted_games(self):
        """
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        """
        self.cursor.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        data = self.cursor.fetchall()
        self.total_executions += 1
        return [name[0] for name in data]

    @staticmethod
    def get_dir_size(directory):
        """
        Converts size of `directory` to best fitting unit of measure.
        """
        total_size = 0
        for path, dirs, files in os.walk(directory):
            for f in files:
                fp = os.path.join(path, f)
                total_size += os.path.getsize(fp)
        if total_size > 0:
            size_name = ("B", "KB", "MB", "GB", "TB")
            try:
                i = int(math.floor(math.log(total_size, 1024)))
                p = math.pow(1024, i)
                s = round(total_size / p, 2)
                return f"{s} {size_name[i]}"
            except ValueError:
                return "0 bits"
        else:
            return "0 bits"

    def get_filename(self, name):
        """
        Removes illegal characters and shortens `name` so it can become a valid filename.
        """
        name = re.sub(r"[^A-Za-z0-9'(){}\s]+", "", name.replace("&", "and")).strip()
        return re.sub("\s\s+", " ", name)[0:50]  # remvoes duplicate spaces and returns

    def get_game_info(self, game_name):
        """
        Returns the save location and last backup of `game_name` from the SQLite Database.
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
        else:
            return None, None

    # TODO delete once not needed
    def exists_in_db(self, game_name):
        """
        Checks if `game_name` is already in the database.
        """
        query = "SELECT save_location FROM games WHERE game_name=:game_name"
        args = {"game_name": game_name}
        self.cursor.execute(query, args)
        entry = self.cursor.fetchone()
        self.total_executions += 1
        return entry != None

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

    def set(self, game_name):
        """
        Sets the current game to `game_name`.
        """
        self.name = game_name
        data = self.get_game_info(game_name)
        self.save_location = data["save_location"]
        self.last_backup = data["last_backup"]
        self.previous_backup_hash = data["previous_backup_hash"]
        self.filename = self.get_filename(game_name)
        self.backup_loc = os.path.join(self.backup_dest, self.filename)
        self.backup_size = self.get_dir_size(self.backup_loc)

    def update(self, old_name, new_name, new_save):
        """
        Updates a game data in the database with `old_name` to `new_name` and `new_save`.
        """
        query = "UPDATE games SET game_name = ?, save_location = ? WHERE game_name = ?;"
        args = (new_name, new_save, old_name)
        self.cursor.execute(query, args)
        self.database.commit()
        self.set(new_name)
        self.total_executions += 1

    def add(self, game_name, save_location):
        """
        Adds game to database with `game_name`, `save_location` data.
        """
        query = "INSERT INTO games VALUES (:game_name, :save_location, :last_backup)"
        args = {
            "game_name": game_name,
            "save_location": save_location,
            "last_backup": "Never",
            "previous_backup_hash": 0,
        }
        self.cursor.execute(query, args)
        self.database.commit()
        self.logger.info(f"Added {game_name} to database.")
        self.total_executions += 1

    def delete_from_db(self):
        """
        Deletes selected game from SQLite Database.
        """
        self.cursor.execute(
            "DELETE FROM games WHERE game_name = :game_name", {"game_name": self.name}
        )
        self.database.commit()
        self.total_executions += 1

    def close_database(self):
        """
        Closes the database.
        """
        self.database.close()
        print(f"Database closed after {self.total_executions} excecutions")
