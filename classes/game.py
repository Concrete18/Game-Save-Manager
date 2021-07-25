import sqlite3, os, re, math, shutil
from classes.logger import Logger
from contextlib import closing

class Game(Logger):


    def __init__(self, backup_dest, db_loc) -> None:
        '''
        ph
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
            )''')


    def query(self, sql, arg1=None, fetchall=False):
        with closing(sqlite3.connect(self.db_loc)) as con, con, \
                closing(con.cursor()) as cur:
            if arg1 == None:
                cur.execute(sql)
            else:
                cur.execute(sql, arg1)
            if fetchall:
                return cur.fetchall()
            else:
                return cur.fetchone()[0]


    def update_sql(self, sql, arg1=None):
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
            cur.execute("SELECT save_location FROM games")
            missing_save_list = []
            for save_location in cur.fetchall():  # appends all save locations that do not exist to a list
                if not os.path.isdir(save_location[0]):
                    cur.execute('''
                    SELECT game_name
                    FROM games
                    WHERE save_location=:save_location''', {'save_location': save_location[0]})
                    game_name = self.cursor.fetchone()[0]
                    missing_save_list.append(game_name)
            return missing_save_list


    def sorted_games(self):
        '''
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        '''
        data = self.query("SELECT game_name FROM games ORDER BY last_backup DESC", fetchall=True)
        ordered_games = []
        for game_name in data:
            ordered_games.append(game_name[0])
        return ordered_games


    @staticmethod
    def convert_size(dir):
        '''
        Converts size of directory to best fitting unit of measure.

        Arguments:

        dir -- directory that have its total size returned
        '''
        total_size = 0
        for path, dirs, files in os.walk(dir):
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
        ph
        '''
        self.backup_size = self.convert_size(os.path.join(self.backup_dest, self.name))


    def get_filename(self, name):
        '''
        Removes illegal characters and shortens the selected games name so it can become a valid filename.
        '''
        name.replace('&', 'and')
        allowed_filename_characters = '[^a-zA-Z0-9.,\s]'
        char_removal = re.compile(allowed_filename_characters)
        string = char_removal.sub('', name)
        return re.sub("\s\s+" , " ", string).strip()[0:50]


    def get_save_loc(self, game_name):
        '''
        Returns the save location of the selected game from the SQLite Database.
        '''
        return self.query("SELECT save_location FROM games WHERE game_name=:game_name", 
            {'game_name': game_name})


    def get_last_backup(self, game_name):
        '''
        Returns the last time the game was backed up.
        '''
        return self.query("SELECT last_backup FROM games WHERE game_name=:game_name", {'game_name': game_name})
    

    def update_last_backup(self, game_name, last_backup):
        '''
        Updates the last backup time for game_name.
        '''
        self.query("UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name",
            {'game_name': game_name, 'last_backup': last_backup})


    def update(self, old_name, new_name, new_save):
        '''
        Updates a game in the database.
        '''
        self.update_sql("UPDATE games SET game_name = ?, save_location = ? WHERE game_name = ?;",
            (new_name, new_save, old_name))
        self.set(new_name)


    def set(self, game_name):
        '''
        Sets the current game to the one entered as an argument
        '''
        self.name = game_name
        self.save_location = self.get_save_loc(game_name)
        self.filename = self.get_filename(game_name)
        self.backup_loc = os.path.join(self.backup_dest, self.filename)
        self.backup_size = self.convert_size(self.backup_loc)
        self.last_backup = self.get_last_backup(game_name)


    def exists_in_db(self, game_name):
        '''
        Checks if game is already in the database.
        '''
        exists = self.query("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game_name})
        return exists != None


    def add(self, game_name, save_location):
        '''
        Adds game to database.
        '''
        self.update_sql("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
            {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
        self.logger.info(f'Added {game_name} to database.')


    def delete_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        self.update_sql("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.name})
        

    def delete_oldest(self, path, redundancy, ignore):
        '''
        Deletes the oldest saves so only the newest specified amount is left.

        Arguments:

        game -- name of folder that will have all but the newest saves deleted
        '''
        # creates save list
        saves_list = []
        for file in os.scandir(path):
            # ignores pre restore backup
            if ignore not in file.name:
                saves_list.append(file.path)
        # exits if the save list is shorted then the backup_redundancy
        if len(saves_list) <= redundancy:
            return
        else:
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(redundancy, len(saves_list)):
                if os.path.isdir(sorted_list[i]):
                    shutil.rmtree(sorted_list[i])
                else:
                    os.remove(sorted_list[i])
            self.logger.info(f'{self.name} had more then {redundancy} Saves. Deleted oldest saves.')
