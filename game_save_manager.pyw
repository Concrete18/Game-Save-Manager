import getpass, sqlite3, shutil, json, time, os, re, sys, subprocess, math
from threading import Thread
from logging.handlers import RotatingFileHandler
import logging as lg
from tkinter import ttk, filedialog, messagebox
import tkinter as Tk
import datetime as dt

# optional imports
try:
    import winsound
except ModuleNotFoundError:
    pass

class Backup_Class:

    # sets script directory in case current working directory is different
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

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

    # var init
    title = 'Game Save Manager'
    allowed_filename_characters = '[^a-zA-Z0-9.,\s]'
    backup_restore_in_progress = 0
    default_entry_value = 'Type Search Query Here'
    # compression setup
    available_compression = []
    for item in shutil.get_archive_formats():
        available_compression.append(f'.{item[0]}')

    # sets up search directories
    username = getpass.getuser()
    initialdir = "C:/"
    search_directories = []
    search_directories_incomplete = 1
    best_dir = ''

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


    def backup_dest_check(self):
        '''
        Checks if backup destination in settings exists and asks if you want to choose one if it does not.
        '''
        Tk.Tk().withdraw()
        if not os.path.exists(self.backup_dest):
            msg = 'Do you want to choose a save backup directory instead of using a default within the program folder?'
            response = messagebox.askyesno(
                title=self.title,
                message=msg)
            if response:
                self.backup_dest = filedialog.askdirectory(initialdir="C:/", title="Select Save Backup Directory")
                if os.path.exists(self.backup_dest):
                    self.data['settings']['backup_dest'] = self.backup_dest
                    json_object = json.dumps(self.data, indent = 4)  # Serializing json
                    with open('settings.json', "w") as outfile:  # Writing to sample.json
                        outfile.write(json_object)
                else:
                    messagebox.showwarning(
                        title=self.title,
                        message='Path does not exist.')
            else:
                os.mkdir(self.backup_dest)


    def database_check(self):
        '''
        Checks for missing save directories from database.
        '''
        self.cursor.execute("SELECT save_location FROM games")
        missing_save_list = []
        missing_save_string = ''
        for save_location in self.cursor.fetchall():  # appends all save locations that do not exist to a list
            if not os.path.isdir(save_location[0]):
                self.cursor.execute('''
                SELECT game_name
                FROM games
                WHERE save_location=:save_location''', {'save_location': save_location[0]})
                game_name = self.cursor.fetchone()[0]
                missing_save_list.append(game_name)
        total_missing_saves = len(missing_save_list)
        if total_missing_saves == 1:
            missing_save_string = missing_save_list[0]
        elif total_missing_saves == 2:
            missing_save_string = f'{missing_save_list[0]} and {missing_save_list[1]}'
        else:
            missing_save_string = ", ".join(missing_save_list)
        if total_missing_saves in range(1, 6):  # shows unfound save locations if list has 1-5 entries
            messagebox.showwarning(
                title=self.title,
                message=f'Save Locations for the following games do not exist.\n{missing_save_string}')
            self.logger.debug(f'Missing Save Locations:{missing_save_string}')
        elif total_missing_saves > 5: # warns of unfound save locations if list is greater then 5 entries
            messagebox.showwarning(
                title=self.title,
                message='More than 5 save locations do not exist.')
            self.logger.debug(f'More then 5 save locations in the database do not exist.')


    def get_selected_game_filename(self, game=None):
        '''
        Removes illegal characters and shortens the selected games name so it can become a valid filename.
        '''
        if game == None:
            game = self.selected_game
        game.replace('&', 'and')
        char_removal = re.compile(self.allowed_filename_characters)
        string = char_removal.sub('', game)
        return re.sub("\s\s+" , " ", string).strip()[0:50]


    def get_selected_game_save(self):
        '''
        Returns the save location of the selected game from the SQLite Database.
        '''
        try:
            self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name",
                {'game_name': self.selected_game})
            return self.cursor.fetchone()[0]
        except TypeError:
            print('Selected Game is ', self.selected_game)
            print(self.cursor.fetchone()[0])


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


    def delete_oldest(self, game):
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
            self.logger.info(f'{game} had more then {self.backup_redundancy} Saves. Deleted oldest saves.')


    def run_full_backup(self):
        '''
        Backups up the game entered based on SQLite save location data to the specified backup folder.
        '''
        def backup(game_name):
            '''
            Runs a single backup for the entered arg.
            Also sets self.backup_restore_in_progress to True so the program wont quick during a backup.
            '''
            self.backup_restore_in_progress = 1
            current_time = dt.datetime.now().strftime("%m-%d-%y %H-%M-%S")
            dest = os.path.join(self.base_backup_folder, current_time)
            # TODO add progress bar for backup
            if self.enable_compression:
                shutil.make_archive(dest, self.compression_type, self.selected_game_save)
            else:
                shutil.copytree(self.selected_game_save, dest)
            self.delete_oldest(self.game_filename)
            time.sleep(.3)
            total_size = self.convert_size(os.path.join(self.backup_dest, self.selected_game))
            # FIXME total_size is wrong for some games right after it finishes backing up
            info1 = f'{game_name} has been backed up.\n'
            info2 = f'Game Backup Size: {total_size} from {len(os.listdir(self.base_backup_folder))} backups'
            if self.enable_debug:
                print(info2)
            self.ActionInfo.config(text=info1 + info2)
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(0, game_name)
            self.logger.info(f'Backed up Save for {game_name}.')
            self.backup_restore_in_progress = 0
            self.completion_sound()

        if self.selected_game == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        game_name = self.selected_game
        self.ActionInfo.config(text=f'Backing up {game_name}\nDo not close program.')
        try:
            Thread(target=backup, args=(game_name, )).start()
            last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            self.cursor.execute(
                """UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
                {'game_name': game_name, 'last_backup': last_backup})
            self.database.commit()
        except FileNotFoundError:
            messagebox.showwarning(
                title=self.title,
                message='Action Failed - File location does not exist.')
            self.logger.error(f'Failed to Backed up Save for {game_name}. File location does not exist.')
        except FileExistsError:
            messagebox.showwarning(
                title=self.title,
                message='Action Failed - Save Already Backed up.')
            self.logger.error(f'Failed to Backed up Save for {game_name}. Save Already Backed up.')
        except SystemExit:
            print('Cancelled Backup.')


    def tk_window_options(self, window_name, window_width, window_height, define_size=0):
        '''
        Disables window resize and centers window if config enables each.
        '''
        window_name.title(self.title)
        if sys.platform == 'win32':
            window_name.iconbitmap(window_name, 'images\Save_icon.ico')
        if self.disable_resize:  # sets window to not resize if disable_resize is set to 1
            window_name.resizable(width=False, height=False)
        if self.center_window == 1:
            width_pos = int((window_name.winfo_screenwidth()-window_width)/2)
            height_pos = int((window_name.winfo_screenheight()-window_height)/2)
            if define_size:
                window_name.geometry(f'{window_width}x{window_height}+{width_pos}+{height_pos}')
            else:
                window_name.geometry(f'+{width_pos}+{height_pos}')


    def backup_shortcut(self, event):
        '''
        Shortcut that activates when pressing enter while a game is selected.
        '''
        response = messagebox.askquestion(
            title=self.title,
            message=f'Are you sure you want to backup {self.selected_game}')
        if response == 'yes':
            self.run_full_backup()
        else:
            self.game_listbox.activate(0)
            return
        print(event)


    def restore_save(self):
        '''
        Opens an interface for picking the dated backup of the selected game to restore.

        First it checks if an existing save exists or if a game is even selected(Exits function if no game is selected).
        '''
        # TODO add progress bar for restore
        self.backup_restore_in_progress = 1
        if self.selected_game == None:
            messagebox.showwarning(
                title=self.title,
                message='No game is selected yet.')
            self.backup_restore_in_progress = 0
            return
        backup_path = self.base_backup_folder
        self.save_dic = {}
        if os.path.exists(backup_path):
            for file in os.scandir(backup_path):
                file_name = os.path.splitext(file.name)[0]
                try:
                    updated_name = dt.datetime.strptime(file_name, '%m-%d-%y %H-%M-%S').strftime('%b %d, %Y %I:%M %p')
                except ValueError:
                    updated_name = file_name
                self.save_dic[updated_name] = file
            for file in os.scandir(os.path.split(self.selected_game_save)[0]):
                if file_name.endswith('.old'):
                    self.save_dic['Undo Last Restore'] = file
        else:
            messagebox.showwarning(
                title=self.title,
                message=f'No backed up saves exist for {self.selected_game}.')
            self.backup_restore_in_progress = 0
            return


        def cancel_restore():
            self.backup_restore_in_progress = 0
            self.Restore_Game_Window.destroy()


        def restore_selected_save():
            '''
            Restores selected game save based on save clicked.

            Restores by renaming current save folder to "save.old" and then copying the backup to replace it.
            '''
            save_name = self.save_dic[save_listbox.get(save_listbox.curselection())]
            print(save_name)
            backup_path = os.path.join(self.backup_dest, self.selected_game, save_name.name)
            if save_name.name.endswith('.old'):
                msg1 = 'This will delete the previously restored save and revert to the original.'
                msg2 = 'Are you sure? This will skip the recycle bin.'
                response = messagebox.askyesno(
                    title=self.title,
                    message=msg1 + msg2)
                if response:
                    shutil.rmtree(save_name.path[:-4])
                    os.rename(save_name.path, save_name.path[:-4])
                    self.Restore_Game_Window.grab_release()
                    self.Restore_Game_Window.destroy()
                    self.logger.info(f'Restored original save for {self.selected_game}.')
                return
            if os.path.exists(f'{self.selected_game_save}.old'):
                msg1 = 'Backup of current save before last restore already exists.'
                msg2 = 'Do you want to delete it? This will cancel the restore if you do not delete it.'
                response = messagebox.askyesno(
                    title=self.title,
                    message=msg1 + msg2)
                if response:
                    shutil.rmtree(f'{self.selected_game_save}.old')
                    self.logger.info(f'Deleted original save before last restore for {self.selected_game}.')
                else:
                    print('Canceling Restore.')
                    self.Restore_Game_Window.grab_release()
                    return
            # TODO Move old file to special backup folder instead of renaming to .old
            os.rename(self.selected_game_save, f'{self.selected_game_save}.old')
            # shutil.move(self.selected_game_save, os.path.join(self.selected_game_save))
            # TODO test with different types of compression
            if save_name.name in self.available_compression:
                # decompresses the backup and sends it to the save location
                try:
                    shutil.unpack_archive(backup_path, self.selected_game_save)
                    self.logger.info(f'Restored save for {self.selected_game} from compressed backup.')
                except ValueError:
                    filetype = os.path.splitext(save_name.name)[1]
                    msg = f'Decompression failed, {filetype} is not actually a valid compression type.'
                    response = messagebox.showwarning(title=self.title, message=msg)
            else:
                shutil.copytree(backup_path, self.selected_game_save)
                self.logger.info(f'Restored save for {self.selected_game}from backup.')
            cancel_restore()


        self.Restore_Game_Window = Tk.Toplevel(takefocus=True)
        self.Restore_Game_Window.protocol("WM_DELETE_WINDOW", cancel_restore)
        window_width = 300
        window_height = 220
        self.tk_window_options(self.Restore_Game_Window, window_width, window_height)
        self.Restore_Game_Window.grab_set()

        RestoreInfo = ttk.Label(self.Restore_Game_Window,
            text='Select save to restore for', font=("Arial Bold", 10))
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=(10,0), padx=10)

        RestoreGame = ttk.Label(self.Restore_Game_Window,
            text=self.selected_game, font=("Arial Bold", 10))
        RestoreGame.grid(columnspan=2, row=1, column=0, pady=(0,10), padx=10)

        save_listbox = Tk.Listbox(self.Restore_Game_Window, exportselection=False, font=("Arial Bold", 12), height=5,
            width=30)
        save_listbox.grid(columnspan=2, row=2, column=0, pady=5, padx=10)

        for item in self.save_dic:
            save_listbox.insert(Tk.END, item)

        confirm_button = ttk.Button(self.Restore_Game_Window, text='Confirm', command=restore_selected_save, width=20)
        confirm_button.grid(row=3, column=0, padx=10, pady=10)

        CancelButton = ttk.Button(self.Restore_Game_Window, text='Cancel', command=cancel_restore, width=20)
        CancelButton.grid(row=3, column=1, padx=10, pady=10)

        self.Restore_Game_Window.mainloop()


    def explore_folder(self, folder):
        '''
        Opens the selected games save location in explorer or backup folder.

        Arguments:

        folder -- Set to "Game Save" or "Backup" to determine folder that is opened in explorer
        '''
        if self.selected_game == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
        elif folder == 'Game Save':  # open game save location in explorer
            if not os.path.isdir(self.selected_game_save):
                msg = f'Save location for {self.selected_game} no longer exists'
                messagebox.showwarning(title=self.title, message=msg)
            subprocess.Popen(f'explorer "{self.selected_game_save}"')
        elif folder == 'Backup':  # open game backup location in explorer
            if not os.path.isdir(self.base_backup_folder):
                messagebox.showwarning(title=self.title, message=f'{self.selected_game} has not been backed up yet.')
            subprocess.Popen(f'explorer "{self.base_backup_folder}"')


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


    def add_game_to_database(self):
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
            msg = f"Can't add {self.selected_game} to database.\nGame already exists."
            messagebox.showwarning(title=self.title, message=msg)
        else:
            if os.path.isdir(save_location):
                self.GameSaveEntry.delete(0, Tk.END)
                self.GameNameEntry.delete(0, Tk.END)
                self.cursor.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
                    {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
                self.database.commit()
                self.game_listbox.insert(0, game_name)
                self.logger.info(f'Added {game_name} to database.')
            else:
                msg = f'Save Location for {self.selected_game} does not exist.'
                messagebox.showwarning(title=self.title, message=msg)


    def find_letters(self):
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
        start = time.perf_counter()
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
            drive_letters = self.find_letters()
        elif platform == 'linux':
            # TODO add linux support to find_search_directories
            dirs_to_check = ['$HOME/.local/share/Steam/userdata']
        # starts directory check
        for dir in dirs_to_check:
            for letter in drive_letters:
                current_dir = letter + dir
                if os.path.isdir(current_dir):
                    if 'documents' in current_dir.lower():
                        self.initialdir = current_dir
                    self.search_directories.append(current_dir)
        for custom_saved_dir in self.data['custom_save_directories']:
            self.search_directories.append(custom_saved_dir)
        if self.enable_debug:
            print(self.search_directories)
        finish = time.perf_counter() # stop time for checking elaspsed runtime
        elapsed_time = round(finish-start, 2)
        if self.enable_debug:
            print(f'find_search_directories: {elapsed_time} seconds')
        self.search_directories_incomplete = 0


    def open_smart_browse_window(self):
        '''
        Smart Browse Progress window
        TODO create index of each directory and use changes in directory to see if a new index should be done.
        '''
        # closes window if it is already open so a new one can be created
        try:
            self.smart_browse_win.destroy()
        except AttributeError:
            pass
        # opens window
        self.smart_browse_win = Tk.Toplevel(self.main_gui)
        self.smart_browse_win.attributes('-topmost', 'true')
        self.tk_window_options(self.smart_browse_win, 340, 130, define_size=0)

        text = f'Looking for the game save directory for\n{self.GameNameEntry.get()}'
        self.info_label = Tk.Label(self.smart_browse_win, text=text, font=("Arial Bold", 10))
        self.info_label.grid(row=0, column=0, pady=(9))

        self.progress = ttk.Progressbar(self.smart_browse_win, orient=Tk.HORIZONTAL, length=360, mode='determinate')
        self.progress.grid(row=1, column=0, pady=(5,10), padx=20)

        self.s_browse = ttk.Button(self.smart_browse_win, text='Browse', command=lambda: self.browse(self.best_dir),
            width=23)
        self.s_browse.grid(row=2, column=0, pady=(5,10))
        self.s_browse.config(state='disabled')
        self.smart_browse_win.focus_force()


    @staticmethod
    def nonascii(string):
        '''
        Returns the given string with ASCII characters removed.
        '''
        return string.encode("ascii", "ignore").decode()


    @staticmethod
    def completion_sound():
        '''
        Makes a sound denoting a task completion.
        '''
        if sys.platform == 'win32':
            try:
                winsound.PlaySound("Exclamation", winsound.SND_ALIAS)
            except ModuleNotFoundError:
                pass


    def game_save_location_search(self, game_name, test=0):
        '''
        Searches for possible save game locations for the given name using a point based system.
        The highes scoring directory is chosen.
        '''
        overall_start = time.perf_counter() # start time for checking elaspsed runtime
        best_score = 0
        break_used = 0
        dir_changed = 0
        if self.enable_debug:
            print(f'\nGame: {game_name}')
        current_score = 0
        self.best_dir = self.initialdir
        possible_dir = ''
        while self.search_directories_incomplete:
            time.sleep(.1)
        if test == 0:
            self.progress['maximum'] = len(self.search_directories) + 1
        for directory in self.search_directories:
            if self.enable_debug:
                print(f'\nCurrent Search Directory: {directory}')
            directory_start = time.perf_counter()
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir in dirs:
                    if game_name.lower().replace(' ', '') in dir.lower().replace(' ', ''):
                        possible_dir = os.path.join(root, dir)
                        if possible_dir != '':
                            if self.enable_debug:
                                print(f'\n{possible_dir}')
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
                        break
            # update based on high score
            directory_finish = time.perf_counter()
            if self.enable_debug:
                print(f'Dir Search Time: {round(directory_finish-directory_start, 2)} seconds')
            if test == 0:
                self.progress['value'] += 1
            if current_score > best_score:
                best_score = current_score
                self.best_dir = os.path.abspath(possible_dir)
                # early break if threshold is met TODO verify for premature breaks
                if current_score > 600:
                    break_used = 1
                    break
            current_score = 0
        overall_finish = time.perf_counter() # stop time for checking elaspsed runtime
        elapsed_time = round(overall_finish-overall_start, 2)
        if self.enable_debug:
            print(f'\n{game_name}\nOverall Search Time: {elapsed_time} seconds')
            print(f'Path Used: {self.best_dir}')
            print(f'Path Score: {best_score}')
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
        if break_used:
            print('Early Break Used')
        self.progress['value'] = self.progress['maximum']
        limit = 50
        if self.best_dir == self.initialdir:
            info = 'Nothing Found.\nIf the game name has colons in it.\nTry searching only for the text on the left of the colons.'
            print('Nothing Found')
        elif len(self.best_dir) > limit:
            info = f'Path Found in {elapsed_time} seconds\n...{self.best_dir[-limit:]}'
        else:
            info = f'Path Found in {elapsed_time} seconds\n{self.best_dir[-limit:]}'
        self.info_label.config(text=info)
        self.completion_sound()
        if self.best_dir != self.initialdir:
            if dir_changed:
                info += f'\nFound directory is different then entered directory.'
            self.s_browse.config(state='normal')


    def smart_browse(self):
        '''
        Searches for a starting point for the save location browser.
        '''
        # removes illegal file characters
        game_name = self.get_selected_game_filename(self.GameNameEntry.get())
        print(game_name)
        # checks if no game name is in entry box.
        if len(game_name) == 0:
            messagebox.showwarning(
                title=self.title,
                message='Smart Browse requires a game name to be entered.')
            return
        self.open_smart_browse_window()
        # looks for folders with the games name
        Thread(target=self.game_save_location_search, args=(game_name,), daemon=True).start()


    def browse(self, initial_dir=None):
        '''
        Opens a file dialog so a save directory can be chosen.
        It starts in the My Games folder in My Documents if it exists within a limited drive letter search.
        '''
        if initial_dir == None:
            starting_point = self.initialdir
            current_save_location = self.GameSaveEntry.get()
            if os.path.exists(current_save_location):
                starting_point = current_save_location
        else:
            starting_point = initial_dir
            self.smart_browse_win.destroy()
        save_dir = filedialog.askdirectory(initialdir=starting_point, title="Select Save Directory")
        self.GameSaveEntry.delete(0, Tk.END)
        self.GameSaveEntry.insert(0, save_dir)


    def delete_game_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        if self.selected_game == None:
            messagebox.showwarning(
                title=self.title,
                message='No game is selected yet.')
            return
        delete_check = messagebox.askyesno(
            title=self.title,
            message=f'Are you sure that you want to delete {self.selected_game}?')
        if delete_check:
            self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.selected_game})
            self.database.commit()
            self.game_listbox.delete(self.game_listbox.curselection()[0])
            self.select_listbox_entry()
            if os.path.isdir(self.base_backup_folder):
                response = messagebox.askyesno(
                    title=self.title,
                    message='Do you want to delete the backed up saves as well?')
                if response:
                    os.path.join(self.backup_dest, self.selected_game)
                    try:
                        shutil.rmtree(self.base_backup_folder)
                        self.logger.info(f'Deleted backups for{self.selected_game}.')
                    except PermissionError:
                        self.logger.warning(f'Failed to delete backups for {self.selected_game}')
                        messagebox.showerror(
                            title=self.title,
                            message='Failed to delete directory\nPermission Error')
                self.logger.info(f'Deleted {self.selected_game} from database.')


    def update_game(self):
        '''
        Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.
        '''
        if self.selected_game == None:
            messagebox.showwarning(
                title=self.title,
                message='No game is selected yet.')
            return
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if os.path.isdir(save_location):
            sql_update_query  ='''UPDATE games
                    SET game_name = ?, save_location = ?
                    WHERE game_name = ?;'''
            data = (game_name, save_location, self.selected_game)
            self.cursor.execute(sql_update_query , data)
            self.database.commit()
            new_name = os.path.join(self.backup_dest, self.get_selected_game_filename(game_name))
            os.rename(self.base_backup_folder, new_name)
            index = self.game_listbox.curselection()
            print(index)
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(index, game_name)
            self.logger.info(f'Updated {self.selected_game} in database.')
        else:
            messagebox.showwarning(
                title=self.title,
                message='Save Location does not exist.')


    @staticmethod
    def readable_time_since(datetime_obj):
        '''
        Gives time since for a datetime object in the unit of time that makes the most sense
        rounded to 1 decimal place.

        Arguments:

        datetime_obj -- datetime object that will have the current date subtracted from it
        '''
        seconds = (dt.datetime.now() - datetime_obj).total_seconds()
        if seconds < (60 * 60):  # seconds in minute * minutes in hour
            minutes = round(seconds / 60, 1)  # seconds in a minute
            return f' {minutes} minutes ago'
        elif seconds < (60 * 60 * 24):  # seconds in minute * minutes in hour * hours in a day
            hours = round(seconds / (60 * 60), 1)  # seconds in minute * minutes in hour
            return f' {hours} hours ago'
        else:
            days = round(seconds / 86400, 1)  # seconds in minute * minutes in hour * hours in a day
            return f' {days} days ago'


    def update_listbox(self, data):
        '''
        Deletes current listbox items and adds the given data in.
        '''
        self.game_listbox.delete(0, Tk.END)
        for item in data:
            self.game_listbox.insert(Tk.END, item)


    def entry_search(self, e):
        '''
        Finds all items in the sorted_list that have the search box data in it.
        It then updates the listbox data to only include matching results.
        '''
        typed = self.search_entry.get()
        if typed == '':
            data = self.sorted_list
        else:
            data = []
            for item in self.sorted_list:
                if typed.lower() in item.lower():
                    data.append(item)
        self.update_listbox(data)


    def select_entry(self, e):
        '''
        Deletes only search box default text on click.
        '''
        if self.search_entry.get() == self.default_entry_value:
            self.search_entry.delete(0, Tk.END)


    def listbox_nav(self, e):
        '''
        TODO Allows Up and Down arrow keys to navigate the listbox.
        '''
        index = self.game_listbox.curselection()[0]
        if e.keysym == 'Up':
            index += -1
        if e.keysym == 'Down':
            index += 1
        if 0 <= index < self.game_listbox.size():
            self.game_listbox.selection_clear(0, Tk.END)
            self.game_listbox.select_set(index)
            self.game_listbox.selection_anchor(index)
            self.game_listbox.activate(index)


    def unfocus_entry(self, e):
        '''
        Resets search box to default_entry_value when it loses focus.
        '''
        self.search_entry.delete(0, Tk.END)
        self.search_entry.insert(0, self.default_entry_value)


    def select_listbox_entry(self, Update = 0):
        '''
        Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.

        Arguments:

        Update -- 1 or 0 (default = 0)
        '''
        # clears entry boxes
        self.GameNameEntry.delete(0, Tk.END)
        self.GameSaveEntry.delete(0, Tk.END)
        if self.backup_restore_in_progress:
            return
        # updates entry boxes to show currently selected game in listbox
        if Update == 1:
            # script wide variables for selected game
            self.selected_game = self.game_listbox.get(self.game_listbox.curselection())
            self.game_filename = self.get_selected_game_filename()
            self.selected_game_save = self.get_selected_game_save()
            self.base_backup_folder = os.path.join(self.backup_dest, self.game_filename)
            # game name and entry box update
            self.GameNameEntry.insert(0, self.selected_game)
            self.GameSaveEntry.insert(0, self.selected_game_save)
            # search box update
            self.search_entry.delete(0, Tk.END)
            self.search_entry.insert(0, self.default_entry_value)
            # enables all buttons to be pressed once a selection is made
            for button in [self.BackupButton, self.ExploreSaveButton]:
                button.config(state='normal')
            if os.path.isdir(self.base_backup_folder):
                set_state = 'normal'
            else:
                set_state = 'disabled'
            for button in [self.ExploreBackupButton, self.RestoreButton]:
                button.config(state=set_state)
            total_size = self.convert_size(self.base_backup_folder)
            self.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name",
                {'game_name': self.selected_game})
            last_backup = self.cursor.fetchone()[0]
            if last_backup != 'Never':
                time_since = self.readable_time_since(dt.datetime.strptime(last_backup, '%Y/%m/%d %H:%M:%S'))
                info1 = f'{self.selected_game} was last backed up {time_since}\n'
                info2 = f'Game Backup Size: {total_size} from {len(os.listdir(self.base_backup_folder))} backups'
                info = info1 + info2
            else:
                info = f'{self.selected_game} has not been backed up\n'
            self.ActionInfo.config(text=info)
            self.BackupButton.focus_set()


    def close_db(self):
        '''
        Closes the database and quits the program when closing the interface.
        '''
        if self.backup_restore_in_progress:
            msg = f'Backup/Restore in progress.\n{self.title} will close after completion when you close this message.'
            messagebox.showerror(title=self.title, message=msg)
        while self.backup_restore_in_progress:
            time.sleep(.1)
        self.database.close
        # FIXME fails to exit if filedialog is left open
        # fix using subclassed filedialog commands that can close it
        exit()


    def open_interface_window(self):
        self.sorted_list = self.sorted_games()

        # Defaults
        BoldBaseFont = "Arial Bold"

        self.main_gui = Tk.Tk()
        self.main_gui.protocol("WM_DELETE_WINDOW", self.close_db)
        window_width = 680
        window_height = 550
        self.tk_window_options(self.main_gui, window_width, window_height)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # binding
        if self.enter_to_quick_backup:
            self.main_gui.bind('<Return>', self.backup_shortcut)

        # Main Row 0
        Backup_Frame = Tk.Frame(self.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        info_text = f'Total Games: {len(self.sorted_list)}\nTotal Backup Size: {self.convert_size(self.backup_dest)}'
        Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
        Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        self.BackupButton = ttk.Button(Backup_Frame, text='Backup Save', state='disabled',
            command=self.run_full_backup, width=button_width)
        self.BackupButton.grid(row=3, column=1, padx=5, pady=5)

        self.RestoreButton = ttk.Button(Backup_Frame, text='Restore Save', state='disabled',
            command=self.restore_save, width=button_width)
        self.RestoreButton.grid(row=3, column=2, padx=5)

        self.ExploreSaveButton = ttk.Button(Backup_Frame, text='Explore Save Location', state='disabled',
            command=lambda: self.explore_folder('Game Save'), width=button_width)
        self.ExploreSaveButton.grid(row=4, column=1, padx=5)

        self.ExploreBackupButton = ttk.Button(Backup_Frame, text='Explore Backup Location', state='disabled',
            command=lambda: self.explore_folder('Backup'), width=button_width)
        self.ExploreBackupButton.grid(row=4, column=2, padx=5)

        # Main Row 1
        instruction = 'Select a Game\nto continue'
        self.ActionInfo = Tk.Label(self.main_gui, text=instruction, font=(BoldBaseFont, 10))
        self.ActionInfo.grid(columnspan=4, row=1, column=0, padx=5, pady= 5)

        # Main Row 2
        self.ListboxFrame = Tk.Frame(self.main_gui)
        self.ListboxFrame.grid(columnspan=4, row=2, column=0,  padx=(20, 20), pady=(5, 10))

        self.scrollbar = Tk.Scrollbar(self.ListboxFrame, orient=Tk.VERTICAL)
        self.scrollbar.grid(row=1, column=3, sticky='ns', rowspan=3)

        self.search_entry = Tk.ttk.Entry(self.ListboxFrame, width=89, exportselection=0)
        self.search_entry.grid(columnspan=3, row=0, column=0, pady=(0, 3))
        self.search_entry.insert(0, self.default_entry_value)
        self.search_entry.bind('<1>', self.select_entry)
        self.search_entry.bind('<FocusOut>', self.unfocus_entry)
        self.search_entry.bind('<KeyRelease>', self.entry_search)

        self.game_listbox = Tk.Listbox(self.ListboxFrame, exportselection=False, yscrollcommand=self.scrollbar.set,
            font=(BoldBaseFont, 12), height=10, width=60)
        self.game_listbox.grid(columnspan=3, row=1, column=0)
        self.game_listbox.bind('<<ListboxSelect>>', lambda event, game_listbox=self.game_listbox,:self.select_listbox_entry(1))

        # TODO finish or delete below code
        # full interface bind for lisxtbox navigation
        # self.main_gui.bind('<Up>', lambda event,arg=.1:self.listbox_nav(event))
        # self.main_gui.bind('<Down>', lambda event,arg=.1:self.listbox_nav(event))

        # scrollbar config
        self.scrollbar.config(command=self.game_listbox.yview)
        # listbox fill
        self.update_listbox(self.sorted_list)

        # Main Row 3
        Add_Game_Frame = Tk.LabelFrame(self.main_gui, text='Manage Games')
        Add_Game_Frame.grid(columnspan=4, row=3, padx=15, pady=(5, 17))

        EnterGameLabel = Tk.ttk.Label(Add_Game_Frame, text='Enter Game Name')
        EnterGameLabel.grid(row=0, column=0)

        entry_width = 65
        self.GameNameEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
        self.GameNameEntry.grid(row=0, column=1, columnspan=3, pady=8, padx=5)

        EnterSaveLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Save Location')
        EnterSaveLabeL.grid(row=1, column=0)

        self.GameSaveEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
        self.GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5, padx=10)

        browse_button_width = 13
        SmartBrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Smart Browse', width=browse_button_width,
            command=self.smart_browse)
        SmartBrowseButton.grid(row=0, column=4, padx=10)

        BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse', width=browse_button_width,
            command=self.browse)
        BrowseButton.grid(row=1, column=4, padx=10)

        # Button Frame Row 2
        Button_Frame = Tk.Frame(Add_Game_Frame)
        Button_Frame.grid(columnspan=5, row=2, pady=(5, 5))

        button_padx = 4
        button_pady = 5
        ConfirmAddButton = Tk.ttk.Button(Button_Frame, text='Add Game',
            command=self.add_game_to_database, width=20)
        ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

        UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Game',
            command=self.update_game, width=20)
        UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

        RemoveButton = ttk.Button(Button_Frame, text='Remove Game',
            command=self.delete_game_from_db, width=20)
        RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
            command=self.select_listbox_entry, width=20)
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        self.database_check()
        self.main_gui.mainloop()


    def run(self):
        '''
        Runs everything needed to make the program work.
        '''
        if self.output:
            sys.stdout = open("output.txt", "w")
        self.backup_dest_check()
        Thread(target=self.find_search_directories).start()
        self.open_interface_window()
        if self.output:
            sys.stdout.close()


if __name__ == '__main__':
    Backup_Class().run()
