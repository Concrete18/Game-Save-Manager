import sqlite3, os, re, math
from logger import logger

class Game(logger):

    # database creation
    database = sqlite3.connect('game_list.db')
    cursor = database.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
        game_name text,
        save_location text,
        last_backup text
        )''')
    # default values
    name = None
    save_location = None

    # TODO switch to class folder structure with init.py

    def __init__(self, backup_dest) -> None:
        self.backup_dest = backup_dest


    def database_check(self):
        '''
        Checks for no longer existing save directories from the database and
        allows showing the missing entries for fixing.
        '''
        self.cursor.execute("SELECT save_location FROM games")
        missing_save_list = []
        for save_location in self.cursor.fetchall():  # appends all save locations that do not exist to a list
            if not os.path.isdir(save_location[0]):
                self.cursor.execute('''
                SELECT game_name
                FROM games
                WHERE save_location=:save_location''', {'save_location': save_location[0]})
                game_name = self.cursor.fetchone()[0]
                missing_save_list.append(game_name)
        return missing_save_list


    def close_database(self):
        '''
        Closes the database.
        '''
        self.database.close()
        print('Database closed')


    def sorted_games(self):
        '''
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        '''
        self.cursor.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in self.cursor.fetchall():
            ordered_games.append(game_name[0])
        self.database.commit()
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
        try:
            self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name",
                {'game_name': game_name})
            return self.cursor.fetchone()[0]
        except TypeError:
            print('Selected Game is ', game_name)
            print(self.cursor.fetchone()[0])


    def get_last_backup(self, game_name):
        '''
        Returns the save location of the selected game from the SQLite Database.
        '''
        self.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name",
            {'game_name': game_name})
        return self.cursor.fetchone()[0]
    

    def update_last_backup(self, game_name, last_backup):
        '''
        ph
        '''
        self.cursor.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
            {'game_name': game_name, 'last_backup': last_backup})
        self.database.commit()


    def update(self, old_name, new_name, new_save):
        '''
        ph
        '''
        sql_update_query  ='''UPDATE games SET game_name = ?, save_location = ? WHERE game_name = ?;'''
        data = (new_name, new_save, old_name)
        self.cursor.execute(sql_update_query , data)
        self.database.commit()
        # TODO make sure this works
        self.set(new_name)


    def set(self, game_name):
        '''
        Sets the current game to the one entered as an argument
        '''
        self.name = game_name
        self.save_location = self.get_save_loc(game_name)
        self.filename = self.get_filename(game_name)
        self.backup_loc = os.path.join(self.backup_dest, self.filename)
        self.backup_size = self.convert_size(os.path.join(self.backup_dest, self.name))
        self.last_backup = self.get_last_backup(game_name)


    def exists_in_db(self, game_name):
        '''
        Checks if game is already in the database.
        '''
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game_name})
        existing_save_loc = self.cursor.fetchone()
        return existing_save_loc != None


    def add(self, game_name, save_location):
        '''
        Adds game to database.
        '''
        self.cursor.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
            {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
        self.database.commit()
        self.logger.info(f'Added {game_name} to database.')


    def delete_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.name})
        self.database.commit()
