import getpass, sqlite3, shutil, json, os, re, sys, subprocess, math
from time import sleep, perf_counter
from logging.handlers import RotatingFileHandler
import logging as lg
from logging.handlers import RotatingFileHandler
import datetime as dt
# optional imports
try:
    import requests
    requests_installed = 1
except ModuleNotFoundError:
    requests_installed = 0

class game_class:

    # settings setup
    with open('settings.json') as json_file:
        data = json.load(json_file)
    backup_dest = data['setup']['backup_dest']  # backup destination setup
    # redundancy settings
    redundancy_limit = 4
    backup_redundancy = data['optional_settings']['backup_redundancy']
    if type(backup_redundancy) is not int or backup_redundancy not in range(1, redundancy_limit + 1):
        backup_redundancy = 4
    # optional settings
    enter_to_quick_backup = data['optional_settings']['enter_to_quick_backup']
    disable_resize = data['optional_settings']['disable_resize']
    center_window = data['optional_settings']['center_window']
    # compression
    enable_compression = data['compression']['enable_compression']
    compression_type = data['compression']['compression_type']
    # debug
    output = data['debug']['text_output']
    enable_debug = data['debug']['enable_debug']

    # scoring init
    with open('scoring.json') as json_file:
        scoring = json.load(json_file)

    # sets up search directories
    backup_restore_in_progress = 0
    search_directories = []
    search_directories_incomplete = 1
    username = getpass.getuser()
    initialdir = "C:/"
    best_dir = ''
    drive_letters = []
    applist = None

    # logger setup
    log_formatter = lg.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p')
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG) # Log Level
    my_handler = RotatingFileHandler('Game_Backup.log', maxBytes=5*1024*1024, backupCount=2)
    my_handler.setFormatter(log_formatter)
    logger.addHandler(my_handler)

    # database creation
    database = sqlite3.connect('game_list.db')
    cursor = database.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
        game_name text,
        save_location text,
        last_backup text
        )''')


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


    def get_game_filename(self, name):
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


    def set(self, game_name):
        '''
        Sets the current game to the one entered as an argument
        '''
        self.name = game_name
        self.save_location = self.get_save_loc(game_name)
        self.filename = self.get_game_filename(game_name)
        self.backup_loc = os.path.join(self.backup_dest, self.filename)
        # set last backup
        self.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name",
            {'game_name': game_name})
        self.backup_size = self.convert_size(os.path.join(self.backup_dest, self.name))
        self.last_backup = self.cursor.fetchone()[0]


    def find_drive_letters(self):
        '''
        Finds the active drive letters for storage.
        '''
        with os.popen("fsutil fsinfo drives") as data:
            letter_output = data.readlines()[1]
        words = re.findall('\S+', letter_output)[1:]
        result = []
        for letters in words:
            result.append(letters[0])
        if self.enable_debug:
            print(result)
        return result


    def find_search_directories(self):
        '''
        Finds the directories to use when searching for games.
        '''
        start = perf_counter()
        # os specific settings
        platform = sys.platform
        if platform == 'win32':
            dirs_to_check = [
                rf":/Users/{self.username}/AppData/Local",
                rf":/Users/{self.username}/AppData/LocalLow",
                rf":/Users/{self.username}/AppData/Roaming",
                rf":/Users/{self.username}/Saved Games",
                rf":/Users/{self.username}/Documents",
                r":/Program Files (x86)/Steam/steamapps/common",
                r":/Program Files/Steam/steamapps/common"
                ]
            self.drive_letters = self.find_drive_letters()
        elif platform == 'linux':
            # TODO add linux support to find_search_directories
            dirs_to_check = ['$HOME/.local/share/Steam/userdata']
        # starts directory check
        for dir in dirs_to_check:
            for letter in self.drive_letters:
                current_dir = letter + dir
                if os.path.isdir(current_dir):
                    if 'documents' in current_dir.lower():
                        self.initialdir = current_dir
                    self.search_directories.append(current_dir)
        for custom_saved_dir in self.data['custom_save_directories']:
            self.search_directories.append(custom_saved_dir)
        if self.enable_debug:
            print(self.search_directories)
        finish = perf_counter() # stop time for checking elapsed runtime
        elapsed_time = round(finish-start, 2)
        if self.enable_debug:
            print(f'find_search_directories: {elapsed_time} seconds')
        self.search_directories_incomplete = 0


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


    @staticmethod
    def compressed(file):
        '''
        Returns True if the file is compressed with a valid compression type.
        '''
        available_compression = []
        for item in shutil.get_archive_formats():
            available_compression.append(f'.{item[0]}')
        filetype = os.path.splitext(file)[1]
        if filetype in available_compression:
            return True
        else:
            return False


    def compress(self, file_path, destination):
        '''
        Compresses the file given as the file path into the destination path.
        '''
        shutil.make_archive(base_name=destination, format=self.compression_type, root_dir=file_path)


    def decompress(self,file, destination, format='unknown filetype'):
        '''
        Decompresses the given file into the given destination.
        '''
        try:
            shutil.unpack_archive(file, destination)
        except ValueError:
            pass
            # TODO move to main file
            # msg = f'Decompression failed, {format} is not actually a valid compression type.'
            # messagebox.showwarning(title=self.title, message=msg)


    def update(self):
        '''
        ph
        '''
        new_name = ''
        new_save = ''


    def add(self, new_name):
        '''
        Adds game to database using entry inputs.
        '''
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if len(self.get_selected_game_filename(game_name)) == 0:
            messagebox.showwarning(title=self.title,message=f'Game name has no legal characters for a filename')
            return
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game_name})
        database_save_location = self.cursor.fetchone()
        if database_save_location != None:
            msg = f"Can't add {self.game.name} to database.\nGame already exists."
            messagebox.showwarning(title=self.title, message=msg)
        else:
            if os.path.isdir(save_location):
                self.GameSaveEntry.delete(0, Tk.END)
                self.GameNameEntry.delete(0, Tk.END)
                self.cursor.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
                    {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
                self.database.commit()
                self.sorted_list.insert(0, game_name)
                self.game_listbox.insert(0, game_name)
                self.logger.info(f'Added {game_name} to database.')
                self.update_listbox()
            else:
                msg = f'Save Location for {self.game.name} does not exist.'
                messagebox.showwarning(title=self.title, message=msg)


    def delete(self):
        '''
        ph
        '''
        self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.game.name})
        self.database.commit()


    def delete_saves(self):
        '''
        ph
        '''
        os.path.join(self.game.backup_dest, self.game.name)
        try:
            shutil.rmtree(self.base_backup_folder)
            self.game.logger.info(f'Deleted backups for{self.game.name}.')
            return True
        except PermissionError:
            self.game.logger.warning(f'Failed to delete backups for {self.game.name}')
            return False
            messagebox.showerror(title=self.title, message='Failed to delete directory\nPermission Error')


    def backup_orignal_save(self, selected_backup, full_save_path):
        '''
        Unpacks or copies the backup depending on if it is compressed or not
        '''
        # checks if the backup is compressed
        if self.compressed(selected_backup.name):
            self.decompress(selected_backup.path, self.selected_save_path)
            return f'Restored save for {self.selected_game} from compressed backup.'
        else:
            if os.path.exists(self.selected_save_path):
                print('Path already exists.')
                # FIXME FileExistsError: [WinError 183] Cannot create a file when that file already exists: 'D:\\My Documents\\Shadow of the Tomb Raider\\76561197982626192'
            shutil.copytree(full_save_path, self.selected_save_path)
            return 'Restored save for {self.selected_game}from backup.'


    def delete_oldest(self):
        '''
        Deletes the oldest saves so only the newest specified amount is left.

        Arguments:

        game -- name of folder that will have all but the newest saves deleted
        '''
        saves_list = []
        dir = os.path.join(self.backup_dest, game)
        for file in os.listdir(dir):
            file = os.path.join(dir, file)
            saves_list.append(file)
        if len(saves_list) <= self.backup_redundancy:
            return
        else:
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(self.backup_redundancy, len(saves_list)):
                if os.path.isdir(sorted_list[i]):
                    shutil.rmtree(sorted_list[i])
                else:
                    os.remove(sorted_list[i])


    def backup(self):
        '''
        Runs a single backup for the entered arg.
        Also sets self.backup_restore_in_progress to True so the program wont quick during a backup.
        '''
        print(f'Backing up {self.name} from {self.save_loc}')
        self.backup_restore_in_progress = 1
        current_time = dt.datetime.now().strftime("%m-%d-%y %H-%M-%S")
        dest = os.path.join(self.backup_loc, current_time)
        if self.enable_compression:
            self.compress(self.save_location, dest)
        else:
            shutil.copytree(self.save_location, dest)
        self.delete_oldest(self.filename)
        sleep(.3)
        self.last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.cursor.execute(
            """UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
            {'game_name': self.name, 'last_backup': self.last_backup})
        self.database.commit()
        self.backup_restore_in_progress = 0
        self.completion_sound()


    def restore(self):
        print(f'Restoring {self.name} to {self.save_location}')


    def dir_scoring(self, possible_dir):
        '''
        Uses a scoring system to determines the chance of the given directory to be the save location.
        '''
        # checks if possible_dir is in the blacklist
        dir_blacklist = self.scoring['dir_blacklist']
        for string in dir_blacklist:
            if string.lower() in possible_dir.lower():
                return 0
        # prints possible_dir if enable_debug is 1 and the var is not blank
        if possible_dir != '' and self.game.enable_debug:
            print(f'\n{possible_dir}')
        current_score = 0
        for found_root, found_dirs, found_files in os.walk(possible_dir, topdown=False):
            for found_file in found_files:
            # file scoring TODO add a way to track scoring that applies
                # + scorers
                for item, score in self.scoring['file_positive_scoring'].items():
                    if item in found_file.lower():
                        current_score += score
                # - scorers
                for item, score in self.scoring['file_negative_scoring'].items():
                    if item in found_file.lower():
                        current_score -= score
            for found_dir in found_dirs:
            # folder scoring
                # + scorers
                for item, score in self.scoring['folder_positive_scoring'].items():
                    if item in found_dir.lower():
                        current_score += score
                # - scorers
                for item, score in self.scoring['folder_negative_scoring'].items():
                    if item in found_dir.lower():
                        current_score -= score
        if self.enable_debug:
            print(f'Score {current_score}')
        return current_score


    def get_appid(self, game):
        '''
        Checks the Steam App list for a game and returns its app id if it exists as entered.
        '''
        if self.applist == None:
            applist = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/'
            data = requests.get(applist)
            if data.status_code != requests.codes.ok:
                return None
            self.applist = data.json()['applist']['apps']
        for item in self.applist:
            if item["name"] == game:
                return item['appid']
        return None


    def check_userdata(self, app_id):
        '''
        Checks for a save folder within the steam userdata folder by looking for the given games app_id.
        '''
        existing_paths = []
        if len(self.drive_letters) == 0:
            self.drive_letters = self.find_drive_letters()
        for letter in self.drive_letters:
            path = f'{letter}:/Program Files (x86)/Steam/userdata'
            if os.path.exists(path):
                existing_paths.append(path)
        for path in existing_paths:
            for dirpath, dirnames, filenames in os.walk(path):
                for dir in dirnames:
                    found_path = os.path.join(dirpath, dir)
                    if str(app_id) in found_path:
                        return found_path.replace('/', '\\')


    def game_save_location_search(self, full_game_name, test=0):
        '''
        Searches for possible save game locations for the given name using a point based system.
        The highes scoring directory is chosen.
        '''
        # var setup
        game_name = self.get_selected_game_filename(full_game_name)
        overall_start = perf_counter() # start time for checking elapsed runtime
        best_score = 0
        dir_changed = 0
        current_score = 0
        possible_dir = ''
        search_method = 'name search'
        self.best_dir = self.initialdir
        if self.enable_debug:
            print(f'\nGame: {game_name}')
        # waits for search directories to be ready before the save search is started
        while self.search_directories_incomplete:
            sleep(.1)
        # disables progress bar actions when testing
        if test == 0:
            self.progress['maximum'] = len(self.search_directories) + 1
        for directory in self.search_directories:
            if self.enable_debug:
                print(f'\nCurrent Search Directory: {directory}')
            directory_start = perf_counter()
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir in dirs:
                    if game_name.lower().replace(' ', '') in dir.lower().replace(' ', ''):
                        possible_dir = os.path.join(root, dir)
                        current_score = self.dir_scoring(possible_dir)
            # update based on high score
            directory_finish = perf_counter()
            if self.enable_debug:
                print(f'Dir Search Time: {round(directory_finish-directory_start, 2)} seconds')
            # disables progress bar actions when testing
            if test == 0:
                self.progress['value'] += 1
            if current_score > best_score:
                best_score = current_score
                self.best_dir = os.path.abspath(possible_dir)
                # early break if threshold is met
                if current_score > 600:
                    break
            current_score = 0
        overall_finish = perf_counter() # stop time for checking elapsed runtime
        elapsed_time = round(overall_finish-overall_start, 2)
        if self.enable_debug:
            print(f'\n{game_name}\nOverall Search Time: {elapsed_time} seconds')
            print(f'Path Used: {self.best_dir}')
            print(f'Path Score: {best_score}')
        # checks if nothing was found from the first search
        if self.best_dir == self.initialdir:
            if requests_installed:
                app_id = self.get_appid(full_game_name)
                if app_id != None:
                    self.best_dir = self.check_userdata(app_id)
                    search_method = 'app id search'
                else:
                    self.game.logger.info(f'app_id cant be found for {full_game_name}')
        if test == 0:
            game_save = os.path.abspath(self.GameSaveEntry.get())
            if game_save != self.script_dir:
                if self.best_dir in game_save:
                    print('Found save is correct.')
                else:
                    print('Found save is incorrect.')
                    dir_changed = 1
        else:
            return self.best_dir
        self.progress['value'] = self.progress['maximum']
        # completion time output
        limit = 50
        if len(self.best_dir) > limit:
            info = f'Path Found in {elapsed_time} seconds\n...{self.best_dir[-limit:]}'
        else:
            info = f'Path Found in {elapsed_time} seconds\n{self.best_dir[-limit:]}'
        self.game.logger.info(f'Save for "{full_game_name}" found in {elapsed_time} seconds via {search_method}.')
        self.info_label.config(text=info)
        self.completion_sound()
        # enables the browse button when a save folder seems to be found
        if self.best_dir != self.initialdir:
            if dir_changed:
                # adds info that the found save location is not the same as the save location in the entry box
                info += f'\nFound directory is different then entered directory.'
            self.s_browse.config(state='normal')
        else:
            pass
