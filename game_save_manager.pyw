from logging.handlers import RotatingFileHandler
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import datetime as dt
import tkinter as Tk
import logging as lg
import subprocess
import winsound
import getpass
import sqlite3
import shutil
import json
import time
import math
import sys
import os
import re

# TODO test older version to see if init needs to be sped up

class Interface:
    pass
    # TODO switch to gui class and functions class


class Backup:

    # sets script directory in case current working directory is different
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # settings setup
    with open('settings.json') as json_file:
        data = json.load(json_file)
    # backup destination setup
    backup_dest = data['settings']['backup_dest']

    backup_redundancy = data['settings']['backup_redundancy']
    if type(backup_redundancy) is not int or backup_redundancy > 4:
        backup_redundancy = 4
    disable_resize = data['settings']['disable_resize']
    center_window = data['settings']['center_window']
    output = data['settings']['text_output']
    debug = data['settings']['debug']

    # var init
    title = 'Game Save Manager'
    allowed_filename_characters = '[^a-zA-Z0-9.,\s]'

    # sets up search directories
    username = getpass.getuser()
    initialdir = "C:/"
    search_directories = []
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


    @classmethod
    def backup_dest_check(cls):
        '''
        Checks if backup destination in settings exists and asks if you want to choose one if it does not.
        '''
        # FIXME first run so blank windows does not show up
        Tk.Tk().withdraw()
        if not os.path.exists(cls.backup_dest):
            msg = 'Do you want to choose a save backup directory instead of using a default within the program folder?'
            response = messagebox.askyesno(
                title=cls.title,
                message=msg)
            if response:
                cls.backup_dest = filedialog.askdirectory(initialdir="C:/", title="Select Save Backup Directory")
                if os.path.exists(cls.backup_dest):
                    cls.data['settings']['backup_dest'] = cls.backup_dest
                    json_object = json.dumps(cls.data, indent = 4)  # Serializing json
                    with open('settings.json', "w") as outfile:  # Writing to sample.json
                        outfile.write(json_object)
                else:
                    messagebox.showwarning(
                        title=cls.title,
                        message='Path does not exist.')
            else:
                os.mkdir(cls.backup_dest)


    @classmethod
    def database_check(cls):
        '''
        Checks for missing save directories from database.
        '''
        cls.cursor.execute("SELECT save_location FROM games")
        missing_save_list = []
        missing_save_string = ''
        for save_location in cls.cursor.fetchall():  # appends all save locations that do not exist to a list
            if not os.path.isdir(save_location[0]):
                cls.cursor.execute('''
                SELECT game_name
                FROM games
                WHERE save_location=:save_location''', {'save_location': save_location[0]})
                game_name = cls.cursor.fetchone()[0]
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
                title=cls.title,
                message=f'Save Locations for the following games do not exist.\n{missing_save_string}')
            cls.logger.debug(f'Missing Save Locations:{missing_save_string}')
        elif total_missing_saves > 5: # warns of unfound save locations if list is greater then 5 entries
            messagebox.showwarning(
                title=cls.title,
                message='More than 5 save locations do not exist.')
            cls.logger.debug(f'More then 5 save locations in the database do not exist.')


    @classmethod
    def get_selected_game_filename(cls, game=None):
        '''
        Removes illegal characters and shortens the selected games name so it can become a valid filename.
        '''
        if game == None:
            game = cls.selected_game
        game.replace('&', 'and')
        char_removal = re.compile(cls.allowed_filename_characters)  # TODO add comma to whitelist
        string = char_removal.sub('', game)
        return re.sub("\s\s+" , " ", string).strip()[0:50]


    @classmethod
    def get_selected_game_save(cls):
        '''
        Returns the save location of the selected game from the SQLite Database.
        '''
        try:
            cls.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name",
                {'game_name': cls.selected_game})
            return cls.cursor.fetchone()[0]
        except TypeError:
            print('Selected Game is ', cls.selected_game)
            print(cls.cursor.fetchone()[0])


    @classmethod
    def sorted_games(cls):
        '''
        Sorts the game list from the SQLite database based on the last backup and then returns a list.
        '''
        cls.cursor.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in cls.cursor.fetchall():
            ordered_games.append(game_name[0])
        cls.database.commit()
        return ordered_games


    @classmethod
    def delete_oldest(cls, game):
        '''
        Deletes the oldest saves so only the newest specified amount is left.

        Arguments:

        game -- name of folder that will have all but the newest saves deleted
        '''
        saves_list = []
        dir = os.path.join(cls.backup_dest, game)
        for file in os.listdir(dir):
            file = os.path.join(dir, file)
            saves_list.append(file)
        if len(saves_list) <= cls.backup_redundancy:
            return
        else:
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(cls.backup_redundancy, len(saves_list)):
                shutil.rmtree(sorted_list[i])
            cls.logger.info(f'{game} had more then {cls.backup_redundancy} Saves. Deleted oldest saves.')


    @classmethod
    def backup_save(cls):
        '''
        Backups up the game entered based on SQLite save location data to the specified backup folder.
        '''
        if cls.selected_game == None:
            messagebox.showwarning(
                title=cls.title,
                message='No game is selected yet.')
            return
        current_time = dt.datetime.now().strftime("%m-%d-%y %H-%M-%S")
        game_name = cls.selected_game
        total_size = cls.convert_size(os.path.join(cls.backup_dest, cls.selected_game))
        dest = os.path.join(cls.base_backup_folder, current_time)
        last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        cls.ActionInfo.config(text=f'Backing up {game_name}\n')
        try:
            def backup():
                shutil.copytree(cls.selected_game_save, dest)
                cls.delete_oldest(cls.game_filename)
                info1 = f'{game_name} has been backed up.\n'
                info2 = f'Game Backup Size: {total_size} from {len(os.listdir(cls.base_backup_folder))} backups'
                cls.ActionInfo.config(text=info1 + info2)
                cls.game_listbox.delete(Tk.ACTIVE)
                cls.game_listbox.insert(0, game_name)
                cls.logger.info(f'Backed up Save for {game_name}.')
            BackupThread = Thread(target=backup)
            BackupThread.start()
            cls.cursor.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
            {'game_name': game_name, 'last_backup': last_backup})
            cls.database.commit()
        except FileNotFoundError:
            messagebox.showwarning(
                title=cls.title,
                message='Action Failed - File location does not exist.')
            cls.logger.error(f'Failed to Backed up Save for {game_name}. File location does not exist.')
        except FileExistsError:
            messagebox.showwarning(
                title=cls.title,
                message='Action Failed - Save Already Backed up.')
            cls.logger.error(f'Failed to Backed up Save for {game_name}. Save Already Backed up.')


    @classmethod
    def tk_window_options(cls, window_name, window_width, window_height, define_size=0):
        '''
        Disables window resize and centers window if config enables each.
        '''
        window_name.title(cls.title)
        window_name.iconbitmap(window_name, 'images\Save_icon.ico')
        if cls.disable_resize:  # sets window to not resize if disable_resize is set to 1
            window_name.resizable(width=False, height=False)
        if cls.center_window == 1:
            width_pos = int((window_name.winfo_screenwidth()-window_width)/2)
            height_pos = int((window_name.winfo_screenheight()-window_height)/2)
            if define_size:
                window_name.geometry(f'{window_width}x{window_height}+{width_pos}+{height_pos}')
            else:
                window_name.geometry(f'+{width_pos}+{height_pos}')


    @classmethod
    def backup_shortcut(cls, event):
        '''
        Shortcut that activates when pressing enter while a game is selected.
        '''
        response = messagebox.askquestion(
            title=cls.title,
            message=f'Are you sure you want to backup {cls.selected_game}')
        if response == 'yes':
            cls.backup_save()
        else:
            cls.game_listbox.activate(0)
            return
        print(event)


    @classmethod
    def restore_save(cls):
        '''
        Opens an interface for picking the dated backup of the selected game to restore.
        '''
        if cls.selected_game == None:
            messagebox.showwarning(
                title=cls.title,
                message='No game is selected yet.')
            return
        backup_path = cls.base_backup_folder
        cls.save_dic = {}
        if os.path.exists(backup_path):
            for file in os.scandir(backup_path):
                try:
                    updated_name = dt.datetime.strptime(file.name, '%m-%d-%y %H-%M-%S').strftime('%b %d, %Y %I:%M %p')
                except ValueError:
                    updated_name = file.name
                cls.save_dic[updated_name] = file
            for file in os.scandir(os.path.split(cls.selected_game_save)[0]):
                if file.name.endswith('.old'):
                    cls.save_dic['Undo Last Restore'] = file
        else:
            messagebox.showwarning(
                title=cls.title,
                message=f'No backed up saves exist for {cls.selected_game}.')
            return


        def restore_selected_save():
            '''
            Restores selected game save based on save clicked.
            Restores by renaming current save folder to "save.old" and then copying the backup to replace it.
            '''
            save_name = cls.save_dic[save_listbox.get(save_listbox.curselection())]
            backup_path = os.path.join(cls.backup_dest, cls.selected_game, save_name.name)
            if save_name.name.endswith('.old'):
                msg1 = 'This will delete the previously restored save and revert to the original.'
                msg2 = 'Are you sure? This will skip the recycle bin.'
                response = messagebox.askyesno(
                    title=cls.title,
                    message=msg1 + msg2)
                if response:
                    shutil.rmtree(save_name.path[:-4])
                    os.rename(save_name.path, save_name.path[:-4])
                    Restore_Game_Window.grab_release()
                    Restore_Game_Window.destroy()
                    cls.logger.info(f'Restored original save for {cls.selected_game}.')
                return
            if os.path.exists(f'{cls.selected_game_save}.old'):
                msg1 = 'Backup of current save before last restore already exists.'
                msg2 = 'Do you want to delete it? This will cancel the restore if you do not delete it.'
                response = messagebox.askyesno(
                    title=cls.title,
                    message=msg1 + msg2)
                if response:
                    shutil.rmtree(f'{cls.selected_game_save}.old')
                    cls.logger.info(f'Deleted original save before last restore for {cls.selected_game}.')
                else:
                    print('Canceling Restore.')
                    Restore_Game_Window.grab_release()
                    return
            # TODO Move old file to special backup folder instead of renaming to .old
            os.rename(cls.selected_game_save, f'{cls.selected_game_save}.old')
            shutil.copytree(backup_path, cls.selected_game_save)
            cls.logger.info(f'Restored save for {cls.selected_game}.')
            Restore_Game_Window.destroy()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        window_width = 300
        window_height = 220
        cls.tk_window_options(Restore_Game_Window, window_width, window_height)
        Restore_Game_Window.grab_set()

        RestoreInfo = ttk.Label(Restore_Game_Window,
            text='Select save to restore for', font=("Arial Bold", 10))
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=(10,0), padx=10)

        RestoreGame = ttk.Label(Restore_Game_Window,
            text=cls.selected_game, font=("Arial Bold", 10))
        RestoreGame.grid(columnspan=2, row=1, column=0, pady=(0,10), padx=10)

        save_listbox = Tk.Listbox(Restore_Game_Window, exportselection=False, font=("Arial Bold", 12), height=5,
            width=30)
        save_listbox.grid(columnspan=2, row=2, column=0, pady=5, padx=10)

        for item in cls.save_dic:
            save_listbox.insert(Tk.END, item)

        confirm_button = ttk.Button(Restore_Game_Window, text='Confirm', command=restore_selected_save, width=20)
        confirm_button.grid(row=3, column=0, padx=10, pady=10)

        CancelButton = ttk.Button(Restore_Game_Window, text='Cancel', command=Restore_Game_Window.destroy, width=20)
        CancelButton.grid(row=3, column=1, padx=10, pady=10)

        Restore_Game_Window.mainloop()


    @classmethod
    def explore_folder(cls, folder):
        '''
        Opens the selected games save location in explorer or backup folder.

        Arguments:

        folder -- Set to "Game Save" or "Backup" to determine folder that is opened in explorer
        '''
        if cls.selected_game == None:
            messagebox.showwarning(
                title=cls.title,
                message='No game is selected yet.')
        elif folder == 'Game Save':  # open game save location in explorer
            if not os.path.isdir(cls.selected_game_save):
                messagebox.showwarning(
                    title=cls.title,
                    message=f'Save location for {cls.selected_game} no longer exists')
            subprocess.Popen(f'explorer "{cls.selected_game_save}"')
        elif folder == 'Backup':  # open game backup location in explorer
            if not os.path.isdir(cls.base_backup_folder):
                messagebox.showwarning(
                    title=cls.title,
                    message=f'{cls.selected_game} has not been backed up yet.')
            subprocess.Popen(f'explorer "{cls.base_backup_folder}"')


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
        size_name = ("B", "KB", "MB", "GB", "TB")
        try:
            i = int(math.floor(math.log(total_size, 1024)))
            p = math.pow(1024, i)
            s = round(total_size / p, 2)
            return f'{s} {size_name[i]}'
        except ValueError:
            return '0 bits'


    @classmethod
    def add_game_to_database(cls):
        '''
        Adds game to database using entry inputs.
        '''
        game_name = cls.GameNameEntry.get()
        save_location = cls.GameSaveEntry.get().replace('/', '\\')
        if len(cls.get_selected_game_filename(game_name)) == 0:
            messagebox.showwarning(
                title=cls.title,
                message=f'Game name has no legal characters for a filename')
            return
        cls.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game_name})
        database_save_location = cls.cursor.fetchone()
        if database_save_location != None:
            messagebox.showwarning(
                title=cls.title,
                message=f"Can't add {cls.selected_game} to database.\nGame already exists.")
        else:
            if os.path.isdir(save_location):
                cls.GameSaveEntry.delete(0, Tk.END)
                cls.GameNameEntry.delete(0, Tk.END)
                cls.cursor.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
                    {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
                cls.database.commit()
                cls.game_listbox.insert(0, game_name)
                cls.logger.info(f'Added {game_name} to database.')
            else:
                messagebox.showwarning(
                    title=cls.title,
                    message=f'Save Location for {cls.selected_game} does not exist.')


    @classmethod
    def find_letters(cls):
        with os.popen("fsutil fsinfo drives") as data:
            letter_output = data.readlines()[1]
        words = re.findall('\S+', letter_output)[1:]
        result = []
        for letters in words:
            result.append(letters[0])
        if cls.debug:
            print(result)
        return result


    @classmethod
    def find_search_directories(cls, test=0):
        '''
        Finds the directories to use when searching for games.
        '''
        def callback():
            start = time.perf_counter()
            dirs_to_check = [
                rf":/Users/{cls.username}/AppData/Local",
                rf":/Users/{cls.username}/AppData/LocalLow",
                rf":/Users/{cls.username}/AppData/Roaming",
                rf":/Users/{cls.username}/Saved Games",
                rf":/Users/{cls.username}/Documents",
                r":/Program Files (x86)/Steam/steamapps/common",
                r":/Program Files/Steam/steamapps/common"
                ]
            drive_letters = cls.find_letters()
            for dir in dirs_to_check:
                for letter in drive_letters:
                    current_dir = letter + dir
                    if os.path.isdir(current_dir):
                        if 'documents' in current_dir.lower():
                            cls.initialdir = current_dir
                        cls.search_directories.append(current_dir)
            for custom_saved_dir in cls.data['custom_save_directories']:
                cls.search_directories.append(custom_saved_dir)
            if cls.debug:
                print(cls.search_directories)
            finish = time.perf_counter() # stop time for checking elaspsed runtime
            elapsed_time = round(finish-start, 2)
            if cls.debug:
                print(f'find_search_directories: {elapsed_time} seconds')
        SearchThread = Thread(target=callback)
        if test == 0:
            SearchThread.start()
        else:
            callback()


    @classmethod
    def open_smart_browse_window(cls):
        '''
        Smart Browse Progress window
        '''
        # closes window if it is already open so a new one can be created
        try:
            cls.smart_browse_win.destroy()
        except AttributeError:
            pass
        # opens window
        cls.smart_browse_win = Tk.Toplevel(cls.main_gui)
        cls.tk_window_options(cls.smart_browse_win, 340, 130, define_size=0)

        text = f'Looking for the game save directory for\n{cls.GameNameEntry.get()}'
        cls.info_label = Tk.Label(cls.smart_browse_win, text=text, font=("Arial Bold", 10))
        cls.info_label.grid(row=0, column=0, pady=(9))

        cls.progress = ttk.Progressbar(cls.smart_browse_win, orient=Tk.HORIZONTAL, length=360, mode='determinate')
        cls.progress.grid(row=1, column=0, pady=(5,10), padx=20)

        cls.s_browse = ttk.Button(cls.smart_browse_win, text='Browse', command=lambda: cls.browse(cls.best_dir),
            width=23)
        cls.s_browse.grid(row=2, column=0, pady=(5,10))
        cls.s_browse.config(state='disabled')
        cls.smart_browse_win.focus_force()


    @staticmethod
    def nonascii(string):
        '''
        Removes ASCII characters.
        '''
        encoded_string = string.encode("ascii", "ignore")
        decode_string = encoded_string.decode()
        return decode_string


    @classmethod
    def game_save_location_search(cls, game_name, test=0):
        overall_start = time.perf_counter() # start time for checking elaspsed runtime
        best_score = 0
        break_used = 0
        if cls.debug:
            print(f'\nGame: {game_name}')
        current_score = 0
        cls.best_dir = cls.initialdir
        possible_dir = ''
        if test == 0:
            cls.progress['maximum'] = len(cls.search_directories) + 1
        for directory in cls.search_directories:
            if cls.debug:
                print(f'\nCurrent Search Directory: {directory}')
            directory_start = time.perf_counter()
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir in dirs:
                    if game_name.lower().replace(' ', '') in dir.lower().replace(' ', ''):
                        possible_dir = os.path.join(root, dir)
                        if possible_dir != '':
                            if cls.debug:
                                print(f'\n{possible_dir}')
                        for found_root, found_dirs, found_files in os.walk(possible_dir, topdown=False):
                            for found_file in found_files:
                            # file scoring TODO add a way to track scoring that applies
                                # + scorers
                                for item, score in cls.data['file_positive_scoring'].items():
                                    if item in found_file.lower():
                                        current_score += score
                                # - scorers
                                for item, score in cls.data['file_negative_scoring'].items():
                                    if item in found_file.lower():
                                        current_score -= score
                            for found_dir in found_dirs:
                            # folder scoring
                                # + scorers
                                for item, score in cls.data['folder_positive_scoring'].items():
                                    if item in found_dir.lower():
                                        current_score += score
                                # - scorers
                                for item, score in cls.data['folder_negative_scoring'].items():
                                    if item in found_dir.lower():
                                        current_score -= score
                        if cls.debug:
                            print(f'Score {current_score}')
                        break
            # update based on high score
            directory_finish = time.perf_counter()
            if cls.debug:
                print(f'Dir Search Time: {round(directory_finish-directory_start, 2)} seconds')
            if test == 0:
                cls.progress['value'] += 1
            if current_score > best_score:
                best_score = current_score
                cls.best_dir = os.path.abspath(possible_dir)
                # early break if threshold is met TODO verify for premature breaks
                if current_score > 600:
                    break_used = 1
                    break
            current_score = 0
        overall_finish = time.perf_counter() # stop time for checking elaspsed runtime
        elapsed_time = round(overall_finish-overall_start, 2)
        if cls.debug:
            print(f'\n{game_name}\nOverall Search Time: {elapsed_time} seconds')
            print(f'Path Used: {cls.best_dir}')
            print(f'Path Score: {best_score}')
        if test == 0:
            # FIXME test more
            game_save = os.path.abspath(cls.GameSaveEntry.get())
            if game_save != None:
                if cls.best_dir in game_save:
                    print('Found save is correct.')
                else:
                    print('Found save is incorrect.')
                    messagebox.showinfo(
                        title=cls.title,
                        message=f'Smart Browse found a different directory for the current game.')
        else:
            return cls.best_dir
        if break_used:
            print('Early Break Used')
        cls.progress['value'] = cls.progress['maximum']
        limit = 50
        if cls.best_dir == cls.initialdir:
            msg = 'Nothing Found\nBrowse will open in the default folder'
            print(msg)
            info = msg
        elif len(cls.best_dir) > limit:
            info = f'Path Found in {elapsed_time} seconds\n...{cls.best_dir[-limit:]}'
        else:
            info = f'Path Found in {elapsed_time} seconds\n{cls.best_dir[-limit:]}'
        cls.s_browse.config(state='normal')
        cls.info_label.config(text=info)
        winsound.PlaySound("Exclamation", winsound.SND_ALIAS)


    @classmethod
    def smart_browse(cls):
        '''
        Searches for a starting point for the save location browser.
        '''
        # removes illegal file characters
        game_name = cls.get_selected_game_filename(cls.GameNameEntry.get())
        print(game_name)
        # checks if no game name is in entry box.
        if len(game_name) == 0:
            messagebox.showwarning(
                title=cls.title,
                message='Smart Browse requires a game name to be entered.')
            return
        cls.open_smart_browse_window()
        # looks for folders with the games name
        SearchThread = Thread(target=cls.game_save_location_search, args=(game_name,), daemon=True)
        SearchThread.start()


    @classmethod
    def browse(cls, initial_dir=None):
        '''
        Opens a file dialog so a save directory can be chosen.
        It starts in the My Games folder in My Documents if it exists within a limited drive letter search.
        '''
        if initial_dir == None:
            starting_point = cls.initialdir
            current_save_location = cls.GameSaveEntry.get()
            if os.path.exists(current_save_location):
                starting_point = current_save_location
        else:
            starting_point = initial_dir
            cls.smart_browse_win.destroy()
        save_dir = filedialog.askdirectory(initialdir=starting_point, title="Select Save Directory")
        cls.GameSaveEntry.delete(0, Tk.END)
        cls.GameSaveEntry.insert(0, save_dir)


    @classmethod
    def delete_game_from_db(cls):
        '''
        Deletes selected game from SQLite Database.
        '''
        if cls.selected_game == None:
            messagebox.showwarning(
                title=cls.title,
                message='No game is selected yet.')
            return
        delete_check = messagebox.askyesno(
            title=cls.title,
            message=f'Are you sure that you want to delete {cls.selected_game}?')
        if delete_check:
            cls.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': cls.selected_game})
            cls.database.commit()
            cls.game_listbox.delete(cls.game_listbox.curselection()[0])
            cls.delete_update_entry()
            if os.path.isdir(cls.base_backup_folder):
                response = messagebox.askyesno(
                    title=cls.title,
                    message='Do you want to delete the backed up saves as well?')
                if response:
                    os.path.join(cls.backup_dest, cls.selected_game)
                    try:
                        shutil.rmtree(cls.base_backup_folder)
                        cls.logger.info(f'Deleted backups for{cls.selected_game}.')
                    except PermissionError:
                        cls.logger.warning(f'Failed to delete backups for {cls.selected_game}')
                        messagebox.showerror(
                            title=cls.title,
                            message='Failed to delete directory\nPermission Error')
                cls.logger.info(f'Deleted {cls.selected_game} from database.')


    @classmethod
    def update_game(cls):
        '''
        Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.
        '''
        if cls.selected_game == None:
            messagebox.showwarning(
                title=cls.title,
                message='No game is selected yet.')
            return
        game_name = cls.GameNameEntry.get()
        save_location = cls.GameSaveEntry.get().replace('/', '\\')
        if os.path.isdir(save_location):
            sql_update_query  ='''UPDATE games
                    SET game_name = ?, save_location = ?
                    WHERE game_name = ?;'''
            data = (game_name, save_location, cls.selected_game)
            cls.cursor.execute(sql_update_query , data)
            cls.database.commit()
            new_name = os.path.join(cls.backup_dest, cls.get_selected_game_filename(game_name))
            # FIXME renaming twice in a row brings up an error
            os.rename(cls.base_backup_folder, new_name)
            index = cls.game_listbox.curselection()
            print(index)
            cls.game_listbox.delete(Tk.ACTIVE)
            cls.game_listbox.insert(index, game_name)
            cls.logger.info(f'Updated {cls.selected_game} in database.')
        else:
            messagebox.showwarning(
                title=cls.title,
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


    @classmethod
    def delete_update_entry(cls, Update = 0):
        '''
        Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.

        Arguments:

        Update -- 1 or 0 (default = 0)
        '''
        # clears entry boxes
        cls.GameNameEntry.delete(0, Tk.END)
        cls.GameSaveEntry.delete(0, Tk.END)
        # updates entry boxes to show currently selected game in listbox
        if Update == 1:
            # script wide variables for selected game
            cls.selected_game = cls.game_listbox.get(cls.game_listbox.curselection())
            cls.game_filename = cls.get_selected_game_filename()
            cls.selected_game_save = cls.get_selected_game_save()
            cls.GameNameEntry.insert(0, cls.selected_game)
            cls.GameSaveEntry.insert(0, cls.selected_game_save)
            cls.base_backup_folder = os.path.join(cls.backup_dest, cls.game_filename)
            # enables all buttons to be pressed once a selection is made
            for button in [cls.BackupButton, cls.ExploreSaveButton]: #  TODO only works with 2 or more games
                button.config(state='normal')
            if os.path.isdir(cls.base_backup_folder):
                set_state = 'normal'
            else:
                set_state = 'disabled'
            for button in [cls.ExploreBackupButton, cls.RestoreButton]:
                button.config(state=set_state)
            total_size = cls.convert_size(cls.base_backup_folder)
            cls.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name",
                {'game_name': cls.selected_game})
            last_backup = cls.cursor.fetchone()[0]
            if last_backup != 'Never':
                time_since = cls.readable_time_since(dt.datetime.strptime(last_backup, '%Y/%m/%d %H:%M:%S'))
                info1 = f'{cls.selected_game} was last backed up {time_since}\n'
                info2 = f'Game Backup Size: {total_size} from {len(os.listdir(cls.base_backup_folder))} backups'
                info = info1 + info2
            else:
                info = f'{cls.selected_game} has not been backed up\n'
            cls.ActionInfo.config(text=info)
            cls.BackupButton.focus_set()


    @classmethod
    def close_db(cls):
        '''
        Closes the database and quits the program when closing the interface.
        '''
        cls.database.close
        # FIXME fails to close if filedialog is left open
        exit()


    @classmethod
    def open_interface_window(cls):
        cls.sorted_list = cls.sorted_games()

        # Defaults
        BoldBaseFont = "Arial Bold"

        cls.main_gui = Tk.Tk()
        cls.main_gui.protocol("WM_DELETE_WINDOW", cls.close_db)
        window_width = 670
        window_height = 550
        cls.tk_window_options(cls.main_gui, window_width, window_height)
        # cls.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # Main Row 0
        Backup_Frame = Tk.Frame(cls.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        info_text = f'Total Games: {len(cls.sorted_list)}\nTotal Backup Size: {cls.convert_size(cls.backup_dest)}'
        Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
        Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        cls.BackupButton = ttk.Button(Backup_Frame, text='Backup Save', state='disabled',
            command=cls.backup_save, width=button_width)
        cls.BackupButton.grid(row=3, column=1, padx=5, pady=5)

        cls.RestoreButton = ttk.Button(Backup_Frame, text='Restore Save', state='disabled',
            command=cls.restore_save, width=button_width)
        cls.RestoreButton.grid(row=3, column=2, padx=5)

        cls.ExploreSaveButton = ttk.Button(Backup_Frame, text='Explore Save Location', state='disabled',
            command=lambda: cls.explore_folder('Game Save'), width=button_width)
        cls.ExploreSaveButton.grid(row=4, column=1, padx=5)

        cls.ExploreBackupButton = ttk.Button(Backup_Frame, text='Explore Backup Location', state='disabled',
            command=lambda: cls.explore_folder('Backup'), width=button_width)
        cls.ExploreBackupButton.grid(row=4, column=2, padx=5)

        # Main Row 1
        instruction = 'Select a Game\nto continue'
        cls.ActionInfo = Tk.Label(cls.main_gui, text=instruction, font=(BoldBaseFont, 10))
        cls.ActionInfo.grid(columnspan=4, row=1, column=0, padx=5, pady= 5)

        # Main Row 2
        cls.ListboxFrame = Tk.Frame(cls.main_gui)
        cls.ListboxFrame.grid(columnspan=4, row=2, column=0,  padx=(20, 20), pady=(5, 10))

        cls.scrollbar = Tk.Scrollbar(cls.ListboxFrame, orient=Tk.VERTICAL)
        cls.scrollbar.grid(row=0, column=3, sticky='ns', rowspan=3)

        cls.game_listbox = Tk.Listbox(cls.ListboxFrame, exportselection=False,
            yscrollcommand=cls.scrollbar.set, font=(BoldBaseFont, 12), height=10, width=60)
        cls.game_listbox.bind('<<ListboxSelect>>', lambda event, game_listbox=cls.game_listbox,:
            cls.delete_update_entry(1))
        cls.game_listbox.grid(columnspan=3, row=0, column=0)
        cls.scrollbar.config(command=cls.game_listbox.yview)

        for item in cls.sorted_list:
            cls.game_listbox.insert(Tk.END, item)

        # Main Row 3
        Add_Game_Frame = Tk.LabelFrame(cls.main_gui, text='Manage Games')
        Add_Game_Frame.grid(columnspan=4, row=3, padx=15, pady=(5, 17))

        EnterGameLabel = Tk.ttk.Label(Add_Game_Frame, text='Enter Game Name')
        EnterGameLabel.grid(row=0, column=0)

        entry_width = 65
        cls.GameNameEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
        cls.GameNameEntry.grid(row=0, column=1, columnspan=3, pady=8, padx=5)

        EnterSaveLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Save Location')
        EnterSaveLabeL.grid(row=1, column=0)

        cls.GameSaveEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
        cls.GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5, padx=10)

        browse_button_width = 13
        SmartBrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Smart Browse', width=browse_button_width,
            command=cls.smart_browse)
        SmartBrowseButton.grid(row=0, column=4, padx=10)

        BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse', width=browse_button_width,
            command=cls.browse)
        BrowseButton.grid(row=1, column=4, padx=10)

        # Button Frame Row 2
        Button_Frame = Tk.Frame(Add_Game_Frame)
        Button_Frame.grid(columnspan=5, row=2, pady=(5, 5))

        button_padx = 4
        button_pady = 5
        ConfirmAddButton = Tk.ttk.Button(Button_Frame, text='Add Game',
            command=cls.add_game_to_database, width=20)
        ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

        UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Game',
            command=cls.update_game, width=20)
        UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

        RemoveButton = ttk.Button(Button_Frame, text='Remove Game',
            command=cls.delete_game_from_db, width=20)
        RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
            command=cls.delete_update_entry, width=20)
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        cls.database_check()
        cls.main_gui.mainloop()


    @classmethod
    def run(cls):
        '''
        Runs everything needed to make the program work.
        '''
        if cls.output:
            sys.stdout = open("output.txt", "w")
        cls.backup_dest_check()
        cls.find_search_directories()
        cls.open_interface_window()
        if cls.output:
            sys.stdout.close()


if __name__ == '__main__':
    Backup.run()
