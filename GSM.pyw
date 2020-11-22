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


class Backup:


    def __init__(self):
        '''Sets up backup configuration, database and logger.'''
        self.selected_game = None
        self.save_dic = {}
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


    def Database_Check(self):
        '''Checks for missing save directories from database.'''
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


    @staticmethod
    def Sanitize_For_Filename(string):
        '''Removes illegal characters from string so it can become a valid filename.

        Arguments:

        string -- string that is sanitized
        '''
        for char in ('<', '>', ':', '/', '\\', '{', '}','|', '?', '!', '*', '#', '%','&', '$', '"', "'"):
            string = string.replace(char,'')
        if len(string) > 31:
            return string[0:31]
        else:
            return string


    def Get_Save_Loc(self, game):
        '''Returns the save location of the entered game from the SQLite Database.

        Arguments:

        game -- game that will have the save location returned for
        '''
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game})
        return self.cursor.fetchone()[0]


    def Game_list_Sorted(self):
        '''Sorts the game list from the SQLite database based on the last backup and then returns a list.'''
        self.cursor.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in self.cursor.fetchall():
            ordered_games.append(game_name[0])
        self.database.commit()
        return ordered_games


    def Delete_Oldest(self, game):
        '''Deletes the oldest saves so only the newest specified amount is left.

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


    def Backup_Save(self):
        '''Backups up the game entered based on SQLite save location data to the specified backup folder.'''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M-%S")
        save_loc = self.Get_Save_Loc(self.selected_game)
        game = self.Sanitize_For_Filename(self.selected_game)
        total_size = self.Convert_Size(os.path.join(self.backup_dest, self.selected_game))
        base_backup_folder = os.path.join(self.backup_dest, game)
        dest = os.path.join(base_backup_folder, current_time)
        try:
            def backup():
                shutil.copytree(save_loc, dest)
                self.Delete_Oldest(game)
            BackupThread = Thread(target=backup)
            BackupThread.start()
            info1 = f'{game} backed up to set backup destination.\n'
            info2 = f'Total Backup Space: {total_size} from {len(os.listdir(base_backup_folder))} backups'
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


    def Restore_Save(self):
        '''Opens an interface for picking the dated backup of the selected game to restore.'''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        backup_path = os.path.join(self.backup_dest, self.selected_game)
        save_location = self.Get_Save_Loc(self.selected_game)
        self.save_dic = {}
        if os.path.exists(backup_path):
            for file in os.scandir(backup_path):
                updated_name = dt.datetime.strptime(file.name, '%d-%m-%y %H-%M-%S').strftime('%b %d, %Y %I:%M %p')
                self.save_dic[updated_name] = file
        else:
            messagebox.showwarning(title='Game Save Manager', message='No saves exist for this game.')


        def Restore_Game_Pressed():
            '''Restores selected game save based on save clicked.
            Restores by renaming current save folder to "save.old" and then copying the backup to replace it.'''
            save_name = self.save_dic[save_listbox.get(save_listbox.curselection())]
            save_path = os.path.join(self.backup_dest, self.selected_game, save_name.name)
            if os.path.exists(f'{save_location}.old'):
                msg = '''Backup of current save before last restore already exists.
                    \nDo you want to delete it? This will cancel the restore if you do not delete it.'''
                response = messagebox.askyesno(title='Game Save Manager', message=msg)
                if response:
                    shutil.rmtree(f'{save_location}.old')
                else:
                    print('Canceling Restore.')
                    return
            os.rename(save_location, f'{save_location}.old')
            shutil.copytree(save_path, save_location)
            self.logger.info(f'Restored Save for {self.selected_game}.')
            Restore_Game_Window.destroy()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        Restore_Game_Window.title('Game Save Manager - Restore Game')
        Restore_Game_Window.iconbitmap('Save_Icon.ico')
        Restore_Game_Window.resizable(width=False, height=False)
        Restore_Game_Window.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
        Restore_Game_Window.unbind_class("Button", "<Key-space>")

        RestoreInfo = ttk.Label(Restore_Game_Window,
            text=f'Select Save for {self.selected_game}', font=("Arial Bold", 10))
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=10, padx=10)

        save_listbox = Tk.Listbox(Restore_Game_Window, exportselection=False, font=("Arial Bold", 12), height=5, width=30)
        save_listbox.grid(columnspan=2, row=1, column=0, pady=5, padx=10)

        for item in self.save_dic:
            save_listbox.insert(Tk.END, item)

        confirm_button = ttk.Button(Restore_Game_Window, text='Confirm', command=Restore_Game_Pressed, width=20)
        confirm_button.grid(row=2, column=0, padx=10, pady=10)

        CancelButton = ttk.Button(Restore_Game_Window, text='Cancel', command=Restore_Game_Window.destroy, width=20)
        CancelButton.grid(row=2, column=1, padx=10, pady=10)

        Restore_Game_Window.mainloop()


    def Explore_Folder(self, folder):
        '''Opens the selected games save location in explorer or backup folder.

        Arguments:

        folder -- Set to "Game Save" or "Backup" to determine folder that is opened in explorer
        '''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        save_location = self.Get_Save_Loc(self.selected_game)
        if folder == 'Game Save':
            subprocess.Popen(f'explorer "{save_location}"')
        elif folder == 'Backup':
            game = self.Sanitize_For_Filename(self.selected_game)
            subprocess.Popen(f'explorer "{os.path.join(self.backup_dest, game)}"')


    @staticmethod
    def Convert_Size(dir):
        '''Converts size of directory to best fitting unit of measure.

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


    def Add_Game_to_Database(self):
        '''Adds game to database using entry inputs.'''
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get()
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


    def Browse_For_Save(self):
        '''Opens a file dialog so a save directory can be chosen.'''
        save_dir = filedialog.askdirectory(initialdir="C:/", title="Select Save Directory")
        self.GameSaveEntry.delete(0, Tk.END)
        self.GameSaveEntry.insert(0, save_dir)


    def Delete_Game_from_DB(self):
        '''Deletes selected game from SQLite Database.'''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        msg = 'Are you sure that you want to delete the game?'
        Delete_Check = messagebox.askyesno(title='Game Save Manager', message=msg)
        if Delete_Check:
            self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.selected_game})
            self.database.commit()
            self.game_listbox.delete(self.game_listbox.curselection()[0])
            self.Delete_Update_Entry()
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


    def Update_Game(self):
        '''Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.'''
        if self.selected_game == None:
            messagebox.showwarning(title='Game Save Manager', message='No game is selected yet.')
            return
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get()
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
    def Readable_Time_Since(datetime_obj):
        '''Gives time since for a datetime object in the unit of time that makes the most sense
        rounded to 1 decimal place.

        Arguments:

        datetime_obj -- datetime object that will have the current date subtracted from it
        '''
        seconds = (dt.datetime.now() - datetime_obj).total_seconds()
        if seconds < (60 * 60):  # seconds in minute * minutes in hour
            minutes = round(seconds / 60, 1)  # seconds in a minute
            time_since = f' {minutes} minutes ago'
        elif seconds < (60 * 60 * 24):  # seconds in minute * minutes in hour * hours in a day
            hours = round(seconds / (60 * 60), 1)  # seconds in minute * minutes in hour
            time_since = f' {hours} hours ago'
        else:
            days = round(seconds / 86400, 1)  # seconds in minute * minutes in hour * hours in a day
            time_since = f' {days} days ago'
        return time_since


    def On_Entry_Trace(self, *args):
        new_state = "disabled" if self.description.get() == "" else "normal"
        self.co_button.configure(state=new_state)


    def Delete_Update_Entry(self, Update = 0):
        '''Updates Game Data into Name and Save Entry for viewing.
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
            self.GameSaveEntry.insert(0, self.Get_Save_Loc(self.selected_game))
            # enables all buttons to be pressed once a selection is made
            for button in [
                self.BackupButton,
                self.RestoreButton,
                self.ExploreBackupButton,
                self.ExploreSaveButton
                ]:
                button.config(state='normal')
            base_backup_folder = os.path.join(self.backup_dest, self.selected_game)
            total_size = self.Convert_Size(base_backup_folder)
            self.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name",
                {'game_name': self.selected_game})
            last_backup = self.cursor.fetchone()[0]
            if last_backup != 'Never':
                time_since = self.Readable_Time_Since(dt.datetime.strptime(last_backup, '%Y/%m/%d %H:%M:%S'))
                info1 = f'{self.selected_game} was last backed up {time_since}\n'
                info2 = f'Total Backup Space: {total_size} from {len(os.listdir(base_backup_folder))} backups'
                info = info1 + info2
            else:
                info = f'{self.selected_game} has not been backed up\n'
            self.ActionInfo.config(text=info)
            self.BackupButton.focus_set()


    def Run_GUI(self):
        # Defaults
        BoldBaseFont = "Arial Bold"

        self.main_gui = Tk.Tk()
        self.main_gui.title('Game Save Manager')
        self.main_gui.iconbitmap('Save_Icon.ico')
        if self.disable_resize:  # sets window to not resize if disable_resize is set to 1
            self.main_gui.resizable(width=False, height=False)
        # window_width = 670
        # window_height = 550
        # width = int((self.main_gui.winfo_screenwidth()-window_width)/2)
        # height = int((self.main_gui.winfo_screenheight()-window_height)/2)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # TODO Binds do not work.
        self.main_gui.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
        self.main_gui.unbind_class("Button", "<Key-space>")

        # Main Row 0
        Backup_Frame = Tk.Frame(self.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        info_text = f'Total Games in Database: {len(self.Game_list_Sorted())}\nSize of Backups: {self.Convert_Size(self.backup_dest)}'
        Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
        Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        self.BackupButton = ttk.Button(Backup_Frame, text='Backup Save', state='disabled',
            command=self.Backup_Save, width=button_width)
        self.BackupButton.grid(row=3, column=1, padx=5, pady=5)

        self.RestoreButton = ttk.Button(Backup_Frame, text='Restore Save', state='disabled',
            command=self.Restore_Save, width=button_width)
        self.RestoreButton.grid(row=3, column=2, padx=5)

        self.ExploreSaveButton = ttk.Button(Backup_Frame, text='Explore Save Location', state='disabled',
            command=lambda: self.Explore_Folder('Game Save'), width=button_width)
        self.ExploreSaveButton.grid(row=4, column=1, padx=5)

        self.ExploreBackupButton = ttk.Button(Backup_Frame, text='Explore Backup Location', state='disabled',
            command=lambda: self.Explore_Folder('Backup'), width=button_width)
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
            self.Delete_Update_Entry(1))
        self.game_listbox.grid(columnspan=3, row=0, column=0)
        self.scrollbar.config(command=self.game_listbox.yview)

        sorted_list = self.Game_list_Sorted()
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

        # TODO set buttons to be disabled unless both entries are not empty
        # for entry in [self.GameSaveEntry, self.GameNameEntry]:
        #     entry.trace("w", self.On_Entry_Trace)
        #     entry.set("")  # initialize the state

        BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse',
            command=self.Browse_For_Save)
        BrowseButton.grid(row=1, column=4, padx=10)

        # Button Frame Row 2
        Button_Frame = Tk.Frame(Add_Game_Frame)
        Button_Frame.grid(columnspan=5, row=2, pady=(5, 5))

        button_padx = 4
        button_pady = 5
        ConfirmAddButton = Tk.ttk.Button(Button_Frame, text='Add Game',
            command=self.Add_Game_to_Database, width=20)
        ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

        UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Game',
            command=self.Update_Game, width=20)
        UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

        RemoveButton = ttk.Button(Button_Frame, text='Remove Game',
            command=self.Delete_Game_from_DB, width=20)
        RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
            command=self.Delete_Update_Entry, width=20)
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        self.Database_Check()

        self.main_gui.mainloop()

        self.database.close()

if __name__ == '__main__':
    App = Backup()
    App.Run_GUI()
