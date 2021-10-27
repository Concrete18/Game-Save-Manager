from classes.logger import Logger
from contextlib import closing
import sqlite3, os, re, math
import datetime as dt


class Game(Logger):


    def __init__(self, backup_dest, db_loc) -> None:
        '''
        Game class that allows setting the current game info up.
        '''
        self.backup_dest = backup_dest
        # database creation
        self.db_loc = db_loc
        self.database = sqlite3.connect(db_loc)
        self.cursor = self.database.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
            game_name text,
            save_location text,
            last_backup text
            )'''
        )


    def query(self, sql, arg1=None, fetchall=False):
        '''
        Querys info in the database using the sql command.
        `arg1` can be used for add args to excute and `fetchall` as true to fetchall instead of fetchone.
        '''
        with closing(sqlite3.connect(self.db_loc)) as con, con, \
                closing(con.cursor()) as cur:
            if arg1 == None:
                cur.execute(sql)
            else:
                cur.execute(sql, arg1)
            if fetchall:
                return cur.fetchall()
            else:
                return cur.fetchone()

    def update_sql(self, sql, arg1=None):
        '''
        Allows updating using the `sql` command with opitional `arg1`.
        '''
        with closing(sqlite3.connect(self.db_loc)) as con, con, \
                closing(con.cursor()) as cur:
            if arg1 == None:
                cur.execute(sql)
            else:
                cur.execute(sql, arg1)

    def database_check(self):
        '''
        Checks for no longer existing save directories from the database and
        allows showing the missing entries for fixing.
        '''
        with closing(sqlite3.connect(self.db_loc)) as con, con, \
            closing(con.cursor()) as cur:
            cur.execute("SELECT game_name, save_location FROM games")
            return [name for name, save_location in cur.fetchall() if not os.path.isdir(save_location)]

    def sorted_games(self):
        '''
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        '''
        data = self.query("SELECT game_name FROM games ORDER BY last_backup DESC", fetchall=True)
        return [name[0] for name in data]

    @staticmethod
    def convert_size(directory):
        '''
        Converts size of `directory` to best fitting unit of measure.
        '''
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
                return f'{s} {size_name[i]}'
            except ValueError:
                return '0 bits'
        else:
            return '0 bits'
    
    def get_backup_size(self):
        '''
        Gets the size of the currently selected games backup folder.
        '''
        self.backup_size = self.convert_size(self.backup_loc)

    def get_filename(self, name):
        '''
        Removes illegal characters and shortens `name` so it can become a valid filename.
        '''
        name.replace('&', 'and')
        allowed_filename_characters = '[^a-zA-Z0-9.,\s]'
        char_removal = re.compile(allowed_filename_characters)
        string = char_removal.sub('', name)
        return re.sub("\s\s+" , " ", string).strip()[0:50]

    def get_game_info(self, game_name):
        '''
        Returns the save location and last backup of `game_name` from the SQLite Database.
        '''
        value = self.query("SELECT save_location, last_backup FROM games WHERE game_name=:game_name", 
            {'game_name': game_name})
        if len(value) > 0:
            return value[0], value[1]

    def update_last_backup(self, game_name):
        '''
        Updates the last_backup time for `game_name` to the current datetime.
        '''
        last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.update_sql("UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name",
            {'game_name': game_name, 'last_backup': last_backup})

    def set(self, game_name):
        '''
        Sets the current game to `game_name`.
        '''
        self.name = game_name
        self.save_location, self.last_backup = self.get_game_info(game_name)
        self.filename = self.get_filename(game_name)
        self.backup_loc = os.path.join(self.backup_dest, self.filename)
        self.backup_size = self.convert_size(self.backup_loc)

    def update(self, old_name, new_name, new_save):
        '''
        Updates a game data in the database with `old_name` to `new_name` and `new_save`.
        '''
        self.update_sql("UPDATE games SET game_name = ?, save_location = ? WHERE game_name = ?;",
            (new_name, new_save, old_name))
        self.set(new_name)

    def exists_in_db(self, game_name):
        '''
        Checks if `game_name` is already in the database.
        '''
        entry = self.query("SELECT save_location FROM games WHERE game_name=:game_name",
            {'game_name': game_name})
        return entry != None

    def add(self, game_name, save_location):
        '''
        Adds game to database with `game_name`, `save_location` data.
        '''
        self.update_sql("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
            {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
        self.logger.info(f'Added {game_name} to database.')

    def delete_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        self.update_sql("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.name})
