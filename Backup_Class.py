from tkinter import filedialog, messagebox
import tkinter as Tk
import datetime as dt
import logging as lg
import sqlite3
import shutil
import time
import math
import json
import os


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
        self.selected_game = None


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


    def Restore_Backup(self):
        '''Restores game save after moving current save to special backup folder.'''
        unfinished = Tk.messagebox.askyesno(title='Game Save Manager', message='Restore is unfinished.')
        print(self.selected_game)
        # save_loc = Get_Save_Loc(self, self.selected_game)
        # source = os.path.join(self.backup_dest, self.selected_game, save_to_restore)
        # # rename save game folder to ph.bachup
        # shutil.copytree(source, save_loc)
        # self.logger.debug(f'Restored Save for {self.selected_game}.')
        # dest = os.path.join(self.backup_dest, game, 'Pre-Restore Backup')
        # save_loc = self.Get_Save_Loc(self.selected_game)
        # radio_buttons = ['radio1', 'radio2', 'radio3', 'radio4']
        # try:
        #     shutil.move(save_loc, dest)
        # except FileNotFoundError:
        #     messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')
        #     return
        # backup_list =[]
        # backup = os.path.join(self.backup_dest, self.selected_game)
        # for file in os.listdir(backup):
        #     backup_list.append(file)


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


    def Delete_Game_from_DB(self, Listbox):
        '''Deletes selected game from SQLite Database.'''
        msg = 'Are you sure that you want to delete the game?'
        Delete_Check = Tk.messagebox.askyesno(title='Game Save Manager', message=msg)
        if Delete_Check:
            c = self.database.cursor()
            c.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.selected_game})
            self.database.commit()
            selected_game = Listbox.curselection()
            Listbox.delete(selected_game[0])
            self.logger.debug(f'Deleted {self.selected_game} from database.')


    def Update_Game(self, GameNameEntry, GameSaveEntry, Listbox):
        '''Allows updating data for games in database.'''
        # TODO Add button to update game info.
        game_name = GameNameEntry.get()
        save_location = GameSaveEntry.get()
        c = self.database.cursor()
        print(self.selected_game)
        sql_update_query  ='''UPDATE games
                SET game_name = ?, save_location = ?
                WHERE game_name = ?;'''
        data = (game_name, save_location, self.selected_game)
        c.execute(sql_update_query , data)
        self.database.commit()


    def Delete_Update_Entry(self, Listbox, GameSaveEntry, GameNameEntry, Update=0):
        '''Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.'''
        GameNameEntry.delete(0, Tk.END)
        GameSaveEntry.delete(0, Tk.END)
        if Update == 1:
            self.selected_game = Listbox.get(Listbox.curselection())
            GameNameEntry.insert(0, self.selected_game)
            GameSaveEntry.insert(0, self.Get_Save_Loc(self.selected_game))
            dir = os.path.join(self.backup_dest, self.selected_game)
            # if os.path.isdir(dir):
            #     radiolist =['radio1', 'radio2', 'radio3', 'radio4']
            #     for file in os.scandir(dir):
            #         for item in radiolist:
            #             item.config(text=file.name, value=file.path, state='normal')
            #             print(file.name)
