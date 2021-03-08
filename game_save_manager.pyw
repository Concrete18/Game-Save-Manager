from logging.handlers import RotatingFileHandler
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import datetime as dt
import tkinter as Tk
import logging as lg
import subprocess
import getpass
import sqlite3
import shutil
import json
import time
import math
import os
import re


class Backup:

    # sets script directory in case current working directory is different
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    def __init__(self):
        '''
        Sets up backup configuration, database and logger.
        '''
        # settings setup
        with open('settings.json') as json_file:
            self.data = json.load(json_file)
        # backup destination setup
        self.backup_dest = self.data['settings']['backup_dest']
        self.backup_dest_check()

        self.backup_redundancy = self.data['settings']['backup_redundancy']
        if type(self.backup_redundancy) is not int or self.backup_redundancy > 4:
            self.backup_redundancy = 4
        self.disable_resize = self.data['settings']['disable_resize']
        self.center_window = self.data['settings']['center_window']

        # sets up search directories
        self.username = getpass.getuser()
        self.initialdir = "C:/"
        self.search_directories = []
        self.find_search_directories()

        # logger setup
        log_formatter = lg.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p')
        self.logger = lg.getLogger(__name__)
        self.logger.setLevel(lg.DEBUG) # Log Level
        my_handler = RotatingFileHandler('Game_Backup.log', maxBytes=5*1024*1024, backupCount=2)
        my_handler.setFormatter(log_formatter)
        self.logger.addHandler(my_handler)

        # database creation
        self.database = sqlite3.connect('game_list.db')
        self.cursor = self.database.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
            game_name text,
            save_location text,
            last_backup text
            )''')
        self.sorted_list = self.sorted_games()


    def backup_dest_check(self):
        '''
        Checks if backup destination in settings exists and asks if you want to choose one if it does not.
        '''
        if not os.path.exists(self.backup_dest):
            msg = 'Do you want to choose a save backup directory instead of using a default within the program folder?'
            response = messagebox.askyesno(title='Game Save Manager', message=msg)
            if response:
                self.backup_dest = filedialog.askdirectory(initialdir="C:/", title="Select Save Backup Directory")
                if os.path.exists(self.backup_dest):
                    self.data['settings']['backup_dest'] = self.backup_dest
                    json_object = json.dumps(self.data, indent = 4)  # Serializing json
                    with open('settings.json', "w") as outfile:  # Writing to sample.json
                        outfile.write(json_object)
                else:
                    messagebox.showwarning(title='Game Save Manager', message='Path does not exist.')
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
            msg = f'Save Locations for the following games do not exist.\n{missing_save_string}'
            messagebox.showwarning(title='Game Save Manager', message=msg)
            self.logger.debug(f'Missing Save Locations:{missing_save_string}')
        elif total_missing_saves > 5: # warns of unfound save locations if list is greater then 5 entries
            msg = 'More than 5 save locations do not exist.'
            messagebox.showwarning(title='Game Save Manager', message=msg)
            self.logger.debug(f'More then 5 save locations in the database do not exist.')


    def get_selected_game_filename(self, game=None):
        '''
        Removes illegal characters and shortens the selected games name so it can become a valid filename.
        '''
        if game == None:
            game = self.selected_game
        game.replace('&', 'and')
        char_removal = re.compile('[^a-zA-Z0-9\s]')
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
                shutil.rmtree(sorted_list[i])
            self.logger.info(f'{game} had more then {self.backup_redundancy} Saves. Deleted oldest saves.')


    def backup_save(self):
        '''
        Backups up the game entered based on SQLite save location data to the specified backup folder.
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        current_time = dt.datetime.now().strftime("%m-%d-%y %H-%M-%S")
        game_name = self.selected_game
        total_size = self.convert_size(os.path.join(self.backup_dest, self.selected_game))
        dest = os.path.join(self.base_backup_folder, current_time)
        last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.ActionInfo.config(text=f'Backing up {game_name}\n')
        try:
            def backup():
                shutil.copytree(self.selected_game_save, dest)
                self.delete_oldest(self.game_filename)
                info1 = f'{game_name} has been backed up.\n'
                info2 = f'Game Backup Size: {total_size} from {len(os.listdir(self.base_backup_folder))} backups'
                self.ActionInfo.config(text=info1 + info2)
                self.game_listbox.delete(Tk.ACTIVE)
                self.game_listbox.insert(0, game_name)
                self.logger.info(f'Backed up Save for {game_name}.')
            BackupThread = Thread(target=backup)
            BackupThread.start()
            self.cursor.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
            {'game_name': game_name, 'last_backup': last_backup})
            self.database.commit()
        except FileNotFoundError:
            messagebox.showwarning(title='Game Save Manager', message='Action Failed - File location does not exist.')
            self.logger.error(f'Failed to Backed up Save for {game_name}. File location does not exist.')
        except FileExistsError:
            messagebox.showwarning(title='Game Save Manager', message='Action Failed - Save Already Backed up.')
            self.logger.error(f'Failed to Backed up Save for {game_name}. Save Already Backed up.')


    def tk_window_options(self, window_name, window_width, window_height, define_size=0):
        '''
        Disables window resize and centers window if config enables each.
        '''
        window_name.title('Game Save Manager')
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
        msg = f'Are you sure you want to backup {self.selected_game}'
        response = messagebox.askquestion(title='Game Save Manager', message=msg)
        if response == 'yes':
            self.backup_save()
        else:
            self.game_listbox.activate(0)
            return
        print(event)


    def restore_save(self):
        '''
        Opens an interface for picking the dated backup of the selected game to restore.
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        backup_path = self.base_backup_folder
        self.save_dic = {}
        if os.path.exists(backup_path):
            for file in os.scandir(backup_path):
                try:
                    updated_name = dt.datetime.strptime(file.name, '%m-%d-%y %H-%M-%S').strftime('%b %d, %Y %I:%M %p')
                except ValueError:
                    updated_name = file.name
                self.save_dic[updated_name] = file
            for file in os.scandir(os.path.split(self.selected_game_save)[0]):
                if file.name.endswith('.old'):
                    self.save_dic['Undo Last Restore'] = file
        else:
            messagebox.showwarning(title='Game Save Manager', message=f'No backed up saves exist for {self.selected_game}.')
            return


        def restore_selected_save():
            '''
            Restores selected game save based on save clicked.
            Restores by renaming current save folder to "save.old" and then copying the backup to replace it.
            '''
            save_name = self.save_dic[save_listbox.get(save_listbox.curselection())]
            backup_path = os.path.join(self.backup_dest, self.selected_game, save_name.name)
            if save_name.name.endswith('.old'):
                msg1 = 'This will delete the previously restored save and revert to the original.'
                msg2 = 'Are you sure? This will skip the recycle bin.'
                response = messagebox.askyesno(title='Game Save Manager', message=msg1 + msg2)
                if response:
                    shutil.rmtree(save_name.path[:-4])
                    os.rename(save_name.path, save_name.path[:-4])
                    Restore_Game_Window.grab_release()
                    Restore_Game_Window.destroy()
                    self.logger.info(f'Restored original save for {self.selected_game}.')
                return
            if os.path.exists(f'{self.selected_game_save}.old'):
                msg1 = 'Backup of current save before last restore already exists.'
                msg2 = 'Do you want to delete it? This will cancel the restore if you do not delete it.'
                response = messagebox.askyesno(title='Game Save Manager', message=msg1 + msg2)
                if response:
                    shutil.rmtree(f'{self.selected_game_save}.old')
                    self.logger.info(f'Deleted original save before last restore for {self.selected_game}.')
                else:
                    print('Canceling Restore.')
                    Restore_Game_Window.grab_release()
                    return
            # TODO Move old file to special backup folder instead of renaming to .old
            os.rename(self.selected_game_save, f'{self.selected_game_save}.old')
            shutil.copytree(backup_path, self.selected_game_save)
            self.logger.info(f'Restored save for {self.selected_game}.')
            Restore_Game_Window.destroy()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        window_width = 300
        window_height = 220
        self.tk_window_options(Restore_Game_Window, window_width, window_height)
        Restore_Game_Window.grab_set()

        RestoreInfo = ttk.Label(Restore_Game_Window,
            text='Select save to restore for', font=("Arial Bold", 10))
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=(10,0), padx=10)

        RestoreGame = ttk.Label(Restore_Game_Window,
            text=self.selected_game, font=("Arial Bold", 10))
        RestoreGame.grid(columnspan=2, row=1, column=0, pady=(0,10), padx=10)

        save_listbox = Tk.Listbox(Restore_Game_Window, exportselection=False, font=("Arial Bold", 12), height=5, width=30)
        save_listbox.grid(columnspan=2, row=2, column=0, pady=5, padx=10)

        for item in self.save_dic:
            save_listbox.insert(Tk.END, item)

        confirm_button = ttk.Button(Restore_Game_Window, text='Confirm', command=restore_selected_save, width=20)
        confirm_button.grid(row=3, column=0, padx=10, pady=10)

        CancelButton = ttk.Button(Restore_Game_Window, text='Cancel', command=Restore_Game_Window.destroy, width=20)
        CancelButton.grid(row=3, column=1, padx=10, pady=10)

        Restore_Game_Window.mainloop()


    def explore_folder(self, folder):
        '''
        Opens the selected games save location in explorer or backup folder.

        Arguments:

        folder -- Set to "Game Save" or "Backup" to determine folder that is opened in explorer
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
        elif folder == 'Game Save':  # open game save location in explorer
            if not os.path.isdir(self.selected_game_save):
                msg = f'Save location for {self.selected_game} no longer exists'
                messagebox.showwarning(title='Game Save Manager', message=msg)
            subprocess.Popen(f'explorer "{self.selected_game_save}"')
        elif folder == 'Backup':  # open game backup location in explorer
            if not os.path.isdir(self.base_backup_folder):
                msg = f'{self.selected_game} has not been backed up yet.'
                messagebox.showwarning(title='Game Save Manager', message=msg)
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
        size_name = ("B", "KB", "MB", "GB", "TB")
        try:
            i = int(math.floor(math.log(total_size, 1024)))
            p = math.pow(1024, i)
            s = round(total_size / p, 2)
            return f'{s} {size_name[i]}'
        except ValueError:
            return '0 bits'


    def add_game_to_database(self):
        '''
        Adds game to database using entry inputs.
        '''
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if len(self.get_selected_game_filename(game_name)) == 0:
            msg = f'Game name has no legal characters for a filename'
            messagebox.showwarning(title='Game Save Manager', message=msg)
            return
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game_name})
        database_save_location = self.cursor.fetchone()
        if database_save_location != None:
            msg = f"Can't add {self.selected_game} to database.\nGame already exists."
            messagebox.showwarning(title='Game Save Manager', message=msg)
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
                messagebox.showwarning(title='Game Save Manager', message=msg)


    @staticmethod
    def find_letters():
        letter_output = os.popen("fsutil fsinfo drives").readlines()[1]
        words = re.findall('\S+', letter_output)[1:]
        result = []
        for letters in words:
            result.append(letters[0])
        print(result)
        return result


    def find_search_directories(self):
        '''
        Finds the directories to use when searching for games.
        '''
        def callback():
            dirs_to_check = [
                rf":/Users/{self.username}/Saved Games",
                rf":/Users/{self.username}/Documents",
                rf":/Users/{self.username}/AppData",
                r":/Program Files (x86)/Steam/steamapps/common"
                ]
            drive_letters = self.find_letters()
            for dir in dirs_to_check:
                for letter in drive_letters:
                    current_dir = letter + dir
                    if os.path.isdir(current_dir):
                        if 'documents' in current_dir.lower():
                            self.initialdir = current_dir
                        self.search_directories.append(current_dir)
            for saved_dir in self.data['extra_save_directories']:
                # insert so it is before the steam common
                self.search_directories.append(saved_dir)
            print(self.search_directories)
        SearchThread = Thread(target=callback)
        SearchThread.start()


    def open_smart_browse_window(self):
        self.smart_browse_win = Tk.Toplevel(self.main_gui)
        self.tk_window_options(self.smart_browse_win, 460, 120, define_size=1)
        text = '''
        Looking for the game save directory.
        If nothing is found then your "My Documents" will be used.
        It can takes and average of 6 seconds.
        '''
        info_label = Tk.Label(self.smart_browse_win, text=text, font=("Arial Bold", 10))
        info_label.grid(row=0, column=0)

        okbutton = ttk.Button(self.smart_browse_win, text='OK', command=self.smart_browse_win.destroy,
            width=23)
        okbutton.grid(row=1, column=0)


    @staticmethod
    def print_nonascii(string):
        encoded_string = string.encode("ascii", "ignore")
        decode_string = encoded_string.decode()
        print(decode_string)


    def smart_browse(self):
        '''
        Searches for a starting point for the save location browser.
        '''
        overall_start = time.perf_counter() # start time for checking elaspsed runtime
        # removes illegal file characters
        game_name = self.GameNameEntry.get()
        game_name.replace('&', 'and')
        char_removal = re.compile('[^a-zA-Z0-9\s]')
        string = char_removal.sub('', game_name)
        game_name = re.sub("\s\s+" , " ", string).strip()[0:50]
        # checks if no game name is in entry box.
        if len(game_name) == 0:
            messagebox.showwarning(
                title='Game Save Manager',
                message='Smart Browse requires the a game name to be entered.')
            return
        # looks for folders with the games name
        topdown = False
        self.open_smart_browse_window()
        def callback():
            best_score = 0
            print(f'\nGame: {game_name}')
            current_score = 0
            best_dir = self.initialdir
            possible_dir = ''
            for directory in self.search_directories:
                print(f'\nCurrent Search Directory: {directory}\n')
                for root, dirs, files in os.walk(directory, topdown=topdown):
                    for dir in dirs:
                        if game_name.lower().replace(' ', '') in dir.lower().replace(' ', ''):
                            possible_dir = os.path.join(root, dir)
                            print(f'\n{possible_dir}')
                            for found_root, found_dirs, found_files in os.walk(possible_dir, topdown=topdown):
                                for found_file in found_files:
                                    # file scoring
                                    # + scorers
                                    if 'save' in found_file.lower():
                                        current_score += 1
                                    if 'autosave' in found_file.lower():
                                        current_score += 50
                                    if 'quicksave' in found_file.lower():
                                        current_score += 50
                                    if 'saveslot' in found_file.lower():
                                        current_score += 10
                                    if 'config' in found_file.lower():
                                        current_score += 1
                                    if '.data' in found_file.lower():
                                        current_score += 1
                                    if 'profile' in found_file.lower():
                                        current_score += 1
                                    if 'sav.' in found_file.lower():
                                        current_score += 50
                                    if '.sav' in found_file.lower():
                                        current_score += 50
                                    if 'screenshot' in dir.lower():
                                        current_score += 1
                                    # - scorers
                                    if 'nvidia' in found_file.lower():
                                        current_score -= 50
                                    # if 'nvidia' in found_dirs.lower():
                                    #     print('Found nvidia')
                                    #     current_score -= 50
                                    if found_file.endswith('.exe'):
                                        current_score -= 50
                            print(f'Score {current_score}')
                            break
                # update based on high score
                if current_score > best_score:
                    best_score = current_score
                    best_dir = possible_dir
                current_score = 0
            self.smart_browse_win.destroy()
            overall_finish = time.perf_counter() # stop time for checking elaspsed runtime
            elapsed_time = round(overall_finish-overall_start, 2)
            print(f'\nTook {elapsed_time} seconds to find {game_name}.')
            print('Path Used', os.path.abspath(best_dir))
            print(f'Path Score: {best_score}')
            if best_dir == self.initialdir:
                print('Nothing Found')
                return
            save_dir = filedialog.askdirectory(initialdir=os.path.abspath(best_dir), title="Select Save Directory")
            self.GameSaveEntry.delete(0, Tk.END)
            if save_dir != None:
                self.GameSaveEntry.insert(0, save_dir)
        SearchThread = Thread(target=callback, daemon=True)
        SearchThread.start()


    def browse(self):
        '''
        Opens a file dialog so a save directory can be chosen.
        It starts in the My Games folder in My Documents if it exists within a limited drive letter search.
        '''
        starting_point = self.initialdir
        current_save_location = self.GameSaveEntry.get()
        if os.path.exists(current_save_location):
            starting_point = current_save_location
        save_dir = filedialog.askdirectory(initialdir=starting_point, title="Select Save Directory")
        self.GameSaveEntry.delete(0, Tk.END)
        self.GameSaveEntry.insert(0, save_dir)


    def delete_game_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        msg = f'Are you sure that you want to delete {self.selected_game}?'
        delete_check = messagebox.askyesno(title='Game Save Manager', message=msg)
        if delete_check:
            self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.selected_game})
            self.database.commit()
            self.game_listbox.delete(self.game_listbox.curselection()[0])
            self.delete_update_entry()
            if os.path.isdir(self.base_backup_folder):
                msg = 'Do you want to delete the backed up saves as well?'
                response = messagebox.askyesno(title='Game Save Manager', message=msg)
                if response:
                    os.path.join(self.backup_dest, self.selected_game)
                    try:
                        shutil.rmtree(self.base_backup_folder)
                        self.logger.info(f'Deleted backups for{self.selected_game}.')
                    except PermissionError:
                        self.logger.warning(f'Failed to delete backups for {self.selected_game}')
                        msg = 'Failed to delete directory\nPermission Error'
                        messagebox.showerror(title='Game Save Manager',message=msg)
                self.logger.info(f'Deleted {self.selected_game} from database.')


    def update_game(self):
        '''
        Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
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
            # FIXME renaming twice in a row brings up an error
            os.rename(self.base_backup_folder, new_name)
            index = self.game_listbox.curselection()
            print(index)
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(index, game_name)
            self.logger.info(f'Updated {self.selected_game} in database.')
        else:
            msg = f'Save Location does not exist.'
            messagebox.showwarning(title='Game Save Manager', message=msg)


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


    def delete_update_entry(self, Update = 0):
        '''
        Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.

        Arguments:

        Update -- 1 or 0 (default = 0)
        '''
        # clears entry boxes
        self.GameNameEntry.delete(0, Tk.END)
        self.GameSaveEntry.delete(0, Tk.END)
        # updates entry boxes to show currently selected game in listbox
        if Update == 1:
            # script wide variables for selected game
            self.selected_game = self.game_listbox.get(self.game_listbox.curselection())
            self.game_filename = self.get_selected_game_filename()
            self.selected_game_save = self.get_selected_game_save()
            self.GameNameEntry.insert(0, self.selected_game)
            self.GameSaveEntry.insert(0, self.selected_game_save)
            self.base_backup_folder = os.path.join(self.backup_dest, self.game_filename)
            # enables all buttons to be pressed once a selection is made
            for button in [self.BackupButton, self.ExploreSaveButton]: #  TODO only works with 2 or more games
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
        self.database.close
        # FIXME fails to close if filedialog is left open
        exit()


    def run_gui(self):
        # Defaults
        BoldBaseFont = "Arial Bold"

        self.main_gui = Tk.Tk()
        self.main_gui.protocol("WM_DELETE_WINDOW", self.close_db)
        window_width = 670
        window_height = 550
        self.tk_window_options(self.main_gui, window_width, window_height)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # Main Row 0
        Backup_Frame = Tk.Frame(self.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        info_text = f'Total Games: {len(self.sorted_list)}\nTotal Backup Size: {self.convert_size(self.backup_dest)}'
        Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
        Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        self.BackupButton = ttk.Button(Backup_Frame, text='Backup Save', state='disabled',
            command=self.backup_save, width=button_width)
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
        self.scrollbar.grid(row=0, column=3, sticky='ns', rowspan=3)

        self.game_listbox = Tk.Listbox(self.ListboxFrame, exportselection=False,
            yscrollcommand=self.scrollbar.set, font=(BoldBaseFont, 12), height=10, width=60)
        self.game_listbox.bind('<<ListboxSelect>>', lambda event, game_listbox=self.game_listbox,:
            self.delete_update_entry(1))
        self.game_listbox.grid(columnspan=3, row=0, column=0)
        self.scrollbar.config(command=self.game_listbox.yview)

        for item in self.sorted_list:
            self.game_listbox.insert(Tk.END, item)

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

        SmartBrowseButton = Tk.ttk.Button(Add_Game_Frame, text='S-Browse',
            command=self.smart_browse)
        SmartBrowseButton.grid(row=0, column=4, padx=10)

        BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse',
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
            command=self.delete_update_entry, width=20)
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        self.database_check()
        self.main_gui.mainloop()

if __name__ == '__main__':
    App = Backup()
    App.run_gui()
