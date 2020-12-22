from logging.handlers import RotatingFileHandler
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import datetime as dt
import tkinter as Tk
import logging as lg
import subprocess
import sqlite3
import shutil
import json
import math
import os
import re


class Backup:


    def __init__(self):
        '''
        Sets up backup configuration, database and logger.
        '''
        self.selected_game = None
        self.save_dic = {}
        self.filename_regex = re.compile('[^a-zA-Z0-9\s]')
        # settings setup
        with open('settings.json') as json_file:
            data = json.load(json_file)
        self.backup_dest = data['settings']['backup_dest']
        if not os.path.exists(self.backup_dest):
            messagebox.showwarning(title='Game Save Manager', message='Backup destination does not exist.')
        self.backup_redundancy = data['settings']['backup_redundancy']
        if type(self.backup_redundancy) is not int or self.backup_redundancy > 4:
            self.backup_redundancy = 4
        self.disable_resize = data['settings']['disable_resize']
        self.center_window = data['settings']['center_window']
        # logger setup
        log_formatter = lg.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p')
        self.logger = lg.getLogger(__name__)
        self.logger.setLevel(lg.DEBUG)
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


    def selected_game_filename(self, game=None):
        '''
        Removes illegal characters and shortens the selected games name so it can become a valid filename.
        '''
        if game != None:
            return self.filename_regex.sub('', game)[0:31]
        return self.filename_regex.sub('', self.selected_game)[0:31]


    def game_save_loc(self):
        '''
        Returns the save location of the selected game from the SQLite Database.
        '''
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name",
            {'game_name': self.selected_game})
        return self.cursor.fetchone()[0]


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
        game = self.selected_game_filename()
        total_size = self.convert_size(os.path.join(self.backup_dest, self.selected_game))
        base_backup_folder = os.path.join(self.backup_dest, game)
        dest = os.path.join(base_backup_folder, current_time)
        save_location = self.game_save_loc()
        try:
            def backup():
                shutil.copytree(save_location, dest)
                self.delete_oldest(game)
            BackupThread = Thread(target=backup)
            BackupThread.start()
            info1 = f'{game} backed up to set backup destination.\n'
            info2 = f'Game Backup Size: {total_size} from {len(os.listdir(base_backup_folder))} backups'
            self.ActionInfo.config(text=info1 + info2)
            last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            self.cursor.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
            {'game_name': game, 'last_backup': last_backup})
            self.database.commit()
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(0, game)
            self.logger.info(f'Backed up Save for {game}.')
        except FileNotFoundError:
            messagebox.showwarning(title='Game Save Manager', message='Action Failed - File location does not exist.')
            self.logger.error(f'Failed to Backed up Save for {game}. File location does not exist.except')
        except FileExistsError:
            messagebox.showwarning(title='Game Save Manager', message='Action Failed - Save Already Backed up.')
            self.logger.error(f'Failed to Backed up Save for {game}. Save Already Backed up.')


    def tk_window_options(self, window_name, window_width, window_height):
        '''
        Disables window resize and centers window if config enables each.
        '''
        if self.disable_resize:  # sets window to not resize if disable_resize is set to 1
            window_name.resizable(width=False, height=False)
        if self.center_window == 1:
            width_pos = int((window_name.winfo_screenwidth()-window_width)/2)
            height_pos = int((window_name.winfo_screenheight()-window_height)/2)
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
        backup_path = os.path.join(self.backup_dest, self.selected_game)
        self.save_dic = {}
        if os.path.exists(backup_path):
            for file in os.scandir(backup_path):
                try:
                    updated_name = dt.datetime.strptime(file.name, '%m-%d-%y %H-%M-%S').strftime('%b %d, %Y %I:%M %p')
                except ValueError:
                    updated_name = file.name
                self.save_dic[updated_name] = file
            for file in os.scandir(os.path.split(self.game_save_loc())[0]):
                if file.name.endswith('.old'):
                    self.save_dic['Undo Last Restore'] = file
        else:
            messagebox.showwarning(title='Game Save Manager', message='No saves exist for this game.')


        def restore_game_pressed():
            '''
            Restores selected game save based on save clicked.
            Restores by renaming current save folder to "save.old" and then copying the backup to replace it.
            '''
            save_name = self.save_dic[save_listbox.get(save_listbox.curselection())]
            save_location = self.game_save_loc()
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
            if os.path.exists(f'{save_location}.old'):
                msg1 = 'Backup of current save before last restore already exists.'
                msg2 = 'Do you want to delete it? This will cancel the restore if you do not delete it.'
                response = messagebox.askyesno(title='Game Save Manager', message=msg1 + msg2)
                if response:
                    shutil.rmtree(f'{save_location}.old')
                    self.logger.info(f'Deleted original save before last restore for {self.selected_game}.')
                else:
                    print('Canceling Restore.')
                    Restore_Game_Window.grab_release()
                    return
            os.rename(save_location, f'{save_location}.old')
            shutil.copytree(backup_path, save_location)
            self.logger.info(f'Restored save for {self.selected_game}.')
            Restore_Game_Window.destroy()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        Restore_Game_Window.title('Game Save Manager')
        Restore_Game_Window.iconbitmap('Save_Icon.ico')
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

        confirm_button = ttk.Button(Restore_Game_Window, text='Confirm', command=restore_game_pressed, width=20)
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
            return
        if folder == 'Game Save':
            subprocess.Popen(f'explorer "{self.game_save_loc()}"')
        elif folder == 'Backup':
            subprocess.Popen(f'explorer "{os.path.join(self.backup_dest, self.selected_game_filename())}"')


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
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game_name})
        database_save_location = self.cursor.fetchone()
        if database_save_location != None:
            msg = "Can't add game to database.\nGame already exists."
            messagebox.showwarning(title='Game Save Manager', message=msg)
            return
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
                messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')


    def browse_for_save(self):
        '''
        Opens a file dialog so a save directory can be chosen.
        '''
        save_dir = filedialog.askdirectory(initialdir="C:/", title="Select Save Directory")
        self.GameSaveEntry.delete(0, Tk.END)
        self.GameSaveEntry.insert(0, save_dir)


    def delete_game_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        msg = 'Are you sure that you want to delete the game?'
        Delete_Check = messagebox.askyesno(title='Game Save Manager', message=msg)
        if Delete_Check:
            self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.selected_game})
            self.database.commit()
            self.game_listbox.delete(self.game_listbox.curselection()[0])
            self.delete_update_entry()
            msg = 'Do you want to delete the backed up game saves as well?'
            response = messagebox.askyesno(title='Game Save Manager', message=msg)
            if response:
                os.path.join(self.backup_dest, self.selected_game)
                try:
                    shutil.rmtree(os.path.join(self.backup_dest, self.selected_game))
                except PermissionError:
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
        save_location = self.GameSaveEntry.get()
        save_location = save_location.replace('/', '\\')
        if os.path.isdir(save_location):
            sql_update_query  ='''UPDATE games
                    SET game_name = ?, save_location = ?
                    WHERE game_name = ?;'''
            data = (game_name, save_location, self.selected_game)
            self.cursor.execute(sql_update_query , data)
            self.database.commit()
            os.rename(os.path.join(self.backup_dest, self.selected_game), os.path.join(self.backup_dest, game_name))
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(0, game_name)
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
            self.selected_game = self.game_listbox.get(self.game_listbox.curselection())  # script wide variable for selected game
            self.GameNameEntry.insert(0, self.selected_game)
            self.GameSaveEntry.insert(0, self.game_save_loc())
            # enables all buttons to be pressed once a selection is made
            for button in [
                self.BackupButton,
                self.RestoreButton,
                self.ExploreBackupButton,
                self.ExploreSaveButton
                ]:
                button.config(state='normal')
            base_backup_folder = os.path.join(self.backup_dest, self.selected_game)
            total_size = self.convert_size(base_backup_folder)
            self.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name",
                {'game_name': self.selected_game})
            last_backup = self.cursor.fetchone()[0]
            if last_backup != 'Never':
                time_since = self.readable_time_since(dt.datetime.strptime(last_backup, '%Y/%m/%d %H:%M:%S'))
                info1 = f'{self.selected_game} was last backed up {time_since}\n'
                info2 = f'Game Backup Size: {total_size} from {len(os.listdir(base_backup_folder))} backups'
                info = info1 + info2
            else:
                info = f'{self.selected_game} has not been backed up\n'
            self.ActionInfo.config(text=info)
            self.BackupButton.focus_set()


    def run_gui(self):
        # Defaults
        BoldBaseFont = "Arial Bold"

        self.main_gui = Tk.Tk()
        self.main_gui.title('Game Save Manager')
        self.main_gui.iconbitmap('Save_Icon.ico')
        window_width = 670
        window_height = 550
        self.tk_window_options(self.main_gui, window_width, window_height)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # Main Row 0
        Backup_Frame = Tk.Frame(self.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        info_text = f'Total Games: {len(self.sorted_games())}\nTotal Backup Size: {self.convert_size(self.backup_dest)}'
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

        sorted_list = self.sorted_games()
        for item in sorted_list:
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

        BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse',
            command=self.browse_for_save)
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

        self.database.close()

if __name__ == '__main__':
    App = Backup()
    App.run_gui()
