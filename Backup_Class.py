from tkinter import filedialog, messagebox
import tkinter as Tk
import datetime as dt
import logging as lg
import sqlite3
import shutil
import math
import os
import json


class Backup:
    def __init__(self, database, logger):
        with open('settings.json') as json_file:
            data = json.load(json_file)
        self.backup_dest = data['settings']['backup_dest']
        redundancy = data['settings']['backup_redundancy']
        if redundancy > 4:
            self.backup_redundancy = 4
        else:
            self.backup_redundancy = redundancy
        self.database = database
        self.logger = logger


    def Database_Check(self):
            '''Checks for missing save directories from database.'''
            c = self.database.cursor()
            c.execute("SELECT save_location FROM games")
            missing_save_loc = []
            for save_location in c.fetchall():
                if os.path.isdir(save_location[0]):
                    pass
                else:
                    missing_save_loc.append(save_location[0])
            missing_saves = len(missing_save_loc)
            continue_var = 0
            if missing_saves > 0 and missing_saves < 6:
                msg = f'Save Locations for the following do not exist.\n{missing_save_loc}'
                continue_var = Tk.messagebox.showwarning(title='Game Save Manager', message=msg)
            elif len(missing_save_loc) > 5:
                msg = 'More than 5 save locations do not exist.'
                continue_var = Tk.messagebox.showwarning(title='Game Save Manager', message=msg)


    def Sanitize_For_Filename(self, string):
        '''Removes illegal characters from string so it can become a valid filename.'''
        for char in ('<', '>', ':', '/', '\\', '|', '?', '*'):
            string = string.replace(char,'')
        return string


    def Get_Save_Loc(self, game):
        '''Returns the save location of the entered game from the SQLite Database.'''
        print(f'Getting Save location for {game}.')
        self.database = sqlite3.connect('game_list.db')
        c = self.database.cursor()
        c.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game})
        save_location = c.fetchone()[0]
        return save_location


    def Game_list_Sorted(self):
        '''Sorts the game list from the SQLite database based on the last backup and then returns a list.'''
        c = self.database.cursor()
        c.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in c.fetchall():
            ordered_games.append(game_name[0])
        self.database.commit()
        return ordered_games


    def Delete_Oldest(self, game):
        '''Deletest the oldest saves so only the the newest specified ammount is left.'''
        saves_list = []
        dir = os.path.join(self.backup_dest, game)
        print(dir)
        for file in os.listdir(dir):
            file = os.path.join(dir, file)
            saves_list.append(file)
        if len(saves_list) < 4:
            print(f'{self.backup_redundancy} or Less Saves.')
            return
        else:
            print(f'More than {self.backup_redundancy} Saves.')
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(self.backup_redundancy, len(saves_list)):
                shutil.rmtree(sorted_list[i])

    def Save_Backup(self, game, info_label):
        '''Backups up the game entered based on SQLite save location data to the specified backup folder.'''
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M")
        save_loc = self.Get_Save_Loc(game)
        game = self.Sanitize_For_Filename(game)
        dest = os.path.join(self.backup_dest, game, current_time)
        try:
            shutil.copytree(save_loc, dest)
            self.Delete_Oldest(game)
            info_label.config(text=f'Backed up {game} to set backup destination.')
        except FileNotFoundError:
            print('No Action Completed - File location does not exist.')
        except FileExistsError:
            print('No Action Completed - Save Already Backed up.')
        c = self.database.cursor()
        c.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
        {'game_name': game, 'last_backup': dt.datetime.now()})
        self.database.commit()
        self.logger.debug(f'Backed-up Save for {game}.')


    def Restore_Backup(self, game):
        '''Restores game save after moving current save to special backup folder.'''
        dest = os.path.join(self.backup_dest, game, 'Pre-Restore Backup')
        save_loc = self.Get_Save_Loc(game)
        # try:
        #     shutil.move(save_loc, dest)
        # except FileNotFoundError:
        #     messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')
        #     return
        self.Create_Restore_Game_Window(game, save_loc)


    def Clicked_Delete(self, Listbox):
        msg = 'Are you sure that you want to delete the game?'
        Delete_Check = Tk.messagebox.askyesno(title='Game Save Manager', message=msg)
        if Delete_Check:
            self.Delete_Game_from_DB(Listbox.get(Tk.ACTIVE), Listbox)


    def Convert_Size(self):
        '''Converts size of directory best fitting '''
        size_bytes = os.path.getsize(self.backup_dest)
        if size_bytes == 0: return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f'{s} {size_name[i]}'


    def Add_Game_Pressed(self, GameNameEntry, GameSaveEntry, Listbox):
        game_name = GameNameEntry.get()
        save_location = GameSaveEntry.get()
        if os.path.isdir(save_location):
            GameSaveEntry.delete(0, Tk.END)
            GameNameEntry.delete(0, Tk.END)
            self.Add_Game_to_DB(game_name, save_location)
            Listbox.insert(Tk.ACTIVE, game_name)
        else:
            Tk.messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')


    def Browse_Click(self, GameNameEntry, GameSaveEntry):
        save_dir = filedialog.askdirectory(initialdir="C:/", title="Select Save Directory")
        GameSaveEntry.delete(0, Tk.END)
        GameSaveEntry.insert(0, save_dir)


    def Add_Game_to_DB(self, game, save_location):
        '''Adds game to SQLite Database using entry box data.'''
        c = self.database.cursor()
        c.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
        {'game_name': game, 'save_location': save_location, 'last_backup': dt.datetime.now()})
        self.database.commit()
        self.logger.debug(f'Added {game} to database.')


    def Delete_Game_from_DB(self, game, Listbox):
        '''Deletes selected game from SQLite Database.'''
        c = self.database.cursor()
        c.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': game})
        self.database.commit()
        selected_game = Listbox.curselection()
        Listbox.delete(selected_game[0])
        self.logger.debug(f'Deleted {game} from database.')


    def Update_Game(self, GameNameEntry, GameSaveEntry, Listbox):
        '''Allows updating data for games in database.'''
        # TODO Add button to update game info.
        selected_game = Listbox.get(Tk.ACTIVE)


    def Cancel_Pressed(self, window):
        window.destroy()


    def Create_Restore_Game_Window(self, game, save_loc):
        backup_list =[]
        backup = os.path.join(self.backup_dest, game)
        for file in os.listdir(backup):
            backup_list.append(file)


        def Restore_Game_Pressed(self, save_to_restore):
            source = os.path.join(self.backup_dest, game, save_to_restore)
            # rename save game folder to ph.bachup
            shutil.copytree(source, save_loc)
            self.logger.debug(f'Restored Save for {game}.')
            Restore_Game_Window.destroy()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        Restore_Game_Window.title('Game Save Manager - Restore Game')
        Restore_Game_Window.iconbitmap('Save_Icon.ico')
        Restore_Game_Window.resizable(width=False, height=False)
        Restore_Game_Window.geometry("+600+600")
        Restore_Game_Window.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
        Restore_Game_Window.unbind_class("Button", "<Key-space>")

        save_to_restore = Tk.StringVar(Restore_Game_Window)

        RestoreInfo = Tk.ttk.Label(Restore_Game_Window, text=f'Select save to restore for {game}.')
        RestoreInfo.grid(columnspan=2, row=0, column=0)

        Listbox = Tk.Listbox(Restore_Game_Window, height=10, width=40)
        Listbox.grid(columnspan=2, row=1, column=0, pady=(0,5))

        sorted_list = self.Game_list_Sorted()
        for item in sorted_list:
            Listbox.insert(Tk.END, item)

        ConfirmButton = Tk.ttk.Button(Restore_Game_Window, text='Confirm', command=lambda: Restore_Game_Pressed(save_to_restore.get()), width=20)
        ConfirmButton.grid(row=2, column=0, padx=5, pady= 5)

        CancelButton = Tk.ttk.Button(Restore_Game_Window, text='Cancel', command=Cancel_Pressed, width=20)
        CancelButton.grid(row=2, column=1, padx=5, pady= 5)

        Restore_Game_Window.mainloop()